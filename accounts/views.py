"""
Accounts App - Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import User, ActivityLog


def login_view(request):
    """Login View"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        # Validate inputs
        if not email:
            messages.error(request, _('Email address is required'))
            return render(request, 'accounts/login.html')
        
        if not password:
            messages.error(request, _('Password is required'))
            return render(request, 'accounts/login.html')
        
        # Use email for authentication since username is None
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.email, password=password)
        except User.DoesNotExist:
            messages.error(request, _('Email address not found in the system'))
            return render(request, 'accounts/login.html')
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, _('Welcome {}').format(user.get_full_name() or user.email))
                
                # Log activity
                ActivityLog.objects.create(
                    user=user,
                    action='login',
                    description='Successful login',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                next_url = request.GET.get('next')
                return redirect(next_url if next_url else 'accounts:dashboard')
            else:
                messages.error(request, _('Account is inactive. Please contact an administrator'))
                return render(request, 'accounts/login.html')
        else:
            messages.error(request, _('Password is incorrect. Please check your email and password'))
            return render(request, 'accounts/login.html')
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Logout View"""
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action='logout',
            description='Logout',
            ip_address=request.META.get('REMOTE_ADDR')
        )
    
    logout(request)
    messages.info(request, _('Successfully logged out'))
    return redirect('accounts:login')


@login_required
def dashboard(request):
    """Dashboard View - Different content based on user role"""
    from purchasing.models import PurchaseRequest
    from suppliers.models import Supplier
    
    user = request.user
    
    # Initialize variables
    title = 'Dashboard'
    recent_requests = []
    stats = {}
    
    if user.role == 'requester':
        # Requester sees only their own requests
        my_requests = PurchaseRequest.objects.filter(created_by=user)
        stats = {
            'total': my_requests.count(),
            'draft': my_requests.filter(status='draft').count(),
            'pending': my_requests.filter(status='pending_approval').count(),
            'approved': my_requests.filter(status='approved').count(),
            'rejected': my_requests.filter(status='rejected').count(),
            'awarded': my_requests.filter(status='awarded').count(),
        }
        recent_requests = my_requests.order_by('-created_at')[:5]
        title = 'My Requests'
        
    elif user.role == 'admin':
        # Admin sees all requests
        all_requests = PurchaseRequest.objects.all()
        stats = {
            'total': all_requests.count(),
            'draft': all_requests.filter(status='draft').count(),
            'pending': all_requests.filter(status='pending_approval').count(),
            'approved': all_requests.filter(status='approved').count(),
            'rejected': all_requests.filter(status='rejected').count(),
            'awarded': all_requests.filter(status='awarded').count(),
        }
        recent_requests = all_requests.order_by('-created_at')[:5]
        title = 'Dashboard - All Requests'
        
    elif user.role == 'approver':
        # Approver sees requests pending approval
        pending = PurchaseRequest.objects.filter(status='pending_approval')
        stats = {
            'total': PurchaseRequest.objects.count(),
            'pending': pending.count(),
            'approved_today': PurchaseRequest.objects.filter(
                status='approved',
                approved_at__date=timezone.now().date()
            ).count(),
            'rejected_today': PurchaseRequest.objects.filter(
                status='rejected',
                rejected_at__date=timezone.now().date()
            ).count(),
        }
        recent_requests = pending.select_related('created_by').order_by('-created_at')[:5]
        title = 'Requests Pending Approval'
        
    elif user.role == 'purchasing_officer':
        # Purchasing officer sees approved requests for RFQ and awarding
        approved = PurchaseRequest.objects.filter(status='approved')
        rfq_sent = PurchaseRequest.objects.filter(status='rfq_sent')
        stats = {
            'total': PurchaseRequest.objects.count(),
            'approved': approved.count(),
            'rfq_sent': rfq_sent.count(),
            'awarded': PurchaseRequest.objects.filter(status='awarded').count(),
            'pending_approval': PurchaseRequest.objects.filter(status='pending_approval').count(),
        }
        recent_requests = approved.select_related('created_by').order_by('-created_at')[:5]
        title = 'Approved Requests - Send RFQ'
    
    # Get suppliers count for dashboard summary
    total_suppliers = Supplier.objects.count()
    
    context = {
        'title': title,
        'stats': stats,
        'recent_requests': recent_requests,
        'total_suppliers': total_suppliers,
    }
    
    return render(request, 'accounts/dashboard.html', context)


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """User List View"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_superuser
    
    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add activity log for admin
        if self.request.user.is_admin or self.request.user.is_superuser:
            from .models import ActivityLog
            context['recent_activity'] = ActivityLog.objects.select_related('user')[:10]
        return context


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """User Create View"""
    model = User
    template_name = 'accounts/user_form.html'
    fields = ['email', 'first_name', 'last_name', 'role', 'phone', 'department', 'password']
    success_url = reverse_lazy('accounts:user_list')
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_superuser
    
    def form_valid(self, form):
        email = form.cleaned_data.get('email', '').strip()
        
        # Check for duplicate email (case-insensitive)
        if User.objects.filter(email__iexact=email).exists():
            form.add_error('email', _('A user with this email already exists.'))
            return self.form_invalid(form)
        
        # get password before saving user
        password = form.cleaned_data.get('password')
        
        # temporarily save user without setting password
        response = super().form_valid(form)
        
        # set the password properly
        self.object.set_password(password)
        self.object.save()
        
        messages.success(self.request, _('User created successfully'))
        return response


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """User Update View"""
    model = User
    template_name = 'accounts/user_form.html'
    fields = ['email', 'first_name', 'last_name', 'role', 'phone', 'department', 'is_active']
    success_url = reverse_lazy('accounts:user_list')
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_superuser
    
    def get_object(self, queryset=None):
        """Return the user object based on pk from URL (for admin only)"""
        # Admin/superuser can edit any user by pk
        if self.request.user.is_admin or self.request.user.is_superuser:
            return get_object_or_404(User, pk=self.kwargs.get('pk'))
        # Non-admin should never reach here (test_func blocks them), but just in case
        return self.request.user
    
    def form_valid(self, form):
        email = form.cleaned_data.get('email', '').strip()
        
        # Check for duplicate email (exclude current user)
        if User.objects.filter(email__iexact=email).exclude(pk=self.object.pk).exists():
            form.add_error('email', _('A user with this email already exists.'))
            return self.form_invalid(form)
        
        messages.success(self.request, _('User updated successfully'))
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """User Delete View - Cannot delete the last admin"""
    model = User
    template_name = 'accounts/user_delete.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        admin_count = User.objects.filter(role='admin').count()
        context['is_last_admin'] = (obj.role == 'admin' and admin_count <= 1)
        return context
    
    def form_valid(self, form):
        obj = self.get_object()
        admin_count = User.objects.filter(role='admin').count()
        
        # Prevent deleting last admin
        if obj.role == 'admin' and admin_count <= 1:
            messages.error(self.request, _('Cannot delete the last admin account. Create another admin first.'))
            return redirect('accounts:user_list')
        
        messages.success(self.request, _('User deleted successfully'))
        return super().form_valid(form)


@login_required
def profile_view(request):
    """User Profile View - View only info + change password only"""
    if request.method == 'POST':
        # Change password (only action allowed)
        if 'change_password' in request.POST:
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if not request.user.check_password(current_password):
                messages.error(request, _('Current password is incorrect'))
            elif new_password != confirm_password:
                messages.error(request, _('New passwords do not match'))
            elif len(new_password) < 6:
                messages.error(request, _('Password must be at least 6 characters'))
            else:
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, _('Password changed successfully'))
                # Re-authenticate to keep user logged in
                from django.contrib.auth import authenticate
                user = authenticate(request, username=request.user.email, password=new_password)
                if user:
                    login(request, user)
    
    # Get recent activities
    recent_activities = ActivityLog.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'recent_activities': recent_activities
    })


@login_required
def activity_log_view(request):
    """Activity Log View"""
    if not request.user.is_admin:
        messages.error(request, _('You do not have permission to view this page'))
        return redirect('accounts:dashboard')
    
    # Get filter parameters
    user_id = request.GET.get('user')
    action = request.GET.get('action')
    
    # Base queryset
    activities = ActivityLog.objects.select_related('user').order_by('-created_at')
    
    # Apply filters
    if user_id:
        activities = activities.filter(user_id=user_id)
    if action:
        activities = activities.filter(action=action)
    
    # Paginate
    from django.core.paginator import Paginator
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all users for filter dropdown
    users = User.objects.all()
    
    return render(request, 'accounts/activity_log.html', {
        'activities': page_obj,
        'users': users
    })