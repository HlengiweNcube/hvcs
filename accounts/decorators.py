from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Allow the view only for the given role(s); 403 otherwise.

    Usage:
        @role_required(User.Role.ADMIN)
        def admin_dashboard(request): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
