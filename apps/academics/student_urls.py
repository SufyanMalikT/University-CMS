from django.urls import path
from .views import home_view, student_dashboard_view, student_add_courses_view, student_add_courses_page_view, \
                    student_course_review_page, course_detail_page_view, student_course_by_semester_page_view, \
                    student_enrolled_course_details_view, student_drop_course_view, add_to_cart_view, cart_page_view, \
                    remove_course_from_cart_view

urlpatterns = [
    path('dashboard/',student_dashboard_view, name='student_dashboard'),
    path('StudentDashboard/enrollment/add_classes',student_add_courses_page_view, name='add_classes'),
    path('StudentDashboard/enrollment/add_classes/<int:course_code_by_section>/enroll',student_add_courses_view, name='enroll_course'),
    path('StudentDashboard/enrollment/review_classes',student_course_review_page,name='review_classes_by_semester'),
    path('StudentDashboard/enrollment/review_classes/<int:semester_id>',student_course_by_semester_page_view,name='review_classes'),
    path('StudentDashboard/enrollment/enrolled_course_details/<int:semester_id>/<int:course_code_by_section>',student_enrolled_course_details_view,name='enrolled_course_details'),
    path('StudentDashboard/enrollment/drop_course/<int:enrollment_id>',student_drop_course_view,name='drop_course'),
    path('StudentDashboard/enrollment/course_details/<int:course_code_by_section>',course_detail_page_view,name='course_details'),
    path('StudentDashboard/enrollment/add_classes/<int:course_by_section_id>',add_to_cart_view, name='add_to_cart'),
    path('StudentDashboard/enrollment/your_cart/',cart_page_view, name='cart'),
    path('StudentDashboard/enrollment/your_cart/remove_item/<int:item_id>',remove_course_from_cart_view, name='remove_course_from_cart'),
]