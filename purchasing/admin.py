"""
Purchasing App - Admin Configuration
"""
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from .models import PurchaseRequest, PurchaseItem, RFQLog, ApprovalHistory


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ['pr_number', 'created_by', 'title', 'status', 'total_items', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['pr_number', 'title', 'description']
    raw_id_fields = ['created_by', 'approved_by', 'rejected_by', 'awarded_supplier']
    readonly_fields = ['pr_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Request Information'), {
            'fields': ('pr_number', 'created_by', 'title', 'description')
        }),
        (_('Status'), {
            'fields': ('status', 'notes')
        }),
        (_('Approval'), {
            'fields': ('approved_by', 'approved_at')
        }),
        (_('Rejection'), {
            'fields': ('rejected_by', 'rejected_at', 'rejection_reason')
        }),
        (_('Award'), {
            'fields': ('awarded_supplier', 'awarded_at')
        }),
    )
    
    actions = ['send_rfq', 'approve_requests', 'reject_requests']
    
    def send_rfq(self, request, queryset):
        for pr in queryset:
            from .services import send_rfq_to_suppliers
            send_rfq_to_suppliers(pr)
        self.message_user(request, f'Sent RFQ for {queryset.count()} purchase request(s).')
    send_rfq.short_description = _('Send RFQ to suppliers')
    
    def approve_requests(self, request, queryset):
        queryset.update(status='approved', approved_by=request.user)
        self.message_user(request, f'Approved {queryset.count()} purchase request(s).')
    approve_requests.short_description = _('Approve selected requests')
    
    def reject_requests(self, request, queryset):
        queryset.update(status='rejected', rejected_by=request.user)
        self.message_user(request, f'Rejected {queryset.count()} purchase request(s).')
    reject_requests.short_description = _('Reject selected requests')


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_request', 'material', 'quantity', 'created_at']
    list_filter = ['material']
    raw_id_fields = ['purchase_request', 'material']
    search_fields = ['purchase_request__pr_number', 'material__name']


@admin.register(RFQLog)
class RFQLogAdmin(admin.ModelAdmin):
    list_display = ['purchase_request', 'supplier', 'sent_at', 'email_sent']
    list_filter = ['email_sent', 'sent_at']
    raw_id_fields = ['purchase_request', 'supplier']
    readonly_fields = ['sent_at']


@admin.register(ApprovalHistory)
class ApprovalHistoryAdmin(admin.ModelAdmin):
    list_display = ['purchase_request', 'action_by', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    raw_id_fields = ['purchase_request', 'action_by']
    readonly_fields = ['created_at']