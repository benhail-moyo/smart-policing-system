#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.models import User

def reset_admin():
    app = create_app('development')
    with app.app_context():
        admin = db.session.query(User).filter_by(email='admin@crimewatch.zw').first()
        if admin:
            admin.failed_login_count = 0
            admin.locked_until = None
            admin.totp_enabled = False
            db.session.commit()
            print("Admin account reset successfully")
            print("Email: admin@crimewatch.zw")
            print("Password: Admin1234!")
            print("MFA: Disabled")
        else:
            print("Admin account not found")

if __name__ == "__main__":
    reset_admin()
