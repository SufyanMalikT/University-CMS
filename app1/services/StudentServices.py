from django.db import transaction
from app1.forms import StudentRegistrationForm
from app1.models import Student, CourseBySection, Semester, Enrollment, VoucherItem, FeeConfiguration, FeeVoucher
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
    # 1. Fetch current rates from FeeConfiguration
    rates = {fc.name: fc.amount for fc in FeeConfiguration.objects.all()}

    # 2. Get the items currently in the student's cart (unvouchered)
    voucher_items = VoucherItem.objects.filter(student=student, fee_voucher=None)

    # 3. Define the fee rates with fallbacks
    credit_fee = rates.get('per_credit', 100.00)
    sem_registration_fee = rates.get('registration', 200.00)
    exam_fee = rates.get('exam_fee', 30.00)
    library_charges = rates.get('library_fee', 50.00)

    total_course_fees = 0
    breakdown = []
    total_credits = 0
    # 4. Loop through courses and calculate based on credit hours
    for voucher_item in voucher_items:
        course = voucher_item.course_by_section.course
        
        # Whether it's Theory (e.g., 3 credits) or Lab (1 credit), 
        # the fee is simply credits * credit_fee
        item_fee = course.credit_hours * credit_fee
        total_course_fees += item_fee
        total_credits += course.credit_hours

        breakdown.append({
            'item_id':voucher_item.id,
            'course_name': course.name,
            'course_code': course.course_code,
            'section':str(voucher_item.course_by_section.section),
            'type': course.course_type,
            'credits': course.credit_hours,
            'fee': float(item_fee)
        })

    # 5. Add fixed administrative fees
    fixed_fees_sum = sem_registration_fee + exam_fee + library_charges
    grand_total = total_course_fees + fixed_fees_sum

    # 6. Return structured data for the UI and the FeeVoucher JSONField
    return {
        'items': breakdown,
        'fixed_fees': {
            'registration': float(sem_registration_fee),
            'exam_fee': float(exam_fee),
            'library_fee': float(library_charges),
        },
        'total_credits':total_credits,
        'total_course_fees': float(total_course_fees),
        'grand_total': float(grand_total)
    }

        
def remove_course_from_cart(student, item_id:int ):
    voucher_item = get_object_or_404(VoucherItem, id=item_id, student=student)
    if voucher_item.fee_voucher is not None:
        raise Exception("Cannot remove an item that is already linked to a fee voucher")

    voucher_item.delete()

def calculate_voucher_due_date(semester):
    today = timezone.now().date()

    standard_expiry = today + timezone.timedelta(days=semester.voucher_validity_days)

    absolute_deadline = semester.fee_payment_deadline 

    if absolute_deadline:
        return min(standard_expiry, absolute_deadline)
    return standard_expiry


@transaction.atomic
def generate_fee_voucher(student):
    voucher_items = VoucherItem.objects.filter(student=student, fee_voucher=None)

    if not voucher_items.exists():
        raise Exception("No items in the cart for fee voucher generation")
    
    semester = Semester.latest_semester()
    if semester.is_past_deadline:
        raise Exception("Fee payment due date is passed")
    
    cart_total = calculate_cart_total(student)
    voucher = FeeVoucher.objects.create(
        student=student,
        amount=int(cart_total['grand_total']*100), # as we are storing amounts in cents in the db recommended for stripe
        breakdown=cart_total,
        semester=semester,
        due_date=calculate_voucher_due_date(semester),
    )

    voucher_items.update(fee_voucher=voucher)

    return voucher
        

@transaction.atomic 
def delete_unpaid_fee_voucher(student, voucher_id):
    unpaid_voucher = get_object_or_404(FeeVoucher, student=student, id=voucher_id, status='unpaid')
    unpaid_voucher.delete()