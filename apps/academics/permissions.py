from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from .models import Assessment

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

def assessment_updation_deletion(view):
    @wraps(view)
    def wrapper(request,pk,*args,**kwargs):
        assessment = get_object_or_404(Assessment,pk=pk)
        if not assessment.is_modifiable:
            return HttpResponseForbidden('The assessment cannot be deleted or updated because one or more mark entries exist of this assessment')
        
        if assessment.course_by_section.semester.is_past_deadline_for_grading:
            return HttpResponseForbidden("The assessment cannot be deleted or updated because the deadline for grading has passed")
        return view(request,pk,*args, **kwargs)
    return wrapper

def upload_and_update_marks(view):
    @wraps(view)
    def wrapper(request,pk,*args,**kwargs):
        assessment = get_object_or_404(Assessment, pk=pk)
        if assessment.course_by_section.semester.is_past_deadline_for_grading:
            raise HttpResponseForbidden("Can't upload or update marks because the deadline has passed")
        return view(request,pk,*args,**kwargs)
    return wrapper