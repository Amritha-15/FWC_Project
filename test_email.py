import os
from backend.services.sendgrid_email_service import SendGridEmailService

if __name__ == '__main__':
    es = SendGridEmailService()
    to = os.getenv('SMTP_FROM', 'test@example.com')
    subject = 'Test Email from HRMS'
    html = '<p>This is a test email to verify SMTP configuration.</p>'
    es.send_simple(to, subject, html, html=True)
