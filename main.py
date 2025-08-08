# main.py
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional
from models import Project, Admin, PasswordResetCode
from utils import (
    authenticate_user,
    create_access_token,
    send_recovery_email,
    update_admin_password as update_password,
    create_project,
    delete_project_by_id,
)
from database import SessionLocal, engine, Base
import secrets
from jose import jwt
from jose.exceptions import JWTError
from auth import hash_password
from sqlalchemy.exc import IntegrityError

# Init FastAPI
app = FastAPI()

# Forzar carga de modelos antes de crear tablas
db = SessionLocal()
try:
    db.query(Admin).first()  # 👈 asegura que Admin esté registrado
finally:
    db.close()

# Crear tablas de todos los modelos
Base.metadata.create_all(bind=engine)

# Si lo deseas puedes mantener esta parte, pero ya no es necesaria si arriba funciona
# from init_db import init_db
# @app.on_event("startup")
# def on_startup():
#     try:
#         init_db()
#     except Exception as e:
#         print("❌ Error al inicializar la base de datos:", e)

# Static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Middleware
SECRET_KEY = secrets.token_hex(32)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Utility
def require_login(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

# ... (todo el resto de las rutas se queda igual)
