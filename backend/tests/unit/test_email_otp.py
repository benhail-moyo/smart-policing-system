from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest

from app import create_app, db
from app.models.models import User, EmailOTP
from app.services.email_service import EmailService
from app.services.otp_service import OTPService


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_email_service_dynamic_config(monkeypatch):
    service = EmailService()
    
    monkeypatch.delenv('SMTP_USERNAME', raising=False)
    monkeypatch.delenv('SMTP_PASSWORD', raising=False)
    monkeypatch.delenv('SMTP_SERVER', raising=False)
    monkeypatch.delenv('SMTP_PORT', raising=False)
    monkeypatch.delenv('FROM_EMAIL', raising=False)
    
    assert not service.is_configured()
    assert service.smtp_server == 'smtp.gmail.com'
    assert service.smtp_port == 587
    assert service.from_email == ''

    monkeypatch.setenv('SMTP_SERVER', 'smtp.custom.org')
    monkeypatch.setenv('SMTP_PORT', '465')
    monkeypatch.setenv('SMTP_USERNAME', 'mailer@custom.org')
    monkeypatch.setenv('SMTP_PASSWORD', 'secret123')
    monkeypatch.setenv('FROM_EMAIL', 'notifications@custom.org')

    assert service.is_configured()
    assert service.smtp_server == 'smtp.custom.org'
    assert service.smtp_port == 465
    assert service.smtp_username == 'mailer@custom.org'
    assert service.from_email == 'notifications@custom.org'


def test_email_otp_model_timezone_handling(app):
    otp_aware_valid = EmailOTP(
        user_id=1,
        code='123456',
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        used=False
    )
    assert otp_aware_valid.is_valid()

    otp_aware_expired = EmailOTP(
        user_id=1,
        code='123456',
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        used=False
    )
    assert not otp_aware_expired.is_valid()

    otp_naive_valid = EmailOTP(
        user_id=1,
        code='123456',
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        used=False
    )
    assert otp_naive_valid.is_valid()

    otp_naive_expired = EmailOTP(
        user_id=1,
        code='123456',
        expires_at=datetime.utcnow() - timedelta(minutes=5),
        used=False
    )
    assert not otp_naive_expired.is_valid()

    otp_used = EmailOTP(
        user_id=1,
        code='123456',
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        used=True
    )
    assert not otp_used.is_valid()


def test_otp_service_generation_and_verification(app, monkeypatch):
    monkeypatch.setenv('SMTP_USERNAME', 'test@harare.gov.zw')
    monkeypatch.setenv('SMTP_PASSWORD', 'password123')

    user = User(
        name='Officer Test',
        email='officer_otp@harare.gov.zw',
        role='officer'
    )
    user.set_password('securepassword123')
    db.session.add(user)
    db.session.commit()

    otp_service = OTPService()

    with patch('app.services.email_service.email_service.send_otp_email', return_value=True) as mock_send:
        msg, err = otp_service.generate_otp(user.id)
        assert err is None
        assert 'OTP sent' in msg
        assert mock_send.called

        otp_record = db.session.query(EmailOTP).filter_by(user_id=user.id, used=False).first()
        assert otp_record is not None
        code = otp_record.code
        assert len(code) == 6

        valid, err = otp_service.verify_otp(user.id, '000000')
        assert not valid
        assert err == 'Invalid OTP code'

        valid, err = otp_service.verify_otp(user.id, code)
        assert valid
        assert err is None

        valid, err = otp_service.verify_otp(user.id, code)
        assert not valid


def test_officer_login_2fa_flow(client, monkeypatch):
    monkeypatch.setenv('SMTP_USERNAME', 'test@harare.gov.zw')
    monkeypatch.setenv('SMTP_PASSWORD', 'password123')

    user = User(
        name='Officer Danai',
        email='officer_danai@harare.gov.zw',
        role='officer'
    )
    user.set_password('securepassword123')
    db.session.add(user)
    db.session.commit()

    with patch('app.services.email_service.email_service.send_otp_email', return_value=True):
        res1 = client.post('/api/v1/auth/login', json={
            'email': 'officer_danai@harare.gov.zw',
            'password': 'securepassword123'
        })
        assert res1.status_code == 200
        data1 = res1.get_json()
        assert data1.get('requires_otp') is True

        otp = db.session.query(EmailOTP).filter_by(user_id=user.id, used=False).first()
        assert otp is not None

        res2_fail = client.post('/api/v1/auth/login', json={
            'email': 'officer_danai@harare.gov.zw',
            'password': 'securepassword123',
            'otp_code': '999999'
        })
        assert res2_fail.status_code == 401

        res2_pass = client.post('/api/v1/auth/login', json={
            'email': 'officer_danai@harare.gov.zw',
            'password': 'securepassword123',
            'otp_code': otp.code
        })
        assert res2_pass.status_code == 200
        data2 = res2_pass.get_json()
        assert 'access_token' in data2
        assert data2['role'] == 'officer'
