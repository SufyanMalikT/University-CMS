from django.utils import timezone
from django.db import transaction
from .models import VoucherItem, FeeVoucher, FeeConfiguration, Payment, Ledger
from ..academics.models import Semester, Enrollment
from django.shortcuts import get_object_or_404
from ..academics.services import enroll_student
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
    reg_fee = Decimal('0.00')
    if not getattr(student, 'is_registration_fee_paid', False):
        reg_fee = rates.get('registration', Decimal('200.00'))
    
    exam_fee = rates.get('exam_fee', Decimal('30.00'))
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
    # 1. Use select_for_update to lock the student record during the transaction
    voucher = get_object_or_404(FeeVoucher.objects.select_related('student'), id=voucher_id)
    
    if voucher.status == 'paid':
        print(f"Voucher {voucher_id} is already marked as paid.")
        return

    # 2. Extract amount (Stripe provides amount in cents)
    amount_paid = Decimal(session.get('amount_total')) / 100

    # 3. Update Balance & Voucher Status
    # We subtract the actual payment from the student's debt
    voucher.student.cached_balance -= amount_paid
    voucher.student.save()

    voucher.status = 'paid'
    voucher.save()

    # 4. Prevent Duplicate Payments
    if Payment.objects.filter(voucher=voucher).exists():
        print(f"Payment already exists for voucher {voucher_id}")
        return
    
    # 5. Record the Payment
    new_payment = Payment.objects.create(
        student=voucher.student,
        voucher=voucher,
        amount_paid=amount_paid,
        stripe_charge_id=session.get('payment_intent')
    )

    # 6. Update the students cached balance
    voucher.student.cached_balance -= new_payment.amount_paid
    voucher.student.save()

    # 7. Creating a ledger
    Ledger.objects.create(
        student=voucher.student,
        amount=-(amount_paid), # this is negative because we owe student the amount that they've paid until enrollment is done
        transaction_type='payment',
        payment_reference=new_payment
    )
    # 8. Finalize Enrollments
    # Ensure enroll_student logic handles successful enrollment
    for item in voucher.voucher_items.all():
        enroll_student(
            voucher.student, 
            item.course_by_section.course_code_by_section # Verify this field name!
        )