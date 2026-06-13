"""
Suppliers App - Admin Configuration
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Material, Supplier, SupplierMaterialPrice, Quotation, QuotationItem


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'unit', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'rating', 'total_orders', 'is_active', 'created_at']
    list_filter = ['is_active', 'rating']
    search_fields = ['name', 'email', 'phone', 'contact_person']
    list_editable = ['is_active']
    readonly_fields = ['total_orders', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'email', 'phone')
        }),
        (_('Contact Information'), {
            'fields': ('address', 'contact_person')
        }),
        (_('Additional Information'), {
            'fields': ('rating', 'total_orders', 'is_active', 'notes')
        }),
    )


@admin.register(SupplierMaterialPrice)
class SupplierMaterialPriceAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'material', 'reference_price', 'lead_time', 'is_available', 'last_updated']
    list_filter = ['supplier', 'material', 'is_available']
    search_fields = ['supplier__name', 'material__name']
    raw_id_fields = ['supplier', 'material']


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['purchase_request', 'supplier', 'status', 'total_amount', 'delivery_days', 'is_winner', 'created_at']
    list_filter = ['status', 'is_winner', 'created_at']
    search_fields = ['purchase_request__pr_number', 'supplier__name']
    raw_id_fields = ['purchase_request', 'supplier']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Quotation Information'), {
            'fields': ('purchase_request', 'supplier', 'status')
        }),
        (_('Financial Information'), {
            'fields': ('total_amount', 'delivery_days', 'valid_until')
        }),
        (_('Additional Information'), {
            'fields': ('is_winner', 'notes')
        }),
    )


@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    list_display = ['quotation', 'material', 'quantity', 'unit_price', 'total_price', 'delivery_days']
    list_filter = ['material']
    raw_id_fields = ['quotation', 'material']
    readonly_fields = ['total_price']