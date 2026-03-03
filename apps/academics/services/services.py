from django.db import transaction
from app1.forms import StudentRegistrationForm
from academics.models import Student, CourseBySection, Semester, Enrollment, VoucherItem, FeeConfiguration, \
                         FeeVoucher,   Payment
from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.utils import timezone
@transaction.atomic 
def StudentRegistration(valid_form):
    user = valid_form.save(commit=False)
    password = valid_form.cleaned_data['password']
    user.set_password(password)
    user.save()
    student = Student.objects.create(user=user)
    student.save()
    return student



@transaction.atomic 
def add_to_cart(student, section_id):
    course_by_section = CourseBySection.objects.select_for_update().get(course_code_by_section=section_id)

    if course_by_section.available_seats <= 0:
        raise ValidationError('All the seats are either taken or booked.')
    
    if Enrollment.objects.filter(student=student, course_by_section_id=section_id).exists():
        raise ValidationError('You are already enrolled in this course.')
    
    obj, created = VoucherItem.objects.get_or_create(
        student=student,
        course_by_section=course_by_section,
        fee_voucher=None
    )
    
    if not created:
        raise ValidationError('The course is already in the cart')
    
    return obj

     
def remove_course_from_cart(student, item_id:int ):
    voucher_item = get_object_or_404(VoucherItem, id=item_id, student=student)
    if voucher_item.fee_voucher is not None:
        raise Exception("Cannot remove an item that is already linked to a fee voucher")

    voucher_item.delete()



@transaction.atomic
def enroll_student(student, course_code_by_section):
    course_by_section = get_object_or_404(CourseBySection, course_code_by_section=course_code_by_section)
    semester = Semester.latest_semester()
    if not semester.can_add_course:
        raise ValidationError("Cannot enroll in this class at this time")
    
    if course_by_section.no_of_enrolled_students >= course_by_section.section.limit_of_students:
        raise ValidationError("No seats available for this class")
    
    
    obj, created = Enrollment.objects.get_or_create(course_by_section=course_by_section, semester=semester, student=student)

    if not created:
        raise ValidationError("You are already enrolled in this class")

    course_by_section.no_of_enrolled_students += 1
    course_by_section.save()

@transaction.atomic
def unenroll_student(enrollment_id):
    enrollment = get_object_or_404(Enrollment,id=enrollment_id)
    if not enrollment.semester.can_drop_course:
        raise ValidationError("Cannot drop this at this time") 
    
    enrollment.course_by_section.no_of_enrolled_students -= 1
    enrollment.save()
    enrollment.delete()