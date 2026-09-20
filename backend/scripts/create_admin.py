#!/usr/bin/env python3
"""
Create a new admin account with MFA enabled.
Run: python backend/scripts/create_admin.py
"""
import sys
import os
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.models import User
from app.security.totp import generate_totp_secret, get_provisioning_qr_base64

def create_admin_account():
    app = create_app('development')
    with app.app_context():
        # Admin credentials
        email = "admin@crimewatch.zw"
        password = "Admin1234!"
        name = "System Administrator"

        # Check if admin already exists
        existing = db.session.query(User).filter_by(email=email).first()
        if existing:
            print(f"Admin with email {email} already exists")
            print(f"Updating password and MFA for existing admin...")
            admin = existing
        else:
            print(f"Creating new admin account with email {email}")
            admin = User(
                email=email,
                role="admin",
                name=name
            )
            db.session.add(admin)

        # Set password using Argon2id
        admin.set_password(password)

        # Generate TOTP secret for mandatory MFA
        totp_secret = generate_totp_secret()
        admin.totp_secret = totp_secret
        admin.totp_enabled = True  # Admins must have MFA enabled

        # Reset lockout counters
        admin.failed_login_count = 0
        admin.locked_until = None

        db.session.commit()

        # Generate QR code for easy setup
        qr_base64 = get_provisioning_qr_base64(totp_secret, email, "Crime-Watch")

        print(f"\n{'='*60}")
        print(f"ADMIN ACCOUNT CREATED SUCCESSFULLY")
        print(f"{'='*60}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Role: admin")
        print(f"MFA: Enabled (mandatory for admins)")
        print(f"\nIMPORTANT: Set up your authenticator app with this TOTP secret:")
        print(f"  {totp_secret}")
        print(f"\nQR Code Data (base64): {qr_base64[:50]}...")
        print(f"\nYou will need to complete MFA setup before logging in.")
        print(f"{'='*60}")

if __name__ == "__main__":
    create_admin_account()
