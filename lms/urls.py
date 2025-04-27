# project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('courses/', include('courses.urls')),
    path('enrollment/', include('enrollment.urls')),  # New enrollment app URLs
    path('quiz/', include('quiz.urls')),              # New quiz app URLs
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)