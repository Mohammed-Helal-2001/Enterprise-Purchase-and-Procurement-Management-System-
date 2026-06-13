"""
Purchasing App - URLs
"""

from django.urls import path
from . import views

app_name = 'purchasing'

urlpatterns = [
    # Purchase Requests
    path('', views.purchase_request_list, name='request_list'),
    path('create/', views.purchase_request_create, name='request_create'),
    path('<int:pr_id>/', views.purchase_request_detail, name='request_detail'),
    path('<int:pr_id>/update/', views.purchase_request_update, name='request_update'),
    
    # RFQ
    path('<int:pr_id>/send-rfq/', views.send_rfq_view, name='send_rfq'),
    
    # Supplier Suggestion
    path('suggest-supplier/<int:pr_id>/', views.suggest_supplier_view, name='suggest_supplier'),
    
    # Approval/Rejection
    path('submit/<int:pr_id>/', views.submit_for_approval_view, name='submit_for_approval'),
    path('approve-request/<int:pr_id>/', views.approve_request_view, name='approve_request'),
    path('reject-request/<int:pr_id>/', views.reject_request_view, name='reject_request'),
    path('award-supplier/<int:pr_id>/', views.award_supplier_view, name='award_supplier'),
    
        # Quotation
    path('quotations/', views.quotation_requests_list, name='quotation_requests_list'),
    path('<int:pr_id>/quotation/', views.quotation_create, name='quotation_create'),
    path('<int:pr_id>/comparison/', views.quotation_comparison, name='quotation_comparison'),
    
        # PDF Export
    path('<int:pr_id>/pdf/', views.export_pr_pdf, name='export_pr_pdf'),
    
    # Send PR via Email
    path('<int:pr_id>/send-email/', views.send_pr_pdf_email_view, name='send_pr_email'),
    
    # API
    path('api/stats/', views.dashboard_stats, name='dashboard_stats'),
]