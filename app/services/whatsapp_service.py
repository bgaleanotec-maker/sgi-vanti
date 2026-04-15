import requests
from app.config import get_service_config


def send_whatsapp(to_number, message_body):
    """Send WhatsApp message via UltraMsg using DB/env config."""
    try:
        instance_id = get_service_config('ultramsg', 'instance_id')
        token = get_service_config('ultramsg', 'token')

        if not instance_id or not token:
            print("UltraMsg not configured. Skipping WhatsApp.")
            return False

        to_number = to_number.replace('+', '').replace(' ', '')

        url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
        payload = {"token": token, "to": to_number, "body": message_body}
        headers = {'content-type': 'application/x-www-form-urlencoded'}

        response = requests.post(url, data=payload, headers=headers)
        print(f"UltraMsg response: {response.text}")

        if response.status_code == 200 and 'sent' in response.text:
            return True
        return False
    except Exception as e:
        print(f"Error sending WhatsApp: {e}")
        return False
