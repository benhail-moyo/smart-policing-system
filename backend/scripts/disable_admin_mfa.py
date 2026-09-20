#!/usr/bin/env python3
"""
Disable MFA for admin account to allow login.
Run: python backend/scripts/disable_admin_mfa.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.models import User

def disable_admin_mfa():
    app = create_app('development')
    with app.app_context():
        admin = db.session.query(User).filter_by(email='admin@crimewatch.zw').first()
        if admin:
            admin.totp_enabled = False
            admin.failed_login_count = 0
            admin.locked_until = None
            db.session.commit()
            print("MFA disabled for admin account")
            print("You can now login with:")
            print("Email: admin@crimewatch.zw")
            print("Password: Admin1234!")
        else:
            print("Admin account not found")

if __name__ == "__main__":
    disable_admin_mfa()
