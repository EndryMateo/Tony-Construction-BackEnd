from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import requests
from database import SessionLocal
from models import Admin

# Config
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# ✅ LOGIN
def authenticate_user(db, username: str, password: str):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or admin.password != password:
        return None
    return admin


# ✅ TOKENS
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def generate_token(db, code: str):
    # Aquí verificamos si el código es válido (mock simple con username='admintony')
    admin = db.query(Admin).filter(Admin.verification_code == code).first()
    if not admin:
        return None

    return create_access_token({"sub": admin.username}, timedelta(minutes=10))


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(request):
    token = request.cookies.get("access_token")
    if not token:
        raise JWTError("Token missing")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload.get("sub")


# ✅ EMAIL
def send_recovery_email(db, email: str):
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin:
        return False

    # Generar código de verificación y token
    code = str(datetime.utcnow().timestamp())[-6:]  # código de 6 dígitos simples
    admin.verification_code = code
    db.commit()

    html_content = f"""
        <h2>Password Recovery - Tony Design Construction</h2>
        <p>Your verification code is:</p>
        <h3>{code}</h3>
        <p>Enter it on the website to reset your password. This code expires in 10 minutes.</p>
    """

    payload = {
        "from": "Tony Design Construction <info@tonydesignconstruction.com>",
        "to": [email],
        "subject": "Password Recovery Code",
        "html": html_content,
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
    return response.status_code == 200


# ✅ CAMBIO DE CONTRASEÑA
def update_admin_password(db, token: str, new_password: str):
    try:
        payload = verify_token(token)
        if not payload:
            return False
        username = payload.get("sub")
        if not username:
            return False

        admin = db.query(Admin).filter(Admin.username == username).first()
        if not admin:
            return False

        admin.password = new_password
        admin.verification_code = None
        db.commit()
        return True
    except Exception:
        return False
