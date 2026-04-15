from app.config import get_service_config


def send_email(to_email, subject, html_content):
    """Send email via SendGrid using DB/env config."""
    try:
        api_key = get_service_config('sendgrid', 'api_key')
        from_addr = get_service_config('sendgrid', 'from_email')

        if not api_key or not from_addr:
            print("SendGrid not configured. Skipping email.")
            return False

        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        sg = SendGridAPIClient(api_key)
        mail = Mail(Email(from_addr), To(to_email), subject, Content("text/html", html_content))
        response = sg.client.mail.send.post(request_body=mail.get())
        print(f"Email sent to {to_email}. Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
