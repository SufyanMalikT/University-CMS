from django.urls import path
from .views import home_view, student_dashboard_view, student_add_courses_view, student_add_courses_page_view, \
                    student_course_review_page, student_enrolled_course_detail_page_view, student_course_by_semester_page_view, \
                    student_course_details_view, add_to_cart_view, cart_page_view, \
                    remove_course_from_cart_view, student_drop_course_page, results_page_view

urlpatterns = [
    path('dashboard/',student_dashboard_view, name='student_dashboard'),
    path('dashboard/academics/add_classes',student_add_courses_page_view, name='add_classes'),
    path('dashboard/academics/add_classes/<int:course_code_by_section>/enroll',student_add_courses_view, name='enroll_course'),
    path('dashboard/academics/course_details/<int:course_code_by_section>',student_course_details_view,name='course_details'),
    path('dashboard/academics/review_classes',student_course_review_page,name='review_classes_by_semester'),
    path('dashboard/academics/review_classes/semester/<int:semester_id>',student_course_by_semester_page_view,name='semester_details'),
    path('dashboard/academics/review_classes/enrolled_course_details/<int:enrollment_id>',student_enrolled_course_detail_page_view,name='enrolled_course_details'),
    path('dashboard/academics/drop_course_page/',student_drop_course_page,name='drop_course'),
    path('dashboard/academics/add_classes/<int:course_by_section_id>',add_to_cart_view, name='add_to_cart'),
    path('dashboard/academics/your_cart/',cart_page_view, name='cart'),
    path('dashboard/academics/your_cart/remove_item/<int:item_id>',remove_course_from_cart_view, name='remove_course_from_cart'),
    
    
    path('dashboard/examinations/result/',results_page_view, name='result'),
]