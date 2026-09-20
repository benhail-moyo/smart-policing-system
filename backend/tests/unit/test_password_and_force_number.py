import pytest
from app import create_app, db
from app.models.models import User
from app.security.passwords import validate_force_number, validate_password_strength, verify_password


def test_validate_force_number():
    # Valid formats (6 digits + 1 capital letter)
    assert validate_force_number("123456X")[0] is True
    assert validate_force_number("084512A")[0] is True
    assert validate_force_number("000101A")[0] is True
    assert validate_force_number("998877Z")[0] is True
    # Lowercase gets normalized
    assert validate_force_number("084512a")[0] is True

    # Invalid formats
    assert validate_force_number("")[0] is False
    assert validate_force_number("123456")[0] is False  # missing letter
    assert validate_force_number("12345A")[0] is False   # only 5 digits
    assert validate_force_number("1234567A")[0] is False # 7 digits
    assert validate_force_number("123456AB")[0] is False # 2 letters
    assert validate_force_number("ABCDEFG")[0] is False  # no digits
    assert validate_force_number("123456!")[0] is False  # special character instead of letter


def test_validate_password_strength_criteria():
    # Rule 1: Min length 8
    valid, errors = validate_password_strength("P@ss1")
    assert valid is False
    assert any("at least 8 characters" in e for e in errors)

    # Rule 2: Special character
    valid, errors = validate_password_strength("Password123")
    assert valid is False
    assert any("special character" in e for e in errors)

    # Rule 3: Capital letter
    valid, errors = validate_password_strength("password123!")
    assert valid is False
    assert any("capital letter" in e for e in errors)

    # Rule 4: Number
    valid, errors = validate_password_strength("Password!@#")
    assert valid is False
    assert any("number" in e for e in errors)

    # All criteria satisfied
    valid, errors = validate_password_strength("Harare-Secure-2026!")
    assert valid is True
    assert len(errors) == 0


def test_validate_password_similarity():
    user_ctx = {
        "name": "Benhail Moyo",
        "email": "benhailmoyo7@gmail.com",
        "force_number": "084512A"
    }

    # Similar to name
    valid, errors = validate_password_strength("Benhail-2026!", user_ctx)
    assert valid is False
    assert any("too similar" in e for e in errors)

    # Similar to email
    valid, errors = validate_password_strength("BenhailMoyo7-2026!", user_ctx)
    assert valid is False
    assert any("too similar" in e for e in errors)

    # Similar to force number
    valid, errors = validate_password_strength("084512A-Secure!", user_ctx)
    assert valid is False
    assert any("too similar" in e for e in errors)

    # Not similar -> passes
    valid, errors = validate_password_strength("Harare-Command-2026!", user_ctx)
    assert valid is True
    assert len(errors) == 0


def test_force_number_officer_login_and_community_login(app, client):
    with app.app_context():
        # Clean existing test users if present
        db.session.query(User).filter(
            (User.email.in_(["officer_test@harare.gov.zw", "community_test@harare.gov.zw"])) |
            (User.force_number == "084512A")
        ).delete()
        db.session.commit()

        # Create an officer with Force Number and official email
        officer = User(
            name="Officer Chikwava",
            email="officer_test@harare.gov.zw",
            force_number="084512A",
            officer_id="084512A",
            role="officer"
        )
        officer.set_password("Officer-2026!")
        db.session.add(officer)

        # Create a community user with email
        community = User(
            name="Tendai Moyo",
            email="community_test@harare.gov.zw",
            role="community"
        )
        community.set_password("Community-2026!")
        db.session.add(community)
        db.session.commit()

    # 1. Officer logs in with Force Number -> triggers SMTP OTP
    res = client.post("/api/v1/auth/login", json={
        "force_number": "084512A",
        "password": "Officer-2026!"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("requires_otp") is True
    assert "masked_email" in data

    # 2. Officer attempting email login -> rejected with instruction
    res = client.post("/api/v1/auth/login", json={
        "email": "officer_test@harare.gov.zw",
        "password": "Officer-2026!"
    })
    assert res.status_code == 400
    assert "must log in with their Force Number" in res.get_json()["error"]

    # 3. Community member logs in with Email -> direct sign in (no 2FA)
    res = client.post("/api/v1/auth/login", json={
        "email": "community_test@harare.gov.zw",
        "password": "Community-2026!"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data
    assert data["role"] == "community"

