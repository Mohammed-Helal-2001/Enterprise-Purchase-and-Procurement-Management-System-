"""
Accounts App - Models
User and permissions system
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom User Manager"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
            
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User Model
    """
    ROLE_CHOICES = [
        ('requester', _('Requester')),
        ('approver', _('Approver')),
        ('purchasing_officer', _('Purchasing Officer')),
        ('admin', _('Admin')),
    ]
    
    username = None
    email = models.EmailField(_('Email Address'), unique=True)
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='requester'
    )
    phone = models.CharField(_('Phone Number'), max_length=20, blank=True)
    department = models.CharField(_('Department'), max_length=100, blank=True)
    avatar = models.ImageField(_('Avatar'), upload_to='avatars/', blank=True, null=True)
    is_active = models.BooleanField(_('Active'), default=True)
    date_joined = models.DateTimeField(_('Date Joined'), auto_now_add=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.get_full_name() or self.email
    
    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
    
    @property
    def is_requester(self):
        return self.role == 'requester'
    
    @property
    def is_approver(self):
        return self.role == 'approver' or self.role == 'purchasing_officer'
    
    @property
    def is_purchasing_officer(self):
        return self.role == 'purchasing_officer'
    
    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser


class UserProfile(models.Model):
    """
    User Profile - Additional Information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    preferences = models.JSONField(_('Preferences'), default=dict, blank=True)
    notification_settings = models.JSONField(_('Notification Settings'), default=dict, blank=True)
    last_login_ip = models.GenericIPAddressField(_('Last Login IP'), blank=True, null=True)
    last_login = models.DateTimeField(_('Last Login'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f'{self.user.email} - Profile'


class ActivityLog(models.Model):
    """
    Activity Log - Track User Actions
    """
    ACTION_TYPES = [
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('create', _('Create')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('approve', _('Approve')),
        ('reject', _('Reject')),
        ('send_rfq', _('Send RFQ')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(_('Action'), max_length=20, choices=ACTION_TYPES)
    description = models.TextField(_('Description'))
    model_name = models.CharField(_('Model Name'), max_length=50, blank=True)
    object_id = models.PositiveIntegerField(_('Object ID'), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Activity Log')
        verbose_name_plural = _('Activity Logs')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.email} - {self.get_action_display()} - {self.created_at}'