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

def authenticate_user(db, username: str, password: str):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or admin.password != password:
        return None
    return admin

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request):
    token = request.cookies.get("access_token")
    if not token:
        raise JWTError("Token missing")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload.get("sub")

def send_recovery_email(email: str, token: str):
    html_content = f"""
        <h2>Password Reset - Tony Design Construction</h2>
        <p>Click the link below to reset your password:</p>
        <a href="https://admin.tonydesignconstruction.com/admin/reset-password?token={token}">Reset Password</a>
        <p>This link expires in 10 minutes.</p>
    """
    payload = {
        "from": "Tony Design Construction <info@tonydesignconstruction.com>",
        "to": [email],
        "subject": "Password Reset",
        "html": html_content,
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
    return response.status_code == 200

def generate_token(data: dict, expires_minutes: int = 10):
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def update_admin_password(db, username: str, new_password: str):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin:
        admin.password = new_password
        db.commit()
