from django.urls import path , include
from rest_framework.routers import SimpleRouter
from .views import CustomUserViewSet, StudentViewSet
router = SimpleRouter()
router.register(r'user',CustomUserViewSet,basename='user')
router.register(r'student',StudentViewSet,basename='student')

urlpatterns = [
    path('',include(router.urls))
]