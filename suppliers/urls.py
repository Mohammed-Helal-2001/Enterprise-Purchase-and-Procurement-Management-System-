"""
Suppliers App - URLs
"""

from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    # Suppliers
    path('', views.supplier_list, name='supplier_list'),
    path('create/', views.supplier_create, name='supplier_create'),
    path('<int:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    path('<int:supplier_id>/update/', views.supplier_update, name='supplier_update'),
    path('<int:supplier_id>/delete/', views.supplier_delete, name='supplier_delete'),
    path('<int:supplier_id>/add-price/', views.supplier_material_price_create, name='supplier_add_price'),
    
    # Materials
    path('materials/', views.material_list, name='material_list'),
    path('materials/create/', views.material_create, name='material_create'),
    path('materials/<int:material_id>/', views.material_detail, name='material_detail'),
    path('materials/<int:material_id>/update/', views.material_update, name='material_update'),
    path('materials/<int:material_id>/delete/', views.material_delete, name='material_delete'),
    
    # Quotations
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('quotations/<int:quotation_id>/', views.quotation_detail, name='quotation_detail'),
]