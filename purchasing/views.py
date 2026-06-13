"""
Purchasing App - Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from .models import PurchaseRequest, PurchaseItem, RFQLog, ApprovalHistory
from suppliers.models import Supplier, Material, Quotation, QuotationItem, SupplierMaterialPrice
from .services import (
    send_rfq_to_suppliers, 
    get_best_supplier, 
    approve_request, 
    reject_request,
    award_supplier,
    send_pr_pdf_to_email,
    generate_pr_pdf_bytes
)



@login_required
def purchase_request_list(request):
    """Purchase Request List View"""
    # Get filter parameters
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    # Base queryset
    queryset = PurchaseRequest.objects.select_related(
        'created_by', 
        'approved_by', 
        'rejected_by',
        'awarded_supplier'
    ).order_by('-created_at')
    
    # Apply filters
    if status:
        queryset = queryset.filter(status=status)
    
    if search:
        queryset = queryset.filter(
            Q(pr_number__icontains=search) |
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
                # Filter by user role
    if request.user.role == 'requester':
        # Requester sees only their own requests
        queryset = queryset.filter(created_by=request.user)
    elif request.user.role == 'approver':
        # Approver sees all requests but can approve pending ones
        pass
    elif request.user.role == 'purchasing_officer':
        # Purchasing officer sees all non-draft requests (can approve/reject at any stage)
        queryset = queryset.exclude(status='draft')
    # Admin sees all

    # Paginate
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'search': search,
        'status_choices': PurchaseRequest.STATUS_CHOICES,
    }
    
    return render(request, 'purchasing/request_list.html', context)


@login_required
def purchase_request_create(request):
    """Create Purchase Request View"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        submit_approval = 'submit_approval' in request.POST
        
        material_ids = request.POST.getlist('material[]')
        quantities = request.POST.getlist('quantity[]')
        descriptions = request.POST.getlist('item_description[]')
        
        # Check if at least one valid item has been provided when submitting for approval
        valid_items_exist = any(
            material_id and i < len(quantities) and quantities[i]
            for i, material_id in enumerate(material_ids)
        )
        
        if submit_approval and not valid_items_exist:
            messages.error(request, 'Please add at least one material before submitting the request for approval.')
            materials = Material.objects.filter(is_active=True).order_by('name')
            return render(request, 'purchasing/request_create.html', {
                'materials': materials,
            })
        
        status = 'pending_approval' if submit_approval else 'draft'
        
        # Create purchase request
        pr = PurchaseRequest.objects.create(
            title=title,
            description=description,
            created_by=request.user,
            status=status
        )
        
        for i, material_id in enumerate(material_ids):
            if material_id and i < len(quantities) and quantities[i]:
                try:
                    material = Material.objects.get(id=material_id)
                    PurchaseItem.objects.create(
                        purchase_request=pr,
                        material=material,
                        quantity=quantities[i],
                        description=descriptions[i] if i < len(descriptions) else ''
                    )
                except Material.DoesNotExist:
                    continue
        
        if submit_approval:
            ApprovalHistory.objects.create(
                purchase_request=pr,
                action_by=request.user,
                action='submit',
                reason='Request submitted for approval'
            )
            messages.success(request, f'Purchase request {pr.pr_number} has been created and submitted for approval successfully.')
        else:
            messages.success(request, f'Purchase request {pr.pr_number} has been saved as a draft successfully.')
        
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    # Get materials for the form
    materials = Material.objects.filter(is_active=True).order_by('name')
    
    context = {
        'materials': materials,
    }
    
    return render(request, 'purchasing/request_create.html', context)


