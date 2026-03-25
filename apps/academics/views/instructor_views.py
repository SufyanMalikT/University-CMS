from django.shortcuts import render
from ..permissions import instructor_only
from django.contrib.auth.decorators import login_required


@login_required
@instructor_only
def instructor_overview_page(request):
    return render(request, 'temps/academics/pages/InstructorDashboard/Overview.html', {})