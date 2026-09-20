#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.models import User

def check_admin():
    app = create_app('development')
    with app.app_context():
        admin = User.query.filter_by(email='admin@crimewatch.zw').first()
        if admin:
            print(f"Admin exists: True")
            print(f"Email: {admin.email}")
            print(f"Role: {admin.role}")
            print(f"Password hash: {admin.password_hash[:50]}...")
            print(f"TOTP enabled: {admin.totp_enabled}")
            print(f"Failed login count: {admin.failed_login_count}")
            print(f"Locked until: {admin.locked_until}")
        else:
            print("Admin does not exist")

if __name__ == "__main__":
    check_admin()
