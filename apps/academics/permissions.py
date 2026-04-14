from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

def instructor_only(myview):
    @wraps(myview)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if not hasattr(request.user,'instructor_profile'):
            return HttpResponseForbidden("Instructors Only")
        
        return myview(request, *args, **kwargs)
    return _wrapped

def student_only(myview):
    @wraps(myview)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if not hasattr(request.user,'student_profile'):
            return HttpResponseForbidden("Students Only")
        return myview(request, *args, **kwargs)
    return _wrapped