"""
Suppliers App - Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Supplier, Material, SupplierMaterialPrice, Quotation, QuotationItem


@login_required
def supplier_list(request):
    """Supplier List View"""
    search = request.GET.get('search')
    is_active = request.GET.get('is_active')
    
    queryset = Supplier.objects.order_by('name')
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active == 'true')
    
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'suppliers/supplier_list.html', {
        'page_obj': page_obj,
        'search': search,
    })


@login_required
def supplier_create(request):
    """Create Supplier View - with material links"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        contact_person = request.POST.get('contact_person')
        rating = request.POST.get('rating', 0)
        notes = request.POST.get('notes')
        
        # Check for duplicate name
        if Supplier.objects.filter(name__iexact=name).exists():
            messages.error(request, f'A supplier with the name "{name}" already exists.')
            materials = Material.objects.filter(is_active=True).order_by('category', 'name')
            return render(request, 'suppliers/supplier_form.html', {'materials': materials})
        
        # Check for duplicate email
        if Supplier.objects.filter(email__iexact=email).exists():
            messages.error(request, f'A supplier with the email "{email}" already exists.')
            materials = Material.objects.filter(is_active=True).order_by('category', 'name')
            return render(request, 'suppliers/supplier_form.html', {'materials': materials})
        
        supplier = Supplier.objects.create(
            name=name,
            email=email,
            phone=phone,
            address=address,
            contact_person=contact_person,
            rating=rating or 0,
            notes=notes
        )
        
        # Link selected materials
        material_ids = request.POST.getlist('materials[]')
        lead_times = request.POST.getlist('lead_time[]')
        for i, mat_id in enumerate(material_ids):
            if mat_id:
                lead_time = lead_times[i] if i < len(lead_times) else 7
                try:
                    SupplierMaterialPrice.objects.create(
                        supplier=supplier,
                        material_id=mat_id,
                        lead_time=int(lead_time) if lead_time else 7,
                        is_available=True
                    )
                except Exception:
                    pass
        
        messages.success(request, f'Supplier {supplier.name} created successfully')
        return redirect('suppliers:supplier_detail', supplier_id=supplier.id)
    
    materials = Material.objects.filter(is_active=True).order_by('category', 'name')
    return render(request, 'suppliers/supplier_form.html', {
        'materials': materials,
    })


@login_required
def supplier_detail(request, supplier_id):
    """Supplier Detail View"""
    supplier = get_object_or_404(
        Supplier.objects.prefetch_related('material_prices__material'),
        id=supplier_id
    )
    
    # Get quotations
    quotations = supplier.quotations.order_by('-created_at')[:10]
    
    # Get materials
    materials = Material.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'suppliers/supplier_detail.html', {
        'supplier': supplier,
        'quotations': quotations,
        'materials': materials,
    })


@login_required
def supplier_update(request, supplier_id):
    """Update Supplier View - with material links"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Check for duplicate name (exclude current supplier)
        if Supplier.objects.filter(name__iexact=name).exclude(id=supplier.id).exists():
            messages.error(request, f'A supplier with the name "{name}" already exists.')
            materials = Material.objects.filter(is_active=True).order_by('category', 'name')
            linked_material_ids = set(supplier.material_prices.values_list('material_id', flat=True))
            return render(request, 'suppliers/supplier_form.html', {
                'supplier': supplier, 'materials': materials, 'linked_material_ids': linked_material_ids,
            })
        
        # Check for duplicate email (exclude current supplier)
        if Supplier.objects.filter(email__iexact=email).exclude(id=supplier.id).exists():
            messages.error(request, f'A supplier with the email "{email}" already exists.')
            materials = Material.objects.filter(is_active=True).order_by('category', 'name')
            linked_material_ids = set(supplier.material_prices.values_list('material_id', flat=True))
            return render(request, 'suppliers/supplier_form.html', {
                'supplier': supplier, 'materials': materials, 'linked_material_ids': linked_material_ids,
            })
        
        supplier.name = name
        supplier.email = email
        supplier.phone = request.POST.get('phone')
        supplier.address = request.POST.get('address')
        supplier.contact_person = request.POST.get('contact_person')
        supplier.rating = request.POST.get('rating', 0) or 0
        supplier.notes = request.POST.get('notes')
        supplier.is_active = request.POST.get('is_active') == 'on'
        supplier.save()
        
        # Update material links
        material_ids = request.POST.getlist('materials[]')
        lead_times = request.POST.getlist('lead_time[]')
        
        current_ids = set(supplier.material_prices.values_list('material_id', flat=True))
        new_ids = set()
        
        for i, mat_id in enumerate(material_ids):
            if mat_id:
                mat_id_int = int(mat_id)
                new_ids.add(mat_id_int)
                lead_time = lead_times[i] if i < len(lead_times) else 7
                
                if mat_id_int in current_ids:
                    SupplierMaterialPrice.objects.filter(
                        supplier=supplier, material_id=mat_id_int
                    ).update(lead_time=int(lead_time) if lead_time else 7, is_available=True)
                else:
                    SupplierMaterialPrice.objects.create(
                        supplier=supplier,
                        material_id=mat_id_int,
                        lead_time=int(lead_time) if lead_time else 7,
                        is_available=True
                    )
        
        ids_to_remove = current_ids - new_ids
        SupplierMaterialPrice.objects.filter(supplier=supplier, material_id__in=ids_to_remove).delete()
        
        messages.success(request, 'Supplier updated successfully')
        return redirect('suppliers:supplier_detail', supplier_id=supplier.id)
    
    materials = Material.objects.filter(is_active=True).order_by('category', 'name')
    linked_material_ids = set(supplier.material_prices.values_list('material_id', flat=True))
    
    return render(request, 'suppliers/supplier_form.html', {
        'supplier': supplier,
        'materials': materials,
        'linked_material_ids': linked_material_ids,
    })


@login_required
def supplier_delete(request, supplier_id):
    """Delete Supplier View"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Supplier deleted successfully')
        return redirect('suppliers:supplier_list')
    
    return render(request, 'suppliers/supplier_confirm_delete.html', {'supplier': supplier})


