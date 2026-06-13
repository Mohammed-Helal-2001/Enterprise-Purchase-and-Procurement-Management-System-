"""
Purchasing App - Services
Core purchasing business services.
"""

from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


def send_rfq_to_suppliers(purchase_request):
    """
    Send RFQ to suppliers automatically
    """
    from suppliers.models import Supplier, SupplierMaterialPrice, Quotation
    
    # Get materials from the purchase request
    pr_materials = purchase_request.items.select_related('material').all()
    
    # Get suppliers who have these materials
    supplier_ids = set()
    material_supplier_map = {}
    
    for item in pr_materials:
        prices = SupplierMaterialPrice.objects.filter(
            material=item.material,
            is_available=True
        ).select_related('supplier')
        
        for price in prices:
            supplier_ids.add(price.supplier_id)
            if price.supplier_id not in material_supplier_map:
                material_supplier_map[price.supplier_id] = []
            material_supplier_map[price.supplier_id].append(item.material)
    
    # Send RFQ to each supplier
    sent_count = 0
    for supplier_id in supplier_ids:
        supplier = Supplier.objects.get(id=supplier_id)
        
        # Create RFQ log
        from purchasing.models import RFQLog
        rfq_log, created = RFQLog.objects.get_or_create(
            purchase_request=purchase_request,
            supplier=supplier,
            defaults={'email_sent': False}
        )
        
        # Send email
        try:
            send_rfq_email(purchase_request, supplier, pr_materials)
            rfq_log.email_sent = True
            rfq_log.save()
            sent_count += 1
        except Exception as e:
            rfq_log.email_error = str(e)
            rfq_log.save()
            logger.error(f'Error sending RFQ to {supplier.name}: {e}')
    
    # Update purchase request status
    if sent_count > 0:
        purchase_request.status = 'rfq_sent'
        purchase_request.save()
    
    return sent_count


