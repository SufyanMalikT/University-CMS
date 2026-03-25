from django import template
from ..models import CourseAssignment, Semester

register = template.Library()

@register.inclusion_tag('comps/InstructorDashboard/sidebar.html',takes_context=True)
def render_instructor_sidebar(context):
    request = context['request']

    assignments = CourseAssignment.objects.filter(semester=Semester.latest_semester(), instructor=request.user.instructor_profile).select_related('course_by_section','course_by_section__course','course_by_section__section')
    return {
        'assignments':assignments,
        'request':request
    }