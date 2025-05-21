from vault.models import AccessLog
from django.contrib.auth.models import User
from django.http import HttpRequest

def log_access(
    user: User,
    action: str,
    request: HttpRequest,
    file=None,
    additional_info=None
):
    """Create an audit log entry"""
    if additional_info is None:
        additional_info = {}
    
    AccessLog.objects.create(
        user=user,
        file=file,
        action=action,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        additional_info=additional_info
    )

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip