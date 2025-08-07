from fastapi import Request
from jose import jwt
from datetime import datetime, timedelta
import secrets
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from database import SessionLocal
from models import Admin, PasswordResetCode
import os
import requests

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "your_resend_api_key")
RESET_URL = os.getenv("RESET_URL", "https://admin.tonydesignconstruction.com/admin/reset-password")

templates = Jinja2Templates(directory="templates")


# 1. Autenticación del admin
def authenticate_user(db, username: str, password: str):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or admin.password != password:
        return None
    return admin


# 2. Crear token de acceso
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 3. Enviar correo de recuperación usando RESEND
def send_recovery_email(to_email: str, code: str):
    url = "https://api.resend.com/emails"
    html_content = f"""
        <h2>Password Recovery - Tony Design Construction LLC</h2>
        <p>Your recovery code is:</p>
        <h3>{code}</h3>
        <p>This code is valid for 10 minutes.</p>
    """
    payload = {
        "from": "Tony Design Construction <info@tonydesignconstruction.com>",
        "to": [to_email],
        "subject": "Password Recovery Code",
        "html": html_content,
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 200


# 4. Verificar el código de recuperación
def verify_code_and_generate_token(db, code: str):
    record = db.query(PasswordResetCode).filter(PasswordResetCode.code == code).first()
    if not record:
        return None
    if datetime.utcnow() > record.expires_at:
        return None
    reset_token = create_access_token({"email": record.email})
    return reset_token


# 5. Cambiar la contraseña del admin
def update_password(db, token: str, new_password: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        if email is None:
            return False
        admin = db.query(Admin).filter(Admin.email == email).first()
        if admin:
            admin.password = new_password
            db.commit()
            return True
        return False
    except Exception:
        return False
