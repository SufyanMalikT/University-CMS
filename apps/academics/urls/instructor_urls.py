from django.urls import path
from ..views.instructor_views import instructor_overview_page, classes_details_page, \
                                    attendance_page_for_class, mark_attendance_view, \
                                    assigned_courses_page_for_attendance, assessment_management_page_view, \
                                    update_assessment_page_view, delete_assessment_view, mark_entry_by_assessment_page_view, \
                                    grade_book_by_section, assigned_courses_page_for_marks
app_name = 'academics/instructor'
urlpatterns = [
    path('',instructor_overview_page, name='instructor_dashboard'),
    path('class/details/attendance/<int:pk>',classes_details_page, name='class_details'),
    path('classes/records/attendance',assigned_courses_page_for_attendance, name='assigned_classes_for_attendance'),
    path('classes/records/marks',assigned_courses_page_for_marks, name='assigned_classes_for_marks'),
    path('class/attendance/<int:course_by_section_id>',attendance_page_for_class, name='attendance_page_for_class'),
    path('class/attendance/<int:course_by_section_id>/mark',mark_attendance_view, name='mark_attendance_for_class'),
    path('class/assessments/<int:course_code_by_section>/',assessment_management_page_view, name='assessment_management'),
    path('class/assessment/<int:pk>/update',update_assessment_page_view, name='update_assessment'),
    path('class/assessment/<int:pk>/delete',delete_assessment_view, name='delete_assessment'),
    path('class/assessment/<int:pk>/upload_marks',mark_entry_by_assessment_page_view, name='upload_marks_by_assessment'),
    path('class/gradebook/<int:pk>',grade_book_by_section, name='grade_book')
]