from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from django.conf import settings
import os
import hashlib
import base64

from typing import Optional

def generate_key(password: str, salt: Optional[bytes] = None):
    """Generate encryption key from password"""
    if salt is None:
        salt = os.urandom(16)
    kdf = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000,
        dklen=32
    )
    return kdf, salt

def encrypt_file(file_path, key):
    """Encrypt file using AES-256-CBC"""
    iv = os.urandom(16)
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    with open(file_path, 'rb') as f:
        plaintext = f.read()
    
    # Pad the data to be a multiple of the block size
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    
    return encrypted_data, iv

def decrypt_file(encrypted_data, key, iv):
    """Decrypt file using AES-256-CBC"""
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    
    decrypted_padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
    
    # Unpad the data
    unpadder = padding.PKCS7(128).unpadder()
    decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()
    
    return decrypted_data