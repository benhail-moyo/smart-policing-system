"""
OTP Service for generating and validating email-based one-time passwords
"""
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import logging

from app import db
from app.models.models import EmailOTP, User
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class OTPService:
    """Service for managing email-based OTP codes."""
    
    # OTP expiration time (10 minutes)
    OTP_EXPIRY_MINUTES = 10
    # OTP code length (6 digits)
    OTP_LENGTH = 6
    
    def generate_otp(self, user_id: int) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate and send OTP code for user.
        
        Args:
            user_id: User ID to generate OTP for
            
        Returns:
            Tuple of (success_message, error_message) - one will be None
        """
        try:
            user = db.session.get(User, user_id)
            if not user:
                return None, "User not found"
            
            if not user.email:
                return None, "User has no email address configured"
            
            # Check if email service is configured
            if not email_service.is_configured():
                logger.warning("Email service not configured, OTP generation skipped")
                return None, "Email service not configured"
            
            # Generate 6-digit numeric code
            otp_code = ''.join(random.choices(string.digits, k=self.OTP_LENGTH))
            
            # Calculate expiration time
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
            
            # Create OTP record
            otp = EmailOTP(
                user_id=user_id,
                code=otp_code,
                expires_at=expires_at,
                used=False
            )
            db.session.add(otp)
            
            # Clean up old unused OTPs for this user (keep only latest 5)
            self._cleanup_old_otps(user_id)
            
            db.session.commit()
            
            # Send email
            user_name = user.name or user.email.split('@')[0]
            email_sent = email_service.send_otp_email(user.email, otp_code, user_name)
            
            if not email_sent:
                err_detail = getattr(email_service, 'last_error', None) or "Failed to send OTP email"
                logger.warning(f"Failed to send OTP email to {user.email}. OTP: {otp_code}. Error: {err_detail}")
                return None, err_detail
            
            logger.info(f"OTP generated and sent to user {user_id} ({user.email})")
            return f"OTP sent to {user.email}", None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to generate OTP for user {user_id}: {str(e)}")
            return None, f"Failed to generate OTP: {str(e)}"
    
    def verify_otp(self, user_id: int, otp_code: str) -> Tuple[bool, Optional[str]]:
        """
        Verify OTP code for user.
        
        Args:
            user_id: User ID to verify OTP for
            otp_code: OTP code to verify
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Find the most recent valid OTP for this user
            otp = db.session.query(EmailOTP).filter(
                EmailOTP.user_id == user_id,
                EmailOTP.code == otp_code,
                EmailOTP.used == False
            ).order_by(EmailOTP.created_at.desc()).first()
            
            if not otp:
                return False, "Invalid OTP code"
            
            if not otp.is_valid():
                if otp.used:
                    return False, "OTP code already used"
                else:
                    return False, "OTP code expired"
            
            # Mark OTP as used
            otp.mark_as_used()
            db.session.commit()
            
            logger.info(f"OTP verified successfully for user {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to verify OTP for user {user_id}: {str(e)}")
            return False, f"Failed to verify OTP: {str(e)}"
    
    def _cleanup_old_otps(self, user_id: int):
        """Clean up old unused OTPs for a user, keeping only the latest 5."""
        try:
            # Get all unused OTPs for this user, ordered by creation time
            old_otps = db.session.query(EmailOTP).filter(
                EmailOTP.user_id == user_id,
                EmailOTP.used == False
            ).order_by(EmailOTP.created_at.desc()).offset(5).all()
            
            # Delete old OTPs
            for otp in old_otps:
                db.session.delete(otp)
                
        except Exception as e:
            logger.warning(f"Failed to cleanup old OTPs for user {user_id}: {str(e)}")
    
    def cleanup_expired_otps(self):
        """Clean up all expired OTPs in the database (maintenance task)."""
        try:
            expired_otps = db.session.query(EmailOTP).filter(
                EmailOTP.expires_at < datetime.now(timezone.utc)
            ).all()
            
            count = len(expired_otps)
            for otp in expired_otps:
                db.session.delete(otp)
            
            db.session.commit()
            logger.info(f"Cleaned up {count} expired OTPs")
            return count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cleanup expired OTPs: {str(e)}")
            return 0


# Global OTP service instance
otp_service = OTPService()