@login_required
def purchase_request_detail(request, pr_id):
    """Purchase Request Detail View"""
    pr = get_object_or_404(
        PurchaseRequest.objects.select_related(
            'created_by', 
            'approved_by', 
            'rejected_by',
            'awarded_supplier'
        ),
        id=pr_id
    )
    
    # Get items
    items = pr.items.select_related('material').all()
    
    # Get quotations
    quotations = pr.quotations.select_related('supplier').prefetch_related('items__material')
    
    # Get RFQ logs
    rfq_logs = pr.rfq_logs.select_related('supplier').all()
    
    # Get approval history
    approval_history = pr.approval_history.select_related('action_by').all()
    
        # Get suppliers that match at least one material in the request
    material_ids = items.values_list('material_id', flat=True)
    if material_ids:
        # Find suppliers who have a link to ANY of the requested materials
        matching_supplier_ids = SupplierMaterialPrice.objects.filter(
            material_id__in=material_ids,
            is_available=True
        ).values_list('supplier_id', flat=True).distinct()
        
        all_suppliers = Supplier.objects.filter(
            id__in=matching_supplier_ids,
            is_active=True
        ).order_by('name')
    else:
        all_suppliers = Supplier.objects.none()
    
    context = {
        'pr': pr,
        'items': items,
        'quotations': quotations,
        'rfq_logs': rfq_logs,
        'has_rfq_logs': rfq_logs.exists(),
        'approval_history': approval_history,
        'all_suppliers': all_suppliers,
    }
    
    return render(request, 'purchasing/request_detail.html', context)


