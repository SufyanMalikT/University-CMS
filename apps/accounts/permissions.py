from functools import wraps 
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

def admin_only(myview):
    @wraps(myview)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_superuser:
            return HttpResponseForbidden("Admins Only")
        
        return myview(request, *args, **kwargs)
    return _wrapped
        