from django.urls import path
from .views import student_registration_view,instructor_registration_view,login_view, logout_view
urlpatterns = [
    path('register/student',student_registration_view, name='student_form'),
    path('register/instructor',instructor_registration_view, name='instructor_form'),
    path('login',login_view, name='login'),
    path('logout',logout_view, name='logout'),
]