@login_required
def purchase_request_update(request, pr_id):
    """Update Purchase Request View"""
    pr = get_object_or_404(PurchaseRequest, id=pr_id)
    
    # Check if user can edit
    if pr.created_by != request.user and not request.user.is_admin:
        messages.error(request, 'You do not have permission to edit this request.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    # Only allow editing in draft status
    if pr.status != 'draft':
        messages.error(request, 'This request cannot be edited in its current status.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    if request.method == 'POST':
        pr.title = request.POST.get('title')
        pr.description = request.POST.get('description')
        pr.save()
        
        # Update items
        pr.items.all().delete()
        
        material_ids = request.POST.getlist('material[]')
        quantities = request.POST.getlist('quantity[]')
        descriptions = request.POST.getlist('item_description[]')
        
        for i, material_id in enumerate(material_ids):
            if material_id and i < len(quantities) and quantities[i]:
                try:
                    material = Material.objects.get(id=material_id)
                    PurchaseItem.objects.create(
                        purchase_request=pr,
                        material=material,
                        quantity=quantities[i],
                        description=descriptions[i] if i < len(descriptions) else ''
                    )
                except Material.DoesNotExist:
                    continue
        
        messages.success(request, 'Purchase request updated successfully.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    materials = Material.objects.filter(is_active=True).order_by('name')
    items = pr.items.select_related('material').all()
    
    context = {
        'pr': pr,
        'materials': materials,
        'items': items,
    }
    
    return render(request, 'purchasing/request_update.html', context)


@login_required
@require_http_methods(["POST"])
def send_rfq_view(request, pr_id):
    """Send RFQ to Suppliers View (Only PO and Admin can send)"""
    pr = get_object_or_404(PurchaseRequest, id=pr_id)
    
    # Only admin and purchasing_officer can send RFQ
    if request.user.role not in ['admin', 'purchasing_officer']:
        messages.error(request, 'You do not have permission to send RFQ. Only admins and purchasing officers can send RFQ.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
        # Only approved requests can be sent to suppliers
    if pr.status != 'approved':
        messages.error(request, 'Cannot send RFQ. Only approved requests can be sent to suppliers.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    try:
        count = send_rfq_to_suppliers(pr)
        if count:
            messages.success(request, f'RFQ emails sent to {count} suppliers.')
        else:
            messages.warning(request, 'No suppliers were found for this purchase request.')
    except Exception as e:
        messages.error(request, f'Error sending RFQ: {str(e)}')
    
    return redirect('purchasing:request_detail', pr_id=pr.id)


@login_required
@require_http_methods(["POST"])
def submit_for_approval_view(request, pr_id):
    """Submit Purchase Request for Approval"""
    pr = get_object_or_404(PurchaseRequest, id=pr_id)
    
    # Check if user is the creator OR admin OR purchasing_officer
    can_submit = (
        pr.created_by == request.user or 
        request.user.role == 'admin' or 
        request.user.role == 'purchasing_officer'
    )
    
    if not can_submit:
        messages.error(request, 'You do not have permission to submit this request.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    # Check if request is in draft status
    if pr.status != 'draft':
        messages.error(request, 'This request cannot be submitted in its current status.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    # Check if request has items
    if not pr.items.exists():
        messages.error(request, 'Please add items to the request before submission.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    # Submit for approval
    pr.status = 'pending_approval'
    pr.save()
    
    # Create approval history
    from .models import ApprovalHistory
    ApprovalHistory.objects.create(
        purchase_request=pr,
        action_by=request.user,
        action='submit',
        reason='Request submitted for approval'
    )
    
    messages.success(request, f'Purchase request {pr.pr_number} was submitted for approval successfully.')
    return redirect('purchasing:request_detail', pr_id=pr.id)


@login_required
def suggest_supplier_view(request, pr_id):
    """Suggest Best Supplier View"""
    pr = get_object_or_404(PurchaseRequest, id=pr_id)
    
    result = get_best_supplier(pr)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(result)
    
    if result['success']:
        messages.success(request, f'Best supplier: {result["best_supplier"]["name"]}')
    else:
        messages.error(request, result.get('message', 'An error occurred'))
    
    return redirect('purchasing:request_detail', pr_id=pr.id)


@login_required
@require_http_methods(["POST"])
def approve_request_view(request, pr_id):
    """Approve Purchase Request View"""
    pr = get_object_or_404(PurchaseRequest, id=pr_id)
    
    # Approver can approve pending_approval requests
    # Purchasing Officer and Admin can approve approved requests (second approval) or pending_approval
    if request.user.role == 'approver':
        if pr.status != 'pending_approval':
            messages.error(request, 'This request cannot be approved in its current status.')
            return redirect('purchasing:request_detail', pr_id=pr.id)
    elif request.user.role in ['admin', 'purchasing_officer']:
        if pr.status not in ['pending_approval', 'approved']:
            messages.error(request, 'This request cannot be approved in its current status.')
            return redirect('purchasing:request_detail', pr_id=pr.id)
    else:
        messages.error(request, 'You do not have permission to approve this request.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    try:
        approve_request(pr, request.user)
        messages.success(request, 'Purchase request approved successfully.')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('purchasing:request_detail', pr_id=pr.id)


@login_required
@require_http_methods(["POST"])
def reject_request_view(request, pr_id):
    """Reject Purchase Request View"""
    pr = get_object_or_404(PurchaseRequest, id=pr_id)
    
    # Approver can reject pending_approval requests
    # Purchasing Officer and Admin can reject approved or pending_approval
    if request.user.role == 'approver':
        if pr.status != 'pending_approval':
            messages.error(request, 'This request cannot be rejected in its current status.')
            return redirect('purchasing:request_detail', pr_id=pr.id)
    elif request.user.role in ['admin', 'purchasing_officer']:
        if pr.status not in ['pending_approval', 'approved']:
            messages.error(request, 'This request cannot be rejected in its current status.')
            return redirect('purchasing:request_detail', pr_id=pr.id)
    else:
        messages.error(request, 'You do not have permission to reject this request.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    reason = request.POST.get('reason', '').strip()
    
    if not reason:
        messages.error(request, 'Please enter a reason for rejection.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    try:
        reject_request(pr, request.user, reason)
        messages.success(request, 'Purchase request rejected successfully.')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('purchasing:request_detail', pr_id=pr.id)


@login_required
@require_http_methods(["POST"])
def award_supplier_view(request, pr_id):
    """Award Supplier View"""
    pr = get_object_or_404(PurchaseRequest, id=pr_id)
    supplier_id = request.POST.get('supplier_id')
    
    if not request.user.is_approver and not request.user.is_admin:
        messages.error(request, 'You do not have permission to award this supplier.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    if pr.status != 'approved':
        messages.error(request, 'A supplier cannot be awarded in the current request status.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    try:
        supplier = Supplier.objects.get(id=supplier_id)
        award_supplier(pr, supplier)
        messages.success(request, f'Purchase request awarded to supplier {supplier.name}.')
    except Supplier.DoesNotExist:
        messages.error(request, 'Supplier not found.')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('purchasing:request_detail', pr_id=pr.id)


@login_required
def quotation_comparison(request, pr_id):
    """Quotation Comparison View"""
    pr = get_object_or_404(PurchaseRequest, id=pr_id)
    
    # Get best supplier suggestion
    best_supplier_result = get_best_supplier(pr)
    
    quotations = pr.quotations.select_related('supplier').prefetch_related('items__material')
    items = pr.items.select_related('material').all()
    
    context = {
        'pr': pr,
        'quotations': quotations,
        'items': items,
        'best_supplier': best_supplier_result.get('best_supplier') if best_supplier_result.get('success') else None,
        'best_score': best_supplier_result.get('best_score') if best_supplier_result.get('success') else None,
        'analysis': best_supplier_result.get('analysis') if best_supplier_result.get('success') else [],
    }
    
    return render(request, 'purchasing/quotation_comparison.html', context)


@login_required
def quotation_requests_list(request):
    """List only requests that have been sent to suppliers (rfq_sent)"""
    # Only admin and purchasing_officer can access
    if request.user.role not in ['admin', 'purchasing_officer']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:dashboard')
    
    # Get requests that have been sent to suppliers (have RFQ logs)
    from django.db.models import Exists, OuterRef
    
    rfq_subquery = RFQLog.objects.filter(purchase_request=OuterRef('pk'))
    
    requests_list = PurchaseRequest.objects.filter(
        Exists(rfq_subquery)
    ).filter(
        status__in=['approved', 'rfq_sent']
    ).select_related(
        'created_by', 'awarded_supplier'
    ).prefetch_related(
        'quotations', 'rfq_logs__supplier'
    ).order_by('-created_at')
    
    from django.core.paginator import Paginator
    paginator = Paginator(requests_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'purchasing/quotation_requests_list.html', context)


@login_required
def quotation_create(request, pr_id):
    """Create Quotation View (Only Admin and Purchasing Officer)"""
    # Permission check: only admin or purchasing_officer can add quotations
    if request.user.role not in ['admin', 'purchasing_officer']:
        messages.error(request, 'You do not have permission to add quotations. Only admins and purchasing officers can add quotations.')
        return redirect('purchasing:request_detail', pr_id=pr_id)
    
    pr = get_object_or_404(PurchaseRequest, id=pr_id)
    
    # Check if RFQ has been sent to at least one supplier
    if pr.status not in ['rfq_sent', 'approved']:
        messages.error(request, 'This purchase request has not been sent to any supplier yet. Please send the RFQ to suppliers first before adding a quotation.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id')
        delivery_days = request.POST.get('delivery_days')
        
        try:
            supplier = Supplier.objects.get(id=supplier_id)
            
            # Create quotation
            quotation = Quotation.objects.create(
                purchase_request=pr,
                supplier=supplier,
                delivery_days=delivery_days or 0
            )
            
            # Add items
            material_ids = request.POST.getlist('material[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            
            for i, material_id in enumerate(material_ids):
                if material_id and i < len(unit_prices) and unit_prices[i]:
                    try:
                        material = Material.objects.get(id=material_id)
                        QuotationItem.objects.create(
                            quotation=quotation,
                            material=material,
                            quantity=quantities[i] if i < len(quantities) else 1,
                            unit_price=unit_prices[i]
                        )
                    except Material.DoesNotExist:
                        continue
            
            # Calculate total
            quotation.calculate_total()
            
            messages.success(request, 'Quotation submitted successfully.')
            return redirect('purchasing:request_detail', pr_id=pr.id)
            
        except Supplier.DoesNotExist:
            messages.error(request, 'Supplier not found.')
    
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    items = pr.items.select_related('material').all()
    
    context = {
        'pr': pr,
        'suppliers': suppliers,
        'items': items,
    }
    
    return render(request, 'purchasing/quotation_create.html', context)




@login_required
def dashboard_stats(request):
    """Dashboard Statistics API - Accurate stats with monthly data"""
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    import calendar
    
    # Get accurate status counts
    all_requests = PurchaseRequest.objects.all()
    
    stats = {
        'draft': all_requests.filter(status='draft').count(),
        'pending': all_requests.filter(status='pending_approval').count(),
        'approved': all_requests.filter(status='approved').count(),
        'rejected': all_requests.filter(status='rejected').count(),
        'rfq_sent': all_requests.filter(status='rfq_sent').count(),
        'awarded': all_requests.filter(status='awarded').count(),
        'total': all_requests.count(),
    }
    
    # Monthly statistics for the last 12 months
    current_date = timezone.now()
    monthly_stats = {}
    
    for i in range(11, -1, -1):
        month_date = current_date - timedelta(days=30*i)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if month_date.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        
        month_count = all_requests.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        month_name = calendar.month_name[month_date.month][:3]
        year = month_date.year
        monthly_stats[f'{month_name} {year}'] = month_count
    
    # Current month breakdown by status
    current_month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if current_date.month == 12:
        current_month_end = current_month_start.replace(year=current_month_start.year + 1, month=1)
    else:
        current_month_end = current_month_start.replace(month=current_month_start.month + 1)
    
    current_month_requests = all_requests.filter(
        created_at__gte=current_month_start,
        created_at__lt=current_month_end
    )
    
    stats['current_month_stats'] = {
        'draft': current_month_requests.filter(status='draft').count(),
        'pending': current_month_requests.filter(status='pending_approval').count(),
        'approved': current_month_requests.filter(status='approved').count(),
        'rejected': current_month_requests.filter(status='rejected').count(),
        'rfq_sent': current_month_requests.filter(status='rfq_sent').count(),
        'awarded': current_month_requests.filter(status='awarded').count(),
    }
    
    stats['monthly_data'] = monthly_stats
    
    return JsonResponse(stats)


@login_required
@require_http_methods(["POST"])
def send_pr_pdf_email_view(request, pr_id):
    """
    Send Purchase Request PDF to a selected supplier's email.
    Only available for admin and purchasing_officer roles.
    Shows list of all suppliers to choose from.
    """
        # Check permission: only admin or purchasing_officer can send emails
    if request.user.role not in ['admin', 'purchasing_officer']:
        messages.error(request, 'You do not have permission to send emails. Only admins and purchasing officers can send emails.')
        return redirect('purchasing:request_detail', pr_id=pr_id)
    
    pr = get_object_or_404(PurchaseRequest, id=pr_id)
    
    # Only allow sending for approved requests (not pending_approval or rejected)
    if pr.status != 'approved':
        messages.error(request, 'Cannot send this request. Only approved requests can be sent to suppliers.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    supplier_id = request.POST.get('supplier_id', '').strip()
    custom_message = request.POST.get('custom_message', '').strip()
    
    if not supplier_id:
        messages.error(request, 'Please select a supplier.')
        return redirect('purchasing:request_detail', pr_id=pr.id)
    
    try:
        supplier = Supplier.objects.get(id=supplier_id)
        if not supplier.email:
            messages.error(request, f'Supplier "{supplier.name}" does not have an email address. Please update their profile first.')
            return redirect('purchasing:request_detail', pr_id=pr.id)
        
        success, msg = send_pr_pdf_to_email(pr, supplier.email, request.user, custom_message)
        if success:
            messages.success(request, f'Purchase request {pr.pr_number} has been sent to {supplier.name} ({supplier.email}) successfully.')
            # Create/update RFQ Log for tracking
            from .models import RFQLog
            rfq_log, created = RFQLog.objects.get_or_create(
                purchase_request=pr,
                supplier=supplier,
                defaults={'email_sent': True}
            )
            if not created:
                rfq_log.email_sent = True
                rfq_log.email_error = ''
                rfq_log.save()
            
            # Update status to rfq_sent
            if pr.status == 'approved':
                pr.status = 'rfq_sent'
                pr.save()
            
            # Log the activity
            from accounts.models import ActivityLog
            ActivityLog.objects.create(
                user=request.user,
                action='send_rfq',
                description=f'Sent PR {pr.pr_number} PDF to supplier {supplier.name} ({supplier.email})',
                model_name='PurchaseRequest',
                object_id=pr.id
            )
    except Supplier.DoesNotExist:
        messages.error(request, 'Supplier not found.')
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
    
    return redirect('purchasing:request_detail', pr_id=pr.id)


@login_required
def export_pr_pdf(request, pr_id):
    """Export Purchase Request as Professional PDF"""
    pr = get_object_or_404(
        PurchaseRequest.objects.select_related(
            'created_by',
            'approved_by',
            'rejected_by',
            'awarded_supplier'
        ),
        id=pr_id
    )

    # Use the same professional PDF function as email attachment
    pdf_bytes = generate_pr_pdf_bytes(pr)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{pr.pr_number}.pdf"'

    return response
