from passlib.context import CryptContext
from models import Admin, Project
from sqlalchemy.orm import Session
from database import SessionLocal
from jose import jwt
from datetime import datetime, timedelta
import requests
import os

# ========================
# Seguridad y Hasheo
# ========================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "secret")  # Cambia esto en producción
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(Admin).filter(Admin.username == username).first()
    if not user or not verify_password(password, user.password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ========================
# Proyectos
# ========================
def create_project(project: Project):
    db = SessionLocal()
    db.add(project)
    db.commit()
    db.close()

def delete_project_by_id(project_id: int):
    db = SessionLocal()
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        db.delete(project)
        db.commit()
    db.close()

# ========================
# Recuperación de contraseña (via Resend)
# ========================
def send_recovery_email(email: str, token: str) -> bool:
    api_key = os.getenv("RESEND_API_KEY", "re_hjkZkuTC_KgkNAHaXKaY58i2Nryv3AMGg")
    reset_url = f"https://admin.tonydesignconstruction.com/admin/reset-password"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    html_content = f"""
    <html>
        <body>
            <h2>Password Reset</h2>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_url}">{reset_url}</a>
        </body>
    </html>
    """

    data = {
        "from": "TONY Design Construction <info@tonydesignconstruction.com>",
        "to": [email],
        "subject": "Password Reset - Tony Design Construction",
        "html": html_content
    }

    try:
        response = requests.post("https://api.resend.com/emails", json=data, headers=headers)
        print("📧 Resend response:", response.status_code, response.text)
        return response.status_code == 200
    except Exception as e:
        print("Error al enviar el correo:", e)
        return False

# ========================
# Actualizar contraseña del admin
# ========================
def update_admin_password(db: Session, email: str, new_password: str) -> bool:
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin:
        return False
    admin.password = hash_password(new_password)
    db.commit()
    return True
