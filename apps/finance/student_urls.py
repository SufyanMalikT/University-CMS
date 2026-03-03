from django.urls import path
from .webhooks import stripe_webhook
from .views import download_fee_voucher, view_fee_voucher, delete_unpaid_voucher_view, create_checkout_session, success_payment_page_view
urlpatterns = [
    path('dashboard/download_fee_voucher/<int:voucher_id>',download_fee_voucher, name='download_fee_voucher'),
    path('dashboard/view_fee_voucher/<int:voucher_id>',view_fee_voucher, name='view_fee_voucher'),
    path('dashboard/delete_unpaid_fee_voucher/<int:voucher_id>',delete_unpaid_voucher_view, name='delete_unpaid_fee_voucher'),
    path('dashboard/voucher/pay/<int:voucher_id>',create_checkout_session, name='pay_voucher'),
    path('stripe/webhook/',stripe_webhook, name='stripe_webhook'),
    path('dashboard/voucher/pay/payment/success/', success_payment_page_view, name='payment_successful'),
]