import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.models import User, RefreshToken, EmailOTP, AuditLog, Incident, Deployment, StrategicPlan, OfficerDailyLog
from app.security.passwords import verify_password

def reset_and_create(app_instance, label=''):
    with app_instance.app_context():
        uri = app_instance.config.get('SQLALCHEMY_DATABASE_URI', '')
        print(f'=== Resetting users in {label} ({uri}) ===')
        try:
            db.create_all()
            
            # Clean related user foreign keys
            db.session.query(EmailOTP).delete()
            db.session.query(RefreshToken).delete()
            db.session.query(OfficerDailyLog).delete()
            db.session.query(Deployment).delete()
            db.session.query(StrategicPlan).delete()
            db.session.query(Incident).update({'reported_by_id': None, 'override_by_id': None})
            db.session.query(AuditLog).update({'user_id': None, 'override_by_id': None})
            
            # Delete all existing users
            deleted = db.session.query(User).delete()
            print(f'Deleted {deleted} existing users.')
            
            # Create new admin
            admin = User(
                email='benhailmoyo7@gmail.com',
                force_number='123456X',
                officer_id='123456X',
                role='admin',
                name='Benhail Moyo',
                is_active=True,
                totp_enabled=False,
                failed_login_count=0,
                locked_until=None
            )
            admin.set_password('Smart-policing1!')
            db.session.add(admin)
            db.session.commit()
            print(f'Admin created successfully: ID={admin.id}, Email={admin.email}, ForceNumber={admin.force_number}, Role={admin.role}')
            
            # Test password verification
            pw_ok = verify_password(admin.password_hash, 'Smart-policing1!')
            print(f'Password verification check: {pw_ok}')
        except Exception as e:
            db.session.rollback()
            print(f'Error during reset in {label}: {e}')

if __name__ == '__main__':
    app = create_app('development')
    reset_and_create(app, 'Current Database')
