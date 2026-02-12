"""
Africa's Talking SMS and WhatsApp integration.
Handles sending reminders via Africa's Talking API.
"""
import requests
import logging
from decouple import config
from django.conf import settings

logger = logging.getLogger(__name__)


class AfricasTalkingGateway:
    """
    Integration with Africa's Talking API for SMS and WhatsApp messaging.
    
    Documentation: https://africastalking.com/
    """
    
    def __init__(self):
        self.api_key = config('AFRICA_TALKING_API_KEY', default='')
        self.username = config('AFRICA_TALKING_USERNAME', default='')
        self.base_url = 'https://api.sandbox.africastalking.com'  # Use production URL in settings
        self.sms_url = f'{self.base_url}/version1/messaging'
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'apiKey': self.api_key,
        }
    
    def is_configured(self):
        """Check if API credentials are configured."""
        return bool(self.api_key and self.username)
    
    def send_sms(self, phone_number, message, sender_id='DawaTrack'):
        """
        Send SMS message via Africa's Talking API.
        
        Args:
            phone_number: Recipient phone number (international format)
            message: SMS message content
            sender_id: Sender ID/name
        
        Returns:
            dict: {
                'success': bool,
                'message_id': str (if successful),
                'error': str (if failed),
                'status': str
            }
        """
        if not self.is_configured():
            logger.warning("Africa's Talking not configured")
            return {
                'success': False,
                'error': 'Africa\'s Talking credentials not configured',
                'status': 'FAILED'
            }
        
        try:
            payload = {
                'username': self.username,
                'to': phone_number,
                'message': message,
                'from': sender_id,
            }
            
            response = requests.post(
                self.sms_url,
                headers=self.headers,
                data=payload,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Check SMS responses
            if 'SMSMessageData' in data:
                sms_data = data['SMSMessageData']
                if sms_data.get('Recipients'):
                    recipient = sms_data['Recipients'][0]
                    if recipient.get('statusCode') == 101:
                        return {
                            'success': True,
                            'message_id': recipient.get('messageId'),
                            'status': 'SENT',
                        }
                    else:
                        return {
                            'success': False,
                            'error': recipient.get('statusMessage', 'Unknown error'),
                            'status': 'FAILED',
                        }
            
            return {
                'success': False,
                'error': 'Invalid response from API',
                'status': 'FAILED',
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"SMS sending failed for {phone_number}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status': 'FAILED',
            }
    
    def send_whatsapp(self, phone_number, message, media_url=None):
        """
        Send WhatsApp message via Africa's Talking API.
        
        Args:
            phone_number: Recipient phone number (international format)
            message: WhatsApp message content
            media_url: Optional media URL to attach
        
        Returns:
            dict: Response with success status and message ID
        """
        if not self.is_configured():
            logger.warning("Africa's Talking not configured")
            return {
                'success': False,
                'error': 'Africa\'s Talking credentials not configured',
                'status': 'FAILED'
            }
        
        try:
            whatsapp_url = f'{self.base_url}/version1/messaging'
            
            payload = {
                'username': self.username,
                'to': phone_number,
                'message': message,
            }
            
            if media_url:
                payload['media_url'] = media_url
            
            response = requests.post(
                whatsapp_url,
                headers=self.headers,
                data=payload,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if 'SMSMessageData' in data:
                sms_data = data['SMSMessageData']
                if sms_data.get('Recipients'):
                    recipient = sms_data['Recipients'][0]
                    if recipient.get('statusCode') == 101:
                        return {
                            'success': True,
                            'message_id': recipient.get('messageId'),
                            'status': 'SENT',
                        }
            
            return {
                'success': False,
                'error': 'Failed to send WhatsApp message',
                'status': 'FAILED',
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"WhatsApp sending failed for {phone_number}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status': 'FAILED',
            }
    
    def send_bulk_sms(self, phone_numbers, message, sender_id='DawaTrack'):
        """
        Send SMS to multiple recipients.
        
        Args:
            phone_numbers: List of phone numbers
            message: SMS message content
            sender_id: Sender ID
        
        Returns:
            list: List of response dicts for each recipient
        """
        results = []
        for phone in phone_numbers:
            result = self.send_sms(phone, message, sender_id)
            results.append({
                'phone_number': phone,
                'result': result
            })
        return results
    
    def parse_webhook_response(self, data):
        """
        Parse webhook response from Africa's Talking for delivery confirmations.
        
        Args:
            data: Webhook payload data
        
        Returns:
            dict: Parsed delivery information
        """
        return {
            'message_id': data.get('id'),
            'status': data.get('status'),
            'phone_number': data.get('phone'),
            'timestamp': data.get('timestamp'),
            'failure_reason': data.get('failureReason'),
        }


# Initialize gateway
gateway = AfricasTalkingGateway()
