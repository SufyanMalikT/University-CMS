from django.urls import path
from ..views.instructor_views import instructor_overview_page
urlpatterns = [
    path('',instructor_overview_page, name='instructor_dashboard')
]