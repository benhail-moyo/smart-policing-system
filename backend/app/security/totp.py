import pyotp
import qrcode
import io
import base64

def generate_totp_secret() -> str:
    return pyotp.random_base32()

def get_provisioning_qr_base64(secret: str, account_name: str, issuer: str = "Crime-Watch") -> str:
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer)
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # allows ±30s clock drift
