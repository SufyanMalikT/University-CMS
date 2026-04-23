from django.urls import path
from ..views.instructor_views import instructor_overview_page, classes_details_page, \
                                    attendance_page_for_class, mark_attendance_view, \
                                    assigned_courses_page
app_name = 'academics/instructor'
urlpatterns = [
    path('',instructor_overview_page, name='instructor_dashboard'),
    path('class/details/<int:class_id>',classes_details_page, name='class_details'),
    path('classes/records',assigned_courses_page, name='assigned_classes'),
    path('class/attendance/<int:course_by_section_id>',attendance_page_for_class, name='attendance_page_for_class'),
    path('class/attendance/<int:course_by_section_id>/mark',mark_attendance_view, name='mark_attendance_for_class'),
]