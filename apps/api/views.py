from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .serializers import CustomUserSerializer, StudentSerializer
from ..accounts.models import CustomUser, Student, Instructor
# Create your views here.

class CustomUserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

class StudentViewSet(ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer