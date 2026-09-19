"""
Email Service for SMTP-based notifications and OTP delivery
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import random
import string
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    @property
    def smtp_server(self) -> str:
        return os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    
    @property
    def smtp_port(self) -> int:
        try:
            return int(os.getenv('SMTP_PORT', '587'))
        except (ValueError, TypeError):
            return 587
        
    @property
    def smtp_username(self) -> str:
        val = os.getenv('SMTP_USERNAME', '')
        return val.strip().strip('"').strip("'")
        
    @property
    def smtp_password(self) -> str:
        val = os.getenv('SMTP_PASSWORD', '')
        # Remove whitespace/spaces and surrounding quotes (e.g. Google 16-char App Passwords formatted as 4x4)
        return "".join(val.split()).strip('"').strip("'")
        
    @property
    def smtp_use_tls(self) -> bool:
        return os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
    @property
    def from_email(self) -> str:
        val = os.getenv('FROM_EMAIL')
        if val:
            val = val.strip().strip('"').strip("'")
        return val or self.smtp_username
        
    @property
    def from_name(self) -> str:
        return os.getenv('FROM_NAME', 'Smart Policing System').strip().strip('"').strip("'")
        
    def _get_smtp_connection(self):
        """Create and return SMTP connection with proper SSL / STARTTLS negotiation and timeout."""
        server = self.smtp_server
        port = self.smtp_port
        timeout = 15  # 15 seconds timeout to prevent worker hangs

        if port == 465:
            # Port 465 is direct SSL/TLS
            smtp = smtplib.SMTP_SSL(server, port, timeout=timeout)
        else:
            smtp = smtplib.SMTP(server, port, timeout=timeout)
            if self.smtp_use_tls:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
        
        if self.smtp_username and self.smtp_password:
            smtp.login(self.smtp_username, self.smtp_password)
        
        return smtp
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: Optional[str] = None) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body content
            text_content: Plain text fallback (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not to_email:
            logger.error("No recipient email provided")
            return False
            
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            with self._get_smtp_connection() as smtp:
                smtp.send_message(msg)
                logger.info(f"Email sent successfully to {to_email}")
                self.last_error = None
                return True
                
        except Exception as e:
            err_str = str(e)
            if "535" in err_str or "BadCredentials" in err_str or "Username and Password not accepted" in err_str:
                self.last_error = "Gmail SMTP rejected credentials (535 Bad Credentials). Ensure your Google App Password is valid and 2-Step Verification is enabled."
            else:
                self.last_error = err_str
            logger.error(f"Failed to send email to {to_email}: {err_str}")
            return False
    
    def send_otp_email(self, to_email: str, otp_code: str, user_name: str = "") -> bool:
        """
        Send OTP verification email.
        
        Args:
            to_email: Recipient email address
            otp_code: 6-digit OTP code
            user_name: User's name for personalization
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Your Verification Code - Smart Policing System"
        
        # Personalized greeting
        greeting = f"Dear {user_name}," if user_name else "Hello,"
        
        # HTML content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #0066cc; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 5px; }}
                .otp-code {{ 
                    font-size: 32px; 
                    font-weight: bold; 
                    color: #0066cc; 
                    text-align: center; 
                    padding: 20px; 
                    background-color: #e6f2ff; 
                    border-radius: 5px; 
                    margin: 20px 0;
                    letter-spacing: 5px;
                }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; text-align: center; }}
                .warning {{ color: #cc0000; font-size: 14px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Smart Policing System</h2>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Your verification code is:</p>
                    <div class="otp-code">{otp_code}</div>
                    <p>This code will expire in 10 minutes.</p>
                    <p class="warning">If you did not request this code, please ignore this email and contact support immediately.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from the Smart Policing System. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        text_content = f"""
{greeting}

Your verification code is: {otp_code}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email and contact support immediately.

---
Smart Policing System
"""
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(self.smtp_username and self.smtp_password)


# Global email service instance
email_service = EmailService()