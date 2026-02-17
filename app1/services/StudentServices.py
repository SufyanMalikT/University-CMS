from django.db import transaction
from app1.forms import StudentRegistrationForm
from app1.models import Student, CourseBySection, Semester, Enrollment, VoucherItem, FeeConfiguration
from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.db.models import Sum
from django.core.exceptions import ValidationError
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


def calculate_cart_total(student):
    rates = {fc.name: fc.amount for fc in FeeConfiguration.objects.all()}

    voucher_items = VoucherItem.objects.filter(student=student, fee_voucher=None)

    credit_fee = rates.get('per_credit',100.00)
    sem_registration_fee = rates.get('registration',200.00)
    exam_fee = rates.get('exam_fee',30.00)
    library_charges = rates.get('library_fee',50.00)

    total_tuition = 0
    lab_total = 0
    breakdown = []

    for voucher_item in voucher_items:
        if voucher_item.course_by_section.course.course_type == 'theory':
            total_tuition += voucher_item.course_by_section.course.credit_hours*credit_fee
        else:
            lab_total += voucher_item.course_by_section.course.credit_hours*credit_fee

        