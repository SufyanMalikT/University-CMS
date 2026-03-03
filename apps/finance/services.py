from django.utils import timezone
from django.db import transaction
from .models import VoucherItem, FeeVoucher, FeeConfiguration, Payment
from ..academics.models import Semester
from django.shortcuts import get_object_or_404
from ..academics.services import enroll_student

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

@transaction.atomic 
def fulfill_order(session, voucher_id):
    voucher = get_object_or_404(FeeVoucher,id=voucher_id)
    voucher.status = 'paid'
    voucher.save()

    payment = Payment.objects.filter(voucher= voucher_id)

    if payment.exists():
        print(f"Payment already exists for voucher {voucher_id}")
        return
    
    new_payment = Payment.objects.create(
        student=voucher.student,
        voucher=voucher,
        amount_paid=session.get('amount_total') / 100,
        stripe_charge_id = session.get('payment_intent')
    )

    voucher_items = voucher.voucher_items.all()

    for voucher_item in voucher_items:
        enroll_student(voucher.student, voucher_item.course_by_section.course_code_by_section)