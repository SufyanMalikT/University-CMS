import stripe 
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .services import fulfill_order

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None 

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_KEY
        )
        
    except ValueError:
        print("Value Error")
        return HttpResponse(status=400) # invalid payload 
    except stripe.error.SignatureVerificationError:
        print("Signature Error")
        return HttpResponse(status=400) # invalid signature
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print("checkout completed")
        voucher_id = session.get('metadata',{}).get('voucher_id')

        if voucher_id:
            print("Payment done: "+ voucher_id)
            fulfill_order(session, voucher_id)

    return HttpResponse(status=200)