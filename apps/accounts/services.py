from django.db import transaction
from .models import Instructor, Student

@transaction.atomic 
def InstructorRegistration(valid_form):
    user = valid_form.save(commit=False)
    password = valid_form.cleaned_data['password']
    user.set_password(password)
    user.save()
    instructor = Instructor.objects.create(user=user)

    return instructor


@transaction.atomic 
def StudentRegistration(valid_form):
    user = valid_form.save(commit=False)
    password = valid_form.cleaned_data['password']
    user.set_password(password)
    user.save()
    student = Student.objects.create(user=user)
    student.save()
    return student