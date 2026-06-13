"""
Purchasing App - Models
Purchase request management system
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.conf import settings


class PurchaseRequest(models.Model):
    """
    Purchase Request Table
    """
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('rfq_sent', _('RFQ Sent')),
        ('pending_approval', _('Pending Approval')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('awarded', _('Awarded')),
    ]
    
    pr_number = models.CharField(_('Request Number'), max_length=20, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchase_requests',
        verbose_name=_('Request Creator')
        )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    title = models.CharField(_('Request Title'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    
    # Additional fields for professional document
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('normal', _('Normal')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]
    priority = models.CharField(
        _('Priority'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal'
    )
    department = models.CharField(_('Department'), max_length=200, blank=True)
    
    # Approval fields
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_requests',
        verbose_name=_('Approved By')
    )
    approved_at = models.DateTimeField(_('Approval Date'), blank=True, null=True)
    rejection_reason = models.TextField(_('Rejection Reason'), blank=True)
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_requests',
        verbose_name=_('Rejected By')
    )
    rejected_at = models.DateTimeField(_('Rejection Date'), blank=True, null=True)
    
    # Award fields
    awarded_supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='awarded_requests',
        verbose_name=_('Awarded Supplier')
    )
    awarded_at = models.DateTimeField(_('Award Date'), blank=True, null=True)
    
    # Notes
    notes = models.TextField(_('Notes'), blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Purchase Request')
        verbose_name_plural = _('Purchase Requests')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.pr_number} - {self.title}'
    
    def save(self, *args, **kwargs):
        if not self.pr_number:
            # Generate PR number
            last_pr = PurchaseRequest.objects.order_by('-id').first()
            if last_pr:
                last_num = int(last_pr.pr_number.replace('PR-', ''))
                self.pr_number = f'PR-{last_num + 1:05d}'
            else:
                self.pr_number = 'PR-00001'
        super().save(*args, **kwargs)
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def total_quotations(self):
        return self.quotations.count()


class PurchaseItem(models.Model):
    """
    Purchase Item Table
    """
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Purchase Request')
    )
    material = models.ForeignKey(
        'suppliers.Material',
        on_delete=models.CASCADE,
        verbose_name=_('Material')
    )
    quantity = models.DecimalField(
        _('Quantity'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    description = models.TextField(_('Description'), blank=True)
    notes = models.TextField(_('Notes'), blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Purchase Item')
        verbose_name_plural = _('Purchase Items')
    
    def __str__(self):
        return f'{self.purchase_request.pr_number} - {self.material.name}'


class RFQLog(models.Model):
    """
    RFQ Sending Log
    """
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='rfq_logs',
        verbose_name=_('Purchase Request')
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.CASCADE,
        related_name='rfq_logs',
        verbose_name=_('Supplier')
    )
    sent_at = models.DateTimeField(_('Sent At'), auto_now_add=True)
    email_sent = models.BooleanField(_('Email Sent'), default=False)
    email_error = models.TextField(_('Email Error'), blank=True)
    
    class Meta:
        verbose_name = _('RFQ Log')
        verbose_name_plural = _('RFQ Logs')
        unique_together = ['purchase_request', 'supplier']
    
    def __str__(self):
        return f'{self.purchase_request.pr_number} - {self.supplier.name}'


class ApprovalHistory(models.Model):
    """
    Approval History
    """
    ACTION_CHOICES = [
        ('approve', _('Approve')),
        ('reject', _('Reject')),
        ('submit', _('Submit for Approval')),
        ('award', _('Award Supplier')),
    ]
    
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='approval_history',
        verbose_name=_('Purchase Request')
    )
    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('By')
    )
    action = models.CharField(_('Action'), max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField(_('Reason'), blank=True)
    notes = models.TextField(_('Notes'), blank=True)
    created_at = models.DateTimeField(_('Action Date'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Approval History')
        verbose_name_plural = _('Approval Histories')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.purchase_request.pr_number} - {self.action}'