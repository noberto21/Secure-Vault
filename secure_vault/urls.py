from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from vault import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # File Vault App
    path('', views.file_list, name='file_list'),
    path('upload/', views.upload_file, name='upload'),
    path('download/<int:file_id>/', views.download_file, name='download'),
    path('delete/<int:file_id>/', views.delete_file, name='delete'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    
    # Authentication (Custom Templates in vault/templates/vault/)
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='vault/login.html',
        extra_context={'app_name': 'Secure Vault'}
    ), name='login'),
    
    path('accounts/logout/', auth_views.LogoutView.as_view(
        template_name='vault/logout.html',
        next_page='login'
    ), name='logout'),
    
    path('accounts/register/', views.register, name='register'),
    
    # Password Reset (if needed)
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='vault/password_reset.html',
        email_template_name='vault/password_reset_email.html',
        subject_template_name='vault/password_reset_subject.txt'
    ), name='password_reset'),
    
    path('accounts/', include('django.contrib.auth.urls')),  # Other auth URLs
    
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