def send_rfq_email(purchase_request, supplier, items):
    """Send RFQ email to supplier with proper error handling."""
    subject = f'RFQ Request - {purchase_request.pr_number}'

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en" dir="ltr">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; background: #f5f5f5; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; padding: 20px; border-radius: 6px; box-shadow: 0 0 12px rgba(0, 0, 0, 0.08); }}
            .header {{ border-bottom: 3px solid #1e40af; padding-bottom: 12px; margin-bottom: 20px; }}
            .header h2 {{ color: #1e40af; margin: 0; }}
            .info {{ margin-bottom: 12px; }}
            .label {{ font-weight: bold; color: #1f2937; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #e5e7eb; padding: 10px; text-align: left; }}
            th {{ background: #1e40af; color: white; }}
            tr:nth-child(even) {{ background: #f9fafb; }}
            .footer {{ margin-top: 24px; padding-top: 15px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 13px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Request for Quotation</h2>
            </div>
            <div class="info">
                <p>Dear {supplier.contact_person or supplier.name},</p>
            </div>
            <div class="info">
                <span class="label">Purchase Request:</span> {purchase_request.pr_number}
            </div>
            <div class="info">
                <span class="label">Title:</span> {purchase_request.title}
            </div>
            <div class="info">
                <span class="label">Date:</span> {purchase_request.created_at.strftime('%Y-%m-%d')}
            </div>

            <h3>Requested Materials</h3>
            <table>
                <thead>
                    <tr>
                        <th>Material</th>
                        <th>Quantity</th>
                        <th>Unit</th>
                    </tr>
                </thead>
                <tbody>
    """

    for item in items:
        html_content += f"""
                    <tr>
                        <td>{item.material.name}</td>
                        <td>{item.quantity}</td>
                        <td>{item.material.unit}</td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
            <div class="info">
                <p>Please submit your quotation through the purchase system at your earliest convenience.</p>
            </div>
            <div class="footer">
                <p>Best regards,</p>
                <p>{purchase_request.created_by.get_full_name()}</p>
                <p>Purchase Management System</p>
            </div>
        </div>
    </body>
    </html>
    """

    if not supplier.email:
        logger.warning(f'Supplier {supplier.name} has no email address')
        raise ValueError(f'Supplier {supplier.name} does not have an email address')

    try:
        send_mail(
            subject=subject,
            message=f'Request for quotation for purchase request {purchase_request.pr_number}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[supplier.email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f'Successfully sent RFQ email to {supplier.email} for PR {purchase_request.pr_number}')
        return True
    except Exception as e:
        logger.error(f'Error sending RFQ email to {supplier.email}: {e}')
        raise Exception(f'Failed to send RFQ email to {supplier.email}: {e}')


def get_best_supplier(purchase_request):
    """
    Core Algorithm: Get Best Supplier
    ==================================
    
    Score Calculation:
    - Price (50%): Lower is better
    - Delivery Days (30%): Lower is better
    - Supplier Rating (20%): Higher is better
    
    Formula:
    score = (price_normalized * 0.5) + (delivery_normalized * 0.3) - (rating_normalized * 0.2)
    
    Lower score = Better supplier
    """
    from suppliers.models import Quotation, QuotationItem
    
    # Get all quotations for this purchase request
    quotations = Quotation.objects.filter(
        purchase_request=purchase_request,
        status='pending'
    ).select_related('supplier').prefetch_related('items')
    
    if not quotations.exists():
        return {
            'success': False,
            'message': 'No quotations were found for this purchase request.'
        }
    
    # Get all prices and delivery days for normalization
    all_prices = [q.total_amount for q in quotations]
    all_delivery_days = [q.delivery_days for q in quotations]
    all_ratings = [q.supplier.rating for q in quotations]
    
    # Find min and max for normalization
    min_price = min(all_prices) if all_prices else 0
    max_price = max(all_prices) if all_prices else 0
    min_delivery = min(all_delivery_days) if all_delivery_days else 0
    max_delivery = max(all_delivery_days) if all_delivery_days else 0
    min_rating = min(all_ratings) if all_ratings else 0
    max_rating = max(all_ratings) if all_ratings else 0
    
    # Calculate score for each quotation
    analysis = []
    best_score = float('inf')
    best_supplier = None
    best_quotation = None
    
    for quotation in quotations:
        supplier = quotation.supplier
        
        # Normalize price (0-1, lower is better)
        if max_price > min_price:
            price_normalized = (quotation.total_amount - min_price) / (max_price - min_price)
        else:
            price_normalized = 0
        
        # Normalize delivery days (0-1, lower is better)
        if max_delivery > min_delivery:
            delivery_normalized = (quotation.delivery_days - min_delivery) / (max_delivery - min_delivery)
        else:
            delivery_normalized = 0
        
        # Normalize rating (0-1, higher is better)
        if max_rating > min_rating:
            rating_normalized = (supplier.rating - min_rating) / (max_rating - min_rating)
        else:
            rating_normalized = 0.5
        
                # Calculate final score
        # Lower is better
        price_normalized = float(price_normalized)
        delivery_normalized = float(delivery_normalized)
        rating_normalized = float(rating_normalized)
        score = (price_normalized * 0.5) + (delivery_normalized * 0.3) - (rating_normalized * 0.2)
        
        analysis.append({
            'quotation_id': quotation.id,
            'supplier_id': supplier.id,
            'supplier_name': supplier.name,
            'total_amount': float(quotation.total_amount),
            'delivery_days': quotation.delivery_days,
            'rating': float(supplier.rating),
            'price_normalized': round(price_normalized, 3),
            'delivery_normalized': round(delivery_normalized, 3),
            'rating_normalized': round(rating_normalized, 3),
            'score': round(score, 3),
            'is_best': False
        })
        
        if score < best_score:
            best_score = score
            best_supplier = supplier
            best_quotation = quotation
    
    # Mark best supplier
    for item in analysis:
        if item['supplier_id'] == best_supplier.id:
            item['is_best'] = True
    
    # Sort by score
    analysis.sort(key=lambda x: x['score'])
    
    # Generate explanation
    explanation = generate_explanation(best_supplier, best_quotation, analysis)
    
    return {
        'success': True,
        'best_supplier': {
            'id': best_supplier.id,
            'name': best_supplier.name,
            'rating': float(best_supplier.rating),
            'email': best_supplier.email
        },
        'best_score': round(best_score, 3),
        'best_quotation_id': best_quotation.id,
        'analysis': analysis,
        'explanation': explanation
    }


def generate_explanation(supplier, quotation, analysis):
    """
    Generate explanation for why this supplier was selected
    """
    # Find this supplier in analysis
    supplier_data = next((item for item in analysis if item['supplier_id'] == supplier.id), None)
    
    if not supplier_data:
        return ''
    
    explanation = f"""
    <div style="font-family: Arial, sans-serif; direction: ltr; text-align: left;">
        <h3 style="color: #1e40af;">Selected Supplier: {supplier.name}</h3>
        
        <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 10px 0;">
            <p><strong>Overall Score:</strong> {supplier_data['score']}</p>
        </div>
        
        <h4>Rating Breakdown:</h4>
        <ul>
            <li><strong>Price (50%):</strong> {supplier_data['total_amount']:.2f} - contribution: {supplier_data['price_normalized'] * 0.5:.3f}</li>
            <li><strong>Delivery (30%):</strong> {supplier_data['delivery_days']} days - contribution: {supplier_data['delivery_normalized'] * 0.3:.3f}</li>
            <li><strong>Supplier Rating (20%):</strong> {supplier_data['rating']:.2f} - contribution: -{supplier_data['rating_normalized'] * 0.2:.3f}</li>
        </ul>
        
        <h4>Comparison with other suppliers:</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #1e40af; color: white;">
                <th style="padding: 8px;">Supplier</th>
                <th style="padding: 8px;">Price</th>
                <th style="padding: 8px;">Delivery</th>
                <th style="padding: 8px;">Rating</th>
                <th style="padding: 8px;">Score</th>
            </tr>
    """
    
    for item in analysis[:5]:  # Show top 5
        marker = '✓' if item['is_best'] else ''
        style = 'background: #dcfce7;' if item['is_best'] else ''
        explanation += f"""
            <tr style="{style}">
                <td style="padding: 8px;">{item['supplier_name']} {marker}</td>
                <td style="padding: 8px;">{item['total_amount']:.2f}</td>
                <td style="padding: 8px;">{item['delivery_days']}</td>
                <td style="padding: 8px;">{item['rating']:.2f}</td>
                <td style="padding: 8px; font-weight: bold;">{item['score']:.3f}</td>
            </tr>
        """
    
    explanation += """
        </table>
    </div>
    """
    
    return explanation


def approve_request(purchase_request, user, reason=''):
    """
    Approve a purchase request
    """
    purchase_request.status = 'approved'
    purchase_request.approved_by = user
    purchase_request.approved_at = timezone.now()
    purchase_request.save()
    
    # Create approval history
    from purchasing.models import ApprovalHistory
    ApprovalHistory.objects.create(
        purchase_request=purchase_request,
        action_by=user,
        action='approve',
        reason=reason
    )
    
    return True


def reject_request(purchase_request, user, reason):
    """
    Reject a purchase request
    """
    if not reason:
        raise ValueError('Reason is required for rejection')
    
    purchase_request.status = 'rejected'
    purchase_request.rejected_by = user
    purchase_request.rejected_at = timezone.now()
    purchase_request.rejection_reason = reason
    purchase_request.save()
    
    # Create approval history
    from purchasing.models import ApprovalHistory
    ApprovalHistory.objects.create(
        purchase_request=purchase_request,
        action_by=user,
        action='reject',
        reason=reason
    )
    
    return True


def award_supplier(purchase_request, supplier):
    """
    Award purchase request to a supplier
    """
    purchase_request.status = 'awarded'
    purchase_request.awarded_supplier = supplier
    purchase_request.awarded_at = timezone.now()
    purchase_request.save()
    
    # Update supplier's total orders
    supplier.total_orders += 1
    supplier.save()
    
    return True


def generate_pr_pdf_bytes(purchase_request):
    """
    Generate a professional PDF for a purchase request.
    Designed to be used as an attachment sent to suppliers.
    Produces a clean, formal, and real-world purchase order document.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
        PageBreak, HRFlowable
    )
    from datetime import datetime
    from io import BytesIO
    
    # Get related data
    items = purchase_request.items.select_related('material').all()
    
    buffer = BytesIO()
    
    # Professional margins
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=1.8*cm, 
        leftMargin=1.8*cm, 
        topMargin=1.5*cm, 
        bottomMargin=1.5*cm
    )
    
    # ============================================================
    # STYLES - Professional and clean
    # ============================================================
    styles = getSampleStyleSheet()
    
    # Company header style
    company_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Heading1'],
        fontSize=22,
        leading=28,
        textColor=colors.HexColor('#1a237e'),  # Deep navy blue
        spaceAfter=2,
        alignment=0,
        fontName='Helvetica-Bold',
    )
    
    # Document type style
    doc_type_style = ParagraphStyle(
        'DocType',
        parent=styles['Heading2'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=4,
        alignment=0,
        fontName='Helvetica-Bold',
    )
    
    # Status badge style
    status_style = ParagraphStyle(
        'StatusBadge',
        fontSize=10,
        leading=14,
        textColor=colors.white,
        backColor=colors.HexColor('#2563eb'),
        alignment=1,
        fontName='Helvetica-Bold',
    )
    
    # Label style (for field names)
    label_style = ParagraphStyle(
        'FieldLabel',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#64748b'),  # Slate gray
        fontName='Helvetica',
    )
    
    # Value style (for field values)
    value_style = ParagraphStyle(
        'FieldValue',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b'),  # Dark slate
        fontName='Helvetica',
    )
    
    # Section title style
    section_title_style = ParagraphStyle(
        'SectionTitle',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1a237e'),
        spaceBefore=12,
        spaceAfter=8,
        fontName='Helvetica-Bold',
    )
    
    # Table header style
    table_header_style = ParagraphStyle(
        'TableHeader',
        fontSize=9,
        leading=12,
        textColor=colors.white,
        alignment=1,
        fontName='Helvetica-Bold',
    )
    
    # Table cell style
    table_cell_style = ParagraphStyle(
        'TableCell',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1e293b'),
        alignment=1,
        fontName='Helvetica',
    )
    
    # Table cell left aligned
    table_cell_left_style = ParagraphStyle(
        'TableCellLeft',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1e293b'),
        alignment=0,
        fontName='Helvetica',
    )
    
    # Footer style
    footer_style = ParagraphStyle(
        'Footer',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#94a3b8'),
        alignment=1,
        fontName='Helvetica',
    )
    
    # Signature style
    signature_style = ParagraphStyle(
        'Signature',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=4,
        fontName='Helvetica',
    )
    
    # ============================================================
    # BUILD DOCUMENT CONTENT
    # ============================================================
    elements = []
    
    # ----- TOP HEADER SECTION -----
    # Company / Document header
    header_data = [
        [Paragraph('PURCHASE SYSTEM', company_style), 
         Paragraph(f'<b>PR No:</b> {purchase_request.pr_number}', value_style)],
        [Paragraph('PURCHASE REQUEST', doc_type_style),
         Paragraph(f'<b>Date:</b> {purchase_request.created_at.strftime("%Y-%m-%d")}', value_style)],
    ]
    
    header_table = Table(header_data, colWidths=[10*cm, 8*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(header_table)
    
    # Horizontal line after header
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1a237e'), spaceBefore=4, spaceAfter=12))
    
    # ----- REQUEST INFORMATION -----
    elements.append(Paragraph('REQUEST INFORMATION', section_title_style))
    
    # Create info table
    info_data = []
    info_data.append([
        Paragraph('<b>Request Title:</b>', label_style),
        Paragraph(purchase_request.title, value_style),
        Paragraph('<b>Status:</b>', label_style),
        Paragraph(f'<font color="#2563eb"><b>{purchase_request.get_status_display()}</b></font>', value_style),
    ])
    info_data.append([
        Paragraph('<b>Created By:</b>', label_style),
        Paragraph(purchase_request.created_by.get_full_name() or purchase_request.created_by.email, value_style),
        Paragraph('<b>Department:</b>', label_style),
        Paragraph(purchase_request.department or '-', value_style),
    ])
    info_data.append([
        Paragraph('<b>Priority:</b>', label_style),
        Paragraph(purchase_request.get_priority_display() if hasattr(purchase_request, 'get_priority_display') else 'Normal', value_style),
        Paragraph('<b>Date Created:</b>', label_style),
        Paragraph(purchase_request.created_at.strftime('%Y-%m-%d %H:%M'), value_style),
    ])
    
    if purchase_request.description:
        info_data.append([
            Paragraph('<b>Description:</b>', label_style),
            Paragraph(purchase_request.description, value_style),
            Paragraph('', label_style),
            Paragraph('', value_style),
        ])
    
    info_table = Table(info_data, colWidths=[3*cm, 5.5*cm, 3*cm, 5.5*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6))
    
    # Light border around info
    info_box_data = [['']]
    info_box = Table(info_box_data, colWidths=[16.4*cm])
    info_box.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    # Actually let's not use a box, the row backgrounds are cleaner
    
    # ----- REQUESTED ITEMS TABLE -----
    elements.append(Paragraph('REQUESTED MATERIALS', section_title_style))
    
    if items:
        items_header = [
            Paragraph('<b>#</b>', table_header_style),
            Paragraph('<b>Material</b>', table_header_style),
            Paragraph('<b>Description</b>', table_header_style),
            Paragraph('<b>Quantity</b>', table_header_style),
            Paragraph('<b>Unit</b>', table_header_style),
        ]
        
        items_body = [items_header]
        for i, item in enumerate(items, 1):
            items_body.append([
                Paragraph(str(i), table_cell_style),
                Paragraph(item.material.name, table_cell_left_style),
                Paragraph(item.description or '-', table_cell_left_style),
                Paragraph(str(item.quantity), table_cell_style),
                Paragraph(item.material.unit, table_cell_style),
            ])
        
        items_table = Table(items_body, colWidths=[1*cm, 4*cm, 5.4*cm, 3*cm, 3*cm])
        items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (2, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(items_table)
    else:
        elements.append(Paragraph('<i>No materials listed in this request.</i>', table_cell_style))
    
    elements.append(Spacer(1, 10))
    
    # ----- APPROVAL STATUS SECTION -----
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=6, spaceAfter=10))
    elements.append(Paragraph('APPROVAL STATUS', section_title_style))
    
    approval_data = []
    
    if purchase_request.approved_by:
        approval_data.append([
            Paragraph('<b>Approved By:</b>', label_style),
            Paragraph(purchase_request.approved_by.get_full_name() or str(purchase_request.approved_by), value_style),
            Paragraph('<b>Date:</b>', label_style),
            Paragraph(purchase_request.approved_at.strftime('%Y-%m-%d %H:%M') if purchase_request.approved_at else '-', value_style),
        ])
    
    if purchase_request.rejected_by:
        approval_data.append([
            Paragraph('<b>Rejected By:</b>', label_style),
            Paragraph(purchase_request.rejected_by.get_full_name() or str(purchase_request.rejected_by), value_style),
            Paragraph('<b>Date:</b>', label_style),
            Paragraph(purchase_request.rejected_at.strftime('%Y-%m-%d %H:%M') if purchase_request.rejected_at else '-', value_style),
        ])
        if purchase_request.rejection_reason:
            approval_data.append([
                Paragraph('<b>Reason:</b>', label_style),
                Paragraph(purchase_request.rejection_reason, value_style),
                Paragraph('', label_style),
                Paragraph('', value_style),
            ])
    
    if purchase_request.awarded_supplier:
        approval_data.append([
            Paragraph('<b>Awarded To:</b>', label_style),
            Paragraph(purchase_request.awarded_supplier.name, value_style),
            Paragraph('<b>Date:</b>', label_style),
            Paragraph(purchase_request.awarded_at.strftime('%Y-%m-%d %H:%M') if purchase_request.awarded_at else '-', value_style),
        ])
    
    if approval_data:
        appr_table = Table(approval_data, colWidths=[3*cm, 5.5*cm, 3*cm, 5.5*cm])
        appr_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(appr_table)
    else:
        elements.append(Paragraph('<i>No approval actions recorded yet.</i>', ParagraphStyle('Italic', parent=table_cell_style, textColor=colors.HexColor('#94a3b8'))))
    
    # ----- NOTES SECTION -----
    if purchase_request.notes:
        elements.append(Spacer(1, 6))
        elements.append(Paragraph('NOTES', section_title_style))
        notes_data = [[
            Paragraph(purchase_request.notes, ParagraphStyle('NotesText', fontSize=9, leading=13, textColor=colors.HexColor('#475569'), fontName='Helvetica'))
        ]]
        notes_table = Table(notes_data, colWidths=[16.4*cm])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fffbeb')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#fde68a')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(notes_table)
    
    # ----- SIGNATURE & FOOTER -----
    elements.append(Spacer(1, 25))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=6, spaceAfter=10))
    
    # Signature area
    created_by_name = purchase_request.created_by.get_full_name() or purchase_request.created_by.email
    signature_data = [
        [Paragraph(f'<b>Prepared By:</b>', signature_style),
         Paragraph(f'<b>Authorized Signature:</b>', signature_style)],
        [Paragraph(created_by_name, signature_style),
         Paragraph('_________________________', signature_style)],
        [Paragraph(f'Date: {purchase_request.created_at.strftime("%Y-%m-%d")}', ParagraphStyle('SigDate', parent=signature_style, textColor=colors.HexColor('#64748b'), fontSize=8)),
         Paragraph('Date: _______________', ParagraphStyle('SigDate2', parent=signature_style, textColor=colors.HexColor('#64748b'), fontSize=8))],
    ]
    
    sig_table = Table(signature_data, colWidths=[8.2*cm, 8.2*cm])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(sig_table)
    
    # Footer
    elements.append(Spacer(1, 12))
    today_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    elements.append(Paragraph(
        f'This document was generated by the Purchase Management System on {today_str} | Page 1 of 1',
        footer_style
    ))
    elements.append(Paragraph(
        'This is a computer-generated document and does not require a physical signature.',
        ParagraphStyle('Disclaimer', parent=footer_style, fontSize=7, textColor=colors.HexColor('#94a3b8'))
    ))
    
    # ============================================================
    # BUILD THE PDF
    # ============================================================
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def send_pr_pdf_to_email(purchase_request, recipient_email, sender_user, custom_message=''):
    """
    Send purchase request as PDF attachment via email.
    Only admins and purchasing officers can use this.
    """
    # Generate PDF
    pdf_bytes = generate_pr_pdf_bytes(purchase_request)
    
    # Build email content
    subject = f'Purchase Request - {purchase_request.pr_number}'
    
    message_body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; background: #f5f5f5; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; padding: 20px; border-radius: 6px; box-shadow: 0 0 12px rgba(0, 0, 0, 0.08); }}
            .header {{ border-bottom: 3px solid #1e40af; padding-bottom: 12px; margin-bottom: 20px; }}
            .header h2 {{ color: #1e40af; margin: 0; }}
            .info {{ margin-bottom: 12px; }}
            .label {{ font-weight: bold; color: #1f2937; }}
            table {{ width: 100%%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #e5e7eb; padding: 10px; text-align: left; }}
            th {{ background: #1e40af; color: white; }}
            tr:nth-child(even) {{ background: #f9fafb; }}
            .footer {{ margin-top: 24px; padding-top: 15px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 13px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Purchase Request - {purchase_request.pr_number}</h2>
            </div>
            <div class="info">
                <p>Dear Sir/Madam,</p>
            </div>
            <div class="info">
                <p>Please find attached the purchase request details for your reference.</p>
            </div>
            <div class="info">
                <span class="label">Request Number:</span> {purchase_request.pr_number}
            </div>
            <div class="info">
                <span class="label">Title:</span> {purchase_request.title}
            </div>
            <div class="info">
                <span class="label">Status:</span> {purchase_request.get_status_display()}
            </div>
            <div class="info">
                <span class="label">Date:</span> {purchase_request.created_at.strftime('%Y-%m-%d')}
            </div>
    """
    
    if custom_message:
        message_body += f"""
            <div class="info" style="background: #f0f9ff; padding: 15px; border-radius: 6px; margin: 15px 0;">
                <p><strong>Message:</strong></p>
                <p>{custom_message}</p>
            </div>
        """
    
    # Add items table
    items = purchase_request.items.select_related('material').all()
    if items:
        message_body += """
            <h3>Requested Items</h3>
            <table>
                <thead>
                    <tr>
                        <th>Material</th>
                        <th>Quantity</th>
                        <th>Unit</th>
                    </tr>
                </thead>
                <tbody>
        """
        for item in items:
            message_body += f"""
                    <tr>
                        <td>{item.material.name}</td>
                        <td>{item.quantity}</td>
                        <td>{item.material.unit}</td>
                    </tr>
            """
        message_body += """
                </tbody>
            </table>
        """
    
    sender_name = sender_user.get_full_name() or sender_user.email
    message_body += f"""
            <div class="footer">
                <p>Best regards,</p>
                <p>{sender_name}</p>
                <p>Purchase Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create email with PDF attachment
    email = EmailMessage(
        subject=subject,
        body=message_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.content_subtype = 'html'
    email.attach(f'PR_{purchase_request.pr_number}.pdf', pdf_bytes, 'application/pdf')
    
    try:
        email.send(fail_silently=False)
        logger.info(f'Successfully sent PR {purchase_request.pr_number} PDF to {recipient_email}')
        return True, 'Email sent successfully'
    except Exception as e:
        logger.error(f'Error sending PR PDF to {recipient_email}: {e}')
        raise Exception(f'Failed to send email: {str(e)}')