from django.contrib import admin
from .models import CustomUser, Student, Instructor
# Register your models here.


admin.site.register(CustomUser)
admin.site.register(Student)
admin.site.register(Instructor)