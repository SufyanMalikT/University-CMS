from django.db import transaction
from app1.models import Instructor
from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
@transaction.atomic 
def InstructorRegistration(valid_form):
    user = valid_form.save(commit=False)
    password = valid_form.cleaned_data['password']
    user.set_password(password)
    user.save()
    instructor = Instructor.objects.create(user=user)

    return instructor

