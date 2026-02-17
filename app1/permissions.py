from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

def instructor_only(myview):
    @wraps(myview)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not hasattr(request.user,'instructor'):
            return HttpResponseForbidden("Instrcutors Only")
        
        return myview(request, *args, **kwargs)
    return _wrapped

def student_only(myview):
    @wraps(myview)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if hasattr(request.user,'student'):
            return HttpResponseForbidden("Students Only")
        return myview(request, *args, **kwargs)
    return _wrapped