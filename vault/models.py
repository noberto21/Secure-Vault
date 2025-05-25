from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import uuid
import os

def user_directory_path(instance, filename):
    """Returns path for uploaded files: user_<id>/<uuid>_<filename>"""
    return f'user_{instance.owner.id}/{uuid.uuid4()}_{filename}'

class UserProfile(models.Model):
    """
    Extended user profile with role-based permissions
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,  # Ensures one profile per user
        related_name='profile'
    )
    public_key = models.TextField(blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Administrator'),
            ('user', 'Regular User'),
            ('auditor', 'Auditor')
        ],
        default='user'
    )

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s profile"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Atomic transaction to ensure one profile per user
    """
    if created:
        try:
            with transaction.atomic():
                UserProfile.objects.get_or_create(user=instance)
        except Exception as e:
            # Log error but don't break user creation
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(f"Couldn't create user profile: {e}")

class VaultFile(models.Model):
    """
    Encrypted file storage with metadata
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='files'
    )
    original_filename = models.CharField(max_length=255)
    encrypted_file = models.FileField(upload_to=user_directory_path)
    file_size = models.PositiveIntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    iv = models.BinaryField(help_text="Initialization vector for AES encryption")
    key_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of encryption key"
    )

    class Meta:
        ordering = ['-upload_date']
        verbose_name = 'Vault File'
        verbose_name_plural = 'Vault Files'

    def __str__(self):
        return self.original_filename

class AccessLog(models.Model):
    """
    Audit trail for all file operations
    """
    ACTION_CHOICES = [
        ('UPLOAD', 'File Upload'),
        ('DOWNLOAD', 'File Download'),
        ('DELETE', 'File Deletion'),
        ('VIEW', 'File Metadata View'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_logs'
    )
    file = models.ForeignKey(
        VaultFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_logs'
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    additional_info = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp'], name='accesslog_timestamp_idx'),
            models.Index(fields=['user'], name='accesslog_user_idx'),
            models.Index(fields=['file'], name='accesslog_file_idx'),
        ]
        verbose_name = 'Access Log'
        verbose_name_plural = 'Access Logs'

    def __str__(self):
        action_display = dict(self.ACTION_CHOICES).get(self.action, self.action)
        return f"{action_display} by {self.user or 'system'} at {self.timestamp}"