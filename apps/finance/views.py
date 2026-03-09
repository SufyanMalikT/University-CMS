from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from ..academics.permissions import student_only
from django.contrib.auth.decorators import login_required
from .models import FeeVoucher, Payment
from django.utils import timezone
from .utils.FeeVoucher import render_to_pdf
from .services import delete_unpaid_fee_voucher, fulfill_order, calculate_cart_total
import stripe
from django.contrib import messages
from django.db import transaction
from ..academics.services import enroll_student
from django.urls import reverse
# Create your views here.

@student_only
@login_required
def download_fee_voucher(request, voucher_id):
    # Security: Ensure the student can only download their own voucher
    voucher = get_object_or_404(FeeVoucher, id=voucher_id, student=request.user.student_profile)
    context = {
        'voucher': voucher,
        'breakdown': voucher.breakdown, # This is your JSON dictionary
        'today': timezone.now(),
    }
    
    pdf = render_to_pdf('pdfs/voucher_template.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Voucher_{voucher.id}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Error generating PDF", status=400)

@student_only
@login_required
def view_fee_voucher(request, voucher_id):
    fee_voucher = get_object_or_404(FeeVoucher, student=request.user.student_profile, id=voucher_id, status='unpaid')

    context_dict = {
        'voucher':fee_voucher,
        'breakdown':fee_voucher.breakdown,
        'today':timezone.now()
    }
    pdf = render_to_pdf('pdfs/voucher_template.html', context_dict)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Voucher_{voucher_id}.pdf"
        content = f"inline; filename={filename}"
        response['content-disposition'] = content
        return response
    return HttpResponse("Cant see the pdf right now...",status=400)

@login_required
def delete_unpaid_voucher_view(request, voucher_id):
    try:
        delete_unpaid_fee_voucher(request.user.student_profile, voucher_id)
        messages.success(request,'The voucher has been deleted you can restart your cart now...')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('cart')

@student_only
@login_required
def create_checkout_session(request, voucher_id):
    voucher = get_object_or_404(FeeVoucher, id=voucher_id)
    
    # Ensure we use the same amount logic for both paths
    # Using voucher.amount as the source of truth here
    amount_in_cents = int(voucher.amount * 100) 

    # PATH A: Zero-Dollar Settlement (Credits/Scholarships covered it)
    if amount_in_cents == 0:
        with transaction.atomic():
            # Create tracking record
            Payment.objects.create(
                student=request.user.student_profile,
                voucher=voucher,
                amount_paid=0,
                stripe_charge_id="INTERNAL_SETTLEMENT",
                status='Success'
            )
            
            # Enrollment Logic (Keep this consistent with your webhook!)
            for item in voucher.breakdown.get('items', []):
                enroll_student(voucher.student, item['course_code_by_section'])
            
            voucher.status = 'paid'
            voucher.save()
            
            return redirect('payment_success_page')

    # PATH B: Stripe Checkout
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"University Fee Voucher #{voucher.id}",
                        'description': f"Semester: {voucher.semester.get_sem}",
                    },
                    'unit_amount': amount_in_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            metadata={
                "voucher_id": voucher.id,
                "user_id": request.user.id # Helpful for debugging webhooks
            },
            # Using reverse() ensures your URLs don't break if you rename them
            success_url=request.build_absolute_uri(reverse('payment_success_page')),
            cancel_url=request.build_absolute_uri(reverse('cart_view')),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        # Log the error and tell the user something went wrong
        return render(request, 'error.html', {'message': str(e)})


@login_required
@student_only
def success_payment_page_view(request):
    messages.success(request, "Payment Successful")
    return redirect('cart')

@login_required
@student_only
def fee_voucher_view(request):
    prev_vouchers = request.user.student_profile.fee_vouchers.all().order_by('-created_at')
    return render(request, 'FeeVouchers.html',{'vouchers':prev_vouchers})

@login_required
@student_only
def download_voucher_receipt(request, voucher_id):
    voucher = get_object_or_404(FeeVoucher, id=voucher_id)
    
    if voucher.status != 'paid':
        messages.error(request, "Can't generate the receipt for the voucher that is not paid yet")
        return redirect('voucher_history')
    
    context = {
        'voucher':voucher,
        'today':timezone.now()
    }

    pdf = render_to_pdf('pdfs/receipt_template.html' , context)

    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"{voucher_id}_PAID_RECEIPT"
        content = f"inline; filename={filename}"
        response['content-disposition'] = content 
        return response
    return HttpResponse("Receipt Generation Failed",status=400)    
