from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from vault import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.file_list, name='file_list'),
    path('upload/', views.upload_file, name='upload'),
    path('download/<int:file_id>/', views.download_file, name='download'),
    path('delete/<int:file_id>/', views.delete_file, name='delete'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='vault/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)