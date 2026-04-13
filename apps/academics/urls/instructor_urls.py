from django.urls import path
from ..views.instructor_views import instructor_overview_page, classes_details_page
app_name = 'academics/instructor'
urlpatterns = [
    path('',instructor_overview_page, name='instructor_dashboard'),
    path('class/details/<int:class_id>',classes_details_page, name='class_details')
]