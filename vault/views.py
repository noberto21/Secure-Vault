from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, FileResponse
from django.conf import settings
from .models import VaultFile, AccessLog, UserProfile
from .forms import UploadFileForm
from .utils.crypto import encrypt_file, decrypt_file, generate_key
from .utils.audit import log_access
import os
import tempfile
import hashlib
from django.core.files.base import ContentFile
from django.contrib import messages

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            password = form.cleaned_data['encryption_password']
            
            # Generate encryption key
            key, salt = generate_key(password)
            key_hash = hashlib.sha256(key).hexdigest()
            
            # Save original file temporarily
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            
            # Encrypt the file
            encrypted_data, iv = encrypt_file(tmp_path, key)
            os.unlink(tmp_path)  # Delete temp file
            
            # Save encrypted file to storage
            vault_file = VaultFile(
                owner=request.user,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                iv=iv,
                key_hash=key_hash
            )
            vault_file.encrypted_file.save(
                uploaded_file.name,
                ContentFile(encrypted_data)
            )
            vault_file.save()
            
            # Log the upload
            log_access(
                request.user,
                'UPLOAD',
                request,
                file=vault_file,
                additional_info={'file_size': uploaded_file.size}
            )
            
            return redirect('file_list')
    else:
        form = UploadFileForm()
    
    return render(request, 'vault/upload.html', {'form': form})

@login_required
def download_file(request, file_id):
    vault_file = get_object_or_404(VaultFile, id=file_id, owner=request.user)
    
    if request.method == 'POST':
        password = request.POST.get('decryption_password')
        key, _ = generate_key(password, salt=None)
        key_hash = hashlib.sha256(key).hexdigest()
        
        if key_hash != vault_file.key_hash:
            # Log failed attempt
            log_access(
                request.user,
                'DOWNLOAD',
                request,
                file=vault_file,
                additional_info={'status': 'failed', 'reason': 'wrong_password'}
            )
            return render(request, 'vault/download.html', {
                'file': vault_file,
                'error': 'Incorrect password'
            })
        
        # Decrypt the file
        encrypted_data = vault_file.encrypted_file.read()
        decrypted_data = decrypt_file(encrypted_data, key, bytes(vault_file.iv))
        
        # Log successful download
        log_access(
            request.user,
            'DOWNLOAD',
            request,
            file=vault_file,
            additional_info={'status': 'success'}
        )
        
        # Create a temporary file for download
        response = HttpResponse(decrypted_data, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{vault_file.original_filename}"'
        return response
    
    return render(request, 'vault/download.html', {'file': vault_file})

@login_required
def file_list(request):
    files = VaultFile.objects.filter(owner=request.user)
    return render(request, 'vault/file_list.html', {'files': files})

@user_passes_test(lambda u: hasattr(u, 'userprofile') and getattr(getattr(u, 'userprofile', None), 'role', None) in ['admin', 'auditor'])
def audit_logs(request):
    logs = AccessLog.objects.all().order_by('-timestamp')
    
    # For auditors, only show logs for files they have access to
    userprofile = getattr(request.user, 'userprofile', None)
    if userprofile and getattr(userprofile, 'role', None) == 'auditor':
        logs = logs.filter(file__owner=request.user)
    
    return render(request, 'vault/audit_logs.html', {'logs': logs})

@login_required
def delete_file(request, file_id):
    vault_file = get_object_or_404(VaultFile, id=file_id, owner=request.user)
    
    if request.method == 'POST':
        # Log the deletion before actually deleting
        log_access(
            request.user,
            'DELETE',
            request,
            file=vault_file,
            additional_info={
                'filename': vault_file.original_filename,
                'size': vault_file.file_size
            }
        )
        
        # Delete the file
        file_path = vault_file.encrypted_file.path
        if os.path.exists(file_path):
            os.remove(file_path)
        vault_file.delete()
        
        messages.success(request, f'File "{vault_file.original_filename}" has been permanently deleted.')
        return redirect('file_list')
    
    return redirect('file_list')