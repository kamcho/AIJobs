import requests
import base64
from datetime import datetime
from django.conf import settings
from .models import MpesaTransaction

class MpesaService:
    @staticmethod
    def get_access_token():
        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        if settings.MPESA_ENVIRONMENT == 'production':
            url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
            
        auth_str = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {"Authorization": f"Basic {encoded_auth}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('access_token')
        except Exception as e:
            print(f"Error getting M-Pesa access token: {str(e)}")
            return None

    @staticmethod
    def initiate_stk_push(user, phone_number, amount, subscription_tier):
        access_token = MpesaService.get_access_token()
        if not access_token:
            return False, "Failed to authenticate with M-Pesa"

        # Format phone number to 254XXXXXXXXX
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
            
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        
        url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        if settings.MPESA_ENVIRONMENT == 'production':
            url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        
        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": 1,
            "PartyA": phone_number,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": f"FindAJob-{subscription_tier}",
            'TransactionDesc': 'JobMatch Subscription'
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            res_json = response.json()
            
            if response.status_code == 200 and res_json.get('ResponseCode') == '0':
                # Save transaction record
                MpesaTransaction.objects.create(
                    user=user,
                    phone_number=phone_number,
                    amount=amount,
                    checkout_request_id=res_json.get('CheckoutRequestID'),
                    merchant_request_id=res_json.get('MerchantRequestID'),
                    subscription_tier=subscription_tier,
                    status='Pending'
                )
                return True, "STK Push initiated successfully. Please check your phone."
            else:
                return False, res_json.get('ResponseDescription', 'STK Push failed')
        except Exception as e:
            return False, f"Error initiating STK Push: {str(e)}"
