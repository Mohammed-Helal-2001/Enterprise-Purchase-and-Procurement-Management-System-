"""purchase_system URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='/login/', permanent=False), name='home'),
    path('admin/', admin.site.urls),
    path('', include('accounts.urls', namespace='accounts')),
    path('purchasing/', include('purchasing.urls', namespace='purchasing')),
    path('suppliers/', include('suppliers.urls', namespace='suppliers')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)