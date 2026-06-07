"""
SendGrid Email Service
Sends emails via SendGrid API
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class SendGridEmailService:
    def __init__(self):
        self.api_key = os.environ.get("SENDGRID_API_KEY")
        self.from_email = os.environ.get("COMPANY_EMAIL", "noreply@company.com")
        
        if not self.api_key:
            print("⚠️  SENDGRID_API_KEY not set in environment")
            self.client = None
        else:
            self.client = SendGridAPIClient(self.api_key)
            print("✅ SendGrid client initialised")

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None
    ) -> bool:
        """
        Send email via SendGrid
        
        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            html_content: HTML body
            plain_text: Plain text fallback
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.client:
            print(f"SendGrid not configured, skipping email to {to_email}")
            return False
        
        try:
            message = Mail(
                from_email=Email(self.from_email, "HRMS"),
                to_emails=To(to_email, to_name),
                subject=subject,
                plain_text_content=plain_text or "Please view this email in HTML format",
                html_content=HtmlContent(html_content)
            )
            
            response = self.client.send(message)
            print(f"✅ Email sent to {to_email} (Status: {response.status_code})")
            return response.status_code in [200, 202]
        
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
#  EMAIL TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════

def get_interview_invite_template(
    candidate_name: str,
    job_title: str,
    company_name: str = "Our Company"
) -> str:
    """HTML template for interview invite email"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
            .greeting {{ font-size: 18px; font-weight: bold; margin-bottom: 20px; }}
            .highlight {{ background: #e8f4f8; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
            .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Congratulations!</h1>
            </div>
            
            <div class="content">
                <div class="greeting">Hi {candidate_name},</div>
                
                <p>We are excited to inform you that you have been selected to move forward in our hiring process for the <strong>{job_title}</strong> position at {company_name}!</p>
                
                <div class="highlight">
                    <strong>Next Step: Interview</strong><br>
                    Our team will contact you shortly to schedule your interview. Please keep an eye on your inbox for further details.
                </div>
                
                <p><strong>What to expect:</strong></p>
                <ul>
                    <li>Interview scheduling email with date and time</li>
                    <li>Interview format and duration details</li>
                    <li>List of topics we'll discuss</li>
                    <li>Meeting link or location information</li>
                </ul>
                
                <p>If you have any questions in the meantime, please don't hesitate to reach out to our HR team.</p>
                
                <p>Best regards,<br>
                <strong>The {company_name} HR Team</strong></p>
            </div>
            
            <div class="footer">
                <p>This is an automated email. Please do not reply directly to this message.</p>
                <p>&copy; {company_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_hired_template(
    candidate_name: str,
    job_title: str,
    company_name: str = "Our Company",
    joining_date: str = "to be confirmed"
) -> str:
    """HTML template for job offer/hired email"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 30px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
            .greeting {{ font-size: 18px; font-weight: bold; margin-bottom: 20px; }}
            .highlight {{ background: #e8f8f5; padding: 15px; border-left: 4px solid #11998e; margin: 20px 0; }}
            .offer-details {{ background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .detail-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
            .detail-label {{ font-weight: bold; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
            .btn {{ display: inline-block; background: #11998e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎊 Welcome Aboard!</h1>
            </div>
            
            <div class="content">
                <div class="greeting">Hi {candidate_name},</div>
                
                <p>We are thrilled to offer you the position of <strong>{job_title}</strong> at {company_name}!</p>
                
                <div class="highlight">
                    <strong>🎉 Job Offer Details</strong>
                </div>
                
                <div class="offer-details">
                    <div class="detail-row">
                        <span class="detail-label">Position:</span>
                        <span>{job_title}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Company:</span>
                        <span>{company_name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Expected Joining Date:</span>
                        <span>{joining_date}</span>
                    </div>
                </div>
                
                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>Our HR team will send you the formal offer letter</li>
                    <li>You will need to review and sign the offer letter</li>
                    <li>We will guide you through the onboarding process</li>
                    <li>Orientation details will be shared separately</li>
                </ul>
                
                <p>We look forward to working with you and believe you'll be a great addition to our team!</p>
                
                <p>If you have any questions about the offer or onboarding process, please reach out to our HR team.</p>
                
                <p>Best regards,<br>
                <strong>The {company_name} HR Team</strong></p>
            </div>
            
            <div class="footer">
                <p>This is an automated email. Please do not reply directly to this message.</p>
                <p>&copy; {company_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """