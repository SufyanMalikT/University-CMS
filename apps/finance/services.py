from django.utils import timezone
from django.db import transaction
from .models import VoucherItem, FeeVoucher, FeeConfiguration, Payment, Ledger
from ..academics.models import Semester, Enrollment
from django.shortcuts import get_object_or_404
from ..academics.services.student_services import enroll_student
from decimal import Decimal

def calculate_cart_total(student):
    # 1. Fetch current rates from FeeConfiguration (using Decimal for money!)
    rates = {fc.name: fc.amount for fc in FeeConfiguration.objects.all()}

    # 2. Get unvouchered items
    voucher_items = VoucherItem.objects.filter(student=student, fee_voucher=None).select_related(
        'course_by_section__course', 'course_by_section__section'
    )

    # 3. Handle the Cached Balance
    # In our Ledger logic: Positive = Owed, Negative = Credit (Carry Forward)
    current_balance = student.cached_balance or Decimal('0.00')

    # 4. Define fee rates with fallbacks
    credit_rate = rates.get('per_credit', Decimal('100.00'))
    exam_fee_per_course = rates.get('exam_fee', Decimal('30.00'))
    reg_fee = Decimal('0.00')
    if not getattr(student, 'is_registration_fee_paid', False):
        reg_fee = rates.get('registration', Decimal('200.00'))
    
    lib_fee = Decimal('0.00')
    if not is_student_lib_fee_paid_current_sem(student):
        lib_fee = rates.get('library_fee', Decimal('50.00'))
        

    total_course_fees = Decimal('0.00')
    items_breakdown = []
    total_credits = 0

    # 5. Calculate course fees
    for item in voucher_items:
        course = item.course_by_section.course
        item_fee = course.credit_hours * credit_rate
        total_course_fees += item_fee
        total_credits += course.credit_hours

        items_breakdown.append({
            'item_id': item.id,
            'course_name': course.name,
            'course_code': course.course_code,
            'course_code_by_section': item.course_by_section.course_code_by_section,
            'section': str(item.course_by_section.section),
            'type': course.course_type,
            'credits': course.credit_hours,
            'fee': float(item_fee)
        })
    exam_fee = exam_fee_per_course*len(items_breakdown)


    # 6. Final Calculation
    # New Bill = (Courses + Reg + Exam + Library)
    current_bill = total_course_fees + reg_fee + exam_fee + lib_fee
    
    # Grand Total = Current Bill + Old Balance
    # If balance is -500, it reduces the bill. If +200, it increases it.
    grand_total = current_bill + current_balance

    # Stripe cannot charge < 0. If they have massive credit, they pay $0.
    final_payable = max(Decimal('0.00'), grand_total)

    # 7. Return structured data
    return {
        'items': items_breakdown,
        'fixed_fees': {
            'registration': float(reg_fee),
            'exam_fee': float(exam_fee),
            'library_fee': float(lib_fee),
        },
        'total_credits': total_credits,
        'total_course_fees': float(total_course_fees),
        'current_bill_subtotal': float(current_bill),
        'existing_balance_adjustment': float(current_balance), # Shows credit as negative
        'grand_total': float(final_payable) 
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
        amount=int(cart_total['grand_total']), # as we are storing amounts in dollars in the db we will need to convert it into cents before passing it to stripe
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
    voucher = get_object_or_404(FeeVoucher.objects.select_related('student'), id=voucher_id)
    
    if voucher.status == 'paid':
        return

    amount_total = Decimal(session.get('amount_total')) / 100

    voucher.status = 'paid'
    voucher.save()

    # 1. Record the Master Payment Record
    new_payment = Payment.objects.create(
        student=voucher.student,
        voucher=voucher,
        amount_paid=amount_total,
        stripe_charge_id=session.get('payment_intent')
    )

    # 2. SPLIT THE LEDGER (The key to your question)
    
    # Bucket A: Registration & Library (Service Charges)
    fixed_fees = voucher.breakdown.get('fixed_fees', {})
    reg_fee = Decimal(fixed_fees.get('registration', 0))
    lib_fee = Decimal(fixed_fees.get('library_fee', 0))
    total_service_charges = reg_fee + lib_fee

    if total_service_charges > 0:
        Ledger.objects.create(
            student=voucher.student,
            amount=-total_service_charges, # Negative because it clears the debt
            transaction_type='service',    # This separates it from tuition!
            description=f"Registration & Library Fees (Voucher #{voucher.id})",
            payment_reference=new_payment
        )

    # Bucket B: Course/Tuition Fees
    course_fees = Decimal(voucher.breakdown.get('total_course_fees', 0))
    exam_fee = Decimal(fixed_fees.get('exam_fee', 0))
    total_tuition_related = course_fees + exam_fee

    if total_tuition_related > 0:
        Ledger.objects.create(
            student=voucher.student,
            amount=-total_tuition_related, # Negative because it clears the debt
            transaction_type='tuition',    # Standard tuition bucket
            description=f"Course Tuition & Exam Fees (Voucher #{voucher.id})",
            payment_reference=new_payment
        )

    # 3. Update Student Debt (The big picture)
    # If positive = debt, we subtract the payment to reduce the debt.
    voucher.student.cached_balance -= total_tuition_related
    voucher.student.save()

    # 4. Finalize Enrollments
    for item in voucher.voucher_items.all():
        enroll_student(voucher.student, item.course_by_section.course_code_by_section)

def is_student_lib_fee_paid_current_sem(student):
    paid_vouchers = student.fee_vouchers.filter(status='paid',semester=Semester.latest_semester())
    if paid_vouchers.exists():
        for voucher in paid_vouchers:
            if voucher.breakdown['fixed_fees']['library_fee'] > 0:
                return True
    return False