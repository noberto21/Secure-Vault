from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import os

def user_directory_path(instance, filename):
    # Files will be uploaded to MEDIA_ROOT/user_<id>/<uuid>_<filename>
    return f'user_{instance.owner.id}/{uuid.uuid4()}_{filename}'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    public_key = models.TextField(blank=True, null=True)  # For GPG if used
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Administrator'),
        ('user', 'Regular User'),
        ('auditor', 'Auditor')  # Read-only access to audit logs
    ], default='user')

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

class VaultFile(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    original_filename = models.CharField(max_length=255)
    encrypted_file = models.FileField(upload_to=user_directory_path)
    file_size = models.PositiveIntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    iv = models.BinaryField()  # Initialization vector for AES
    key_hash = models.CharField(max_length=64)  # SHA-256 of encryption key
    
    def __str__(self):
        return self.original_filename

class AccessLog(models.Model):
    ACTION_CHOICES = [
        ('UPLOAD', 'File Upload'),
        ('DOWNLOAD', 'File Download'),
        ('DELETE', 'File Deletion'),
        ('VIEW', 'File Metadata View'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file = models.ForeignKey(VaultFile, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    additional_info = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']