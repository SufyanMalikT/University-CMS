from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from ..academics.permissions import student_only
from django.contrib.auth.decorators import login_required
from .models import FeeVoucher
from django.utils import timezone
from .utils.FeeVoucher import render_to_pdf
from .services import delete_unpaid_fee_voucher
import stripe
from django.contrib import messages
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
    student = request.user.student_profile
    voucher = get_object_or_404(FeeVoucher, id=voucher_id, student=student)

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"University Fee Voucher #{voucher.id}",
                    'description': f"Semester: {voucher.semester.get_sem}",
                },
                'unit_amount': int(voucher.amount), # Already in cents
            },
            'quantity': 1,
        }],
        mode='payment',
        # Crucial: Metadata allows us to find the voucher later in the webhook
        metadata={
            "voucher_id": voucher.id
        },
        success_url=request.build_absolute_uri('payment/success/'),
        cancel_url=request.build_absolute_uri('/cart/'),
    )

    return redirect(checkout_session.url, code=303)


def success_payment_page_view(request):
    messages.success(request, "Payment Successful")
    return redirect('cart')