@login_required
def material_list(request):
    """Material List View"""
    search = request.GET.get('search')
    category = request.GET.get('category')
    
    queryset = Material.objects.order_by('name')
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if category:
        queryset = queryset.filter(category=category)
    
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories
    categories = Material.objects.values_list('category', flat=True).distinct()
    
    return render(request, 'suppliers/material_list.html', {
        'page_obj': page_obj,
        'search': search,
        'categories': [c for c in categories if c],
    })


@login_required
def material_create(request):
    """Create Material View"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        unit = request.POST.get('unit')
        category = request.POST.get('category')
        
        material = Material.objects.create(
            name=name,
            description=description,
            unit=unit,
            category=category
        )
        
        messages.success(request, f'Material {material.name} created successfully')
        return redirect('suppliers:material_detail', material_id=material.id)
    
    return render(request, 'suppliers/material_form.html', {})


@login_required
def material_detail(request, material_id):
    """Material Detail View"""
    material = get_object_or_404(
        Material.objects.prefetch_related('supplier_prices__supplier'),
        id=material_id
    )
    
    # Get supplier prices
    supplier_prices = material.supplier_prices.select_related('supplier').order_by('supplier__name')
    
    return render(request, 'suppliers/material_detail.html', {
        'material': material,
        'supplier_prices': supplier_prices,
    })


@login_required
def material_update(request, material_id):
    """Update Material View"""
    material = get_object_or_404(Material, id=material_id)
    
    if request.method == 'POST':
        material.name = request.POST.get('name')
        material.description = request.POST.get('description')
        material.unit = request.POST.get('unit')
        material.category = request.POST.get('category')
        material.is_active = request.POST.get('is_active') == 'on'
        material.save()
        
        messages.success(request, 'Material updated successfully')
        return redirect('suppliers:material_detail', material_id=material.id)
    
    return render(request, 'suppliers/material_form.html', {'material': material})


@login_required
def material_delete(request, material_id):
    """Delete Material View"""
    material = get_object_or_404(Material, id=material_id)
    
    if request.method == 'POST':
        material.delete()
        messages.success(request, 'Material deleted successfully')
        return redirect('suppliers:material_list')
    
    return render(request, 'suppliers/material_confirm_delete.html', {'material': material})


@login_required
def supplier_material_price_create(request, supplier_id):
    """Create Supplier Material Price View"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        material_id = request.POST.get('material')
        reference_price = request.POST.get('reference_price')
        lead_time = request.POST.get('lead_time')
        
        try:
            material = Material.objects.get(id=material_id)
            
            price, created = SupplierMaterialPrice.objects.update_or_create(
                supplier=supplier,
                material=material,
                defaults={
                    'reference_price': reference_price or None,
                    'lead_time': lead_time or 0,
                    'is_available': True
                }
            )
            
            messages.success(request, 'Material price updated successfully')
        except Material.DoesNotExist:
            messages.error(request, 'Material not found')
        
        return redirect('suppliers:supplier_detail', supplier_id=supplier.id)
    
    materials = Material.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'suppliers/supplier_material_price_form.html', {
        'supplier': supplier,
        'materials': materials,
    })


@login_required
def quotation_list(request):
    """Quotation List View"""
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    queryset = Quotation.objects.select_related(
        'purchase_request',
        'supplier'
    ).order_by('-created_at')
    
    if status:
        queryset = queryset.filter(status=status)
    
    if search:
        queryset = queryset.filter(
            Q(purchase_request__pr_number__icontains=search) |
            Q(supplier__name__icontains=search)
        )
    
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'suppliers/quotation_list.html', {
        'page_obj': page_obj,
        'status': status,
    })


@login_required
def quotation_detail(request, quotation_id):
    """Quotation Detail View"""
    quotation = get_object_or_404(
        Quotation.objects.select_related(
            'purchase_request',
            'supplier'
        ).prefetch_related('items__material'),
        id=quotation_id
    )
    
    return render(request, 'suppliers/quotation_detail.html', {
        'quotation': quotation,
    })
