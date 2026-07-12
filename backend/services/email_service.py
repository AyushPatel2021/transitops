import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', 'noreply@enterprise.com')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Enterprise Metadata System')
        
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Send an email using SMTP"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.error("SMTP credentials not configured")
                return False
                
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str) -> bool:
        """Send password reset email"""
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        subject = "Reset Your Password - Enterprise Metadata System"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    
                    <p>We received a request to reset your password for your Enterprise Metadata System account.</p>
                    
                    <p>Click the button below to reset your password:</p>
                    
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #f0f0f0; padding: 10px; border-radius: 4px;">
                        {reset_url}
                    </p>
                    
                    <div class="warning">
                        <strong>Security Notice:</strong>
                        <ul>
                            <li>This link will expire in 1 hour for security reasons</li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>Never share this link with anyone</li>
                        </ul>
                    </div>
                    
                    <p>If you have any questions, please contact our support team.</p>
                    
                    <p>Best regards,<br>Enterprise Metadata System Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hello {user_name},
        
        We received a request to reset your password for your Enterprise Metadata System account.
        
        Please visit the following link to reset your password:
        {reset_url}
        
        This link will expire in 1 hour for security reasons.
        
        If you didn't request this reset, please ignore this email.
        
        Best regards,
        Enterprise Metadata System Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)

    def send_driver_license_expiry_email(
        self,
        to_email: str,
        driver_name: str,
        license_number: str,
        expiry_date: str,
        days_left: int,
    ) -> bool:
        """Send driver license expiry reminder email."""
        subject = "Driving License Expiry Reminder - TransitOps"
        status_line = (
            f"Your driving license expires in {days_left} day{'s' if days_left != 1 else ''}."
            if days_left >= 0
            else "Your driving license has expired."
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1f2937;">
            <div style="max-width: 600px; margin: 0 auto; padding: 24px;">
                <h2 style="margin: 0 0 16px;">Driving License Reminder</h2>
                <p>Hello {driver_name},</p>
                <p>{status_line}</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>License Number</strong></td>
                        <td style="padding: 8px; border: 1px solid #e5e7eb;">{license_number}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Expiry Date</strong></td>
                        <td style="padding: 8px; border: 1px solid #e5e7eb;">{expiry_date}</td>
                    </tr>
                </table>
                <p>Please renew the license and update TransitOps before dispatch assignment.</p>
                <p>TransitOps Team</p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Driving License Reminder

        Hello {driver_name},

        {status_line}

        License Number: {license_number}
        Expiry Date: {expiry_date}

        Please renew the license and update TransitOps before dispatch assignment.

        TransitOps Team
        """

        return self.send_email(to_email, subject, html_content, text_content)

# Global instance
email_service = EmailService()
