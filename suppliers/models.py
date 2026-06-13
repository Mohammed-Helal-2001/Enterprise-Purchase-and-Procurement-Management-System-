"""
Suppliers App - Models
Suppliers and raw materials management
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class Material(models.Model):
    """
    Raw Materials Table
    """
    name = models.CharField(_('Material Name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    unit = models.CharField(_('Unit'), max_length=50, help_text=_('e.g. pc, kg, liter'))
    category = models.CharField(_('Category'), max_length=100, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Raw Material')
        verbose_name_plural = _('Raw Materials')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Supplier(models.Model):
    """
    Suppliers Table
    """
    name = models.CharField(_('Supplier Name'), max_length=200)
    email = models.EmailField(_('Email Address'), unique=True)
    phone = models.CharField(_('Phone Number'), max_length=20)
    address = models.TextField(_('Address'))
    contact_person = models.CharField(_('Contact Person'), max_length=100, blank=True)
    rating = models.DecimalField(
        _('Rating'),
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text=_('Rating from 0 to 5')
    )
    total_orders = models.PositiveIntegerField(_('Total Orders'), default=0)
    is_active = models.BooleanField(_('Active'), default=True)
    notes = models.TextField(_('Notes'), blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_rating_display(self):
        """Display rating as stars"""
        full_stars = int(self.rating)
        half_star = (self.rating - full_stars) >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        return '★' * full_stars + ('½' if half_star else '') + '☆' * empty_stars


class SupplierMaterialPrice(models.Model):
    """
    Supplier Material Price Table
    Reference prices only - not final prices
    """
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.CASCADE, 
        related_name='material_prices',
        verbose_name=_('Supplier')
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='supplier_prices',
        verbose_name=_('Material')
    )
    reference_price = models.DecimalField(
        _('Reference Price'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Reference price only, not final price')
    )
    lead_time = models.PositiveIntegerField(
        _('Lead Time (days)'),
        default=0
    )
    is_available = models.BooleanField(_('Available'), default=True)
    last_updated = models.DateTimeField(_('Last Updated'), auto_now=True)
    
    class Meta:
        verbose_name = _('Supplier Material Price')
        verbose_name_plural = _('Supplier Material Prices')
        unique_together = ['supplier', 'material']
    
    def __str__(self):
        return f'{self.supplier.name} - {self.material.name}'


class Quotation(models.Model):
    """
    Quotation Table
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('rejected', _('Rejected')),
        ('expired', _('Expired')),
    ]
    
    purchase_request = models.ForeignKey(
        'purchasing.PurchaseRequest',
        on_delete=models.CASCADE,
        related_name='quotations',
        verbose_name=_('Purchase Request')
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='quotations',
        verbose_name=_('Supplier')
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    total_amount = models.DecimalField(
        _('Total Amount'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    delivery_days = models.PositiveIntegerField(_('Lead Time (days)'), default=0)
    valid_until = models.DateField(_('Valid Until'), blank=True, null=True)
    notes = models.TextField(_('Notes'), blank=True)
    is_winner = models.BooleanField(_('Winner'), default=False)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Quotation')
        verbose_name_plural = _('Quotations')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.supplier.name} - {self.purchase_request.pr_number}'
    
    def calculate_total(self):
        """Calculate total from items"""
        total = sum(item.total_price for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total


class QuotationItem(models.Model):
    """
    Quotation Item Table
    """
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Quotation')
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        verbose_name=_('Material')
    )
    quantity = models.DecimalField(
        _('Quantity'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    unit_price = models.DecimalField(
        _('Unit Price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    delivery_days = models.PositiveIntegerField(_('Lead Time (days)'), default=0)
    notes = models.TextField(_('Notes'), blank=True)
    
    class Meta:
        verbose_name = _('Quotation Item')
        verbose_name_plural = _('Quotation Items')
    
    def __str__(self):
        return f'{self.quotation.supplier.name} - {self.material.name}'
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price