#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.models import User

def fix_admin_password():
    app = create_app('development')
    with app.app_context():
        admin = db.session.query(User).filter_by(email='admin@crimewatch.zw').first()
        if admin:
            # Reset password using the new Argon2id hashing
            admin.set_password("Admin1234!")
            admin.failed_login_count = 0
            admin.locked_until = None
            admin.totp_enabled = False
            db.session.commit()
            print("Admin password reset with new Argon2id hashing")
            print("Email: admin@crimewatch.zw")
            print("Password: Admin1234!")
            print("MFA: Disabled")
        else:
            print("Admin account not found")

if __name__ == "__main__":
    fix_admin_password()
