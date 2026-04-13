from django.shortcuts import render
from ..permissions import instructor_only
from django.contrib.auth.decorators import login_required
from ..models import CourseBySection
from django.shortcuts import get_object_or_404
@login_required
@instructor_only
def instructor_overview_page(request):
    return render(request, 'temps/academics/pages/InstructorDashboard/Overview.html', {})


@login_required
@instructor_only
def classes_details_page(request, class_id):
    course_by_section = get_object_or_404(CourseBySection, course_code_by_section=class_id)
    pending_grading = None
    if course_by_section.pending_grading is not None:
        pending_grading = course_by_section.pending_grading
    return render(request, 'temps/academics/pages/InstructorDashboard/classes-details.html',{'class':course_by_section,'pending_grading':pending_grading})