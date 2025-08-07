from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from starlette.status import HTTP_303_SEE_OTHER
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import Project, Admin
from utils import (
    get_current_user, create_access_token, authenticate_user,
    hash_password, verify_password, send_recovery_email,
    generate_token, verify_token, update_admin_password
)
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/admin")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/admin/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/admin/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = authenticate_user(db, username, password)
    if not admin:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
        )
    token = create_access_token({"sub": admin.username})
    response = RedirectResponse(url="/admin", status_code=HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@app.get("/admin/logout")
async def logout():
    response = RedirectResponse(url="/admin/login", status_code=HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@app.get("/admin/recover", response_class=HTMLResponse)
async def recover_form(request: Request):
    return templates.TemplateResponse("recover.html", {"request": request})

@app.post("/admin/recover")
async def send_recovery(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin:
        return templates.TemplateResponse(
            "recover.html",
            {"request": request, "error": "Email not found"},
        )

    token = generate_token({"sub": admin.username})
    send_recovery_email(admin.email, token)
    return templates.TemplateResponse(
        "recover.html",
        {"request": request, "message": "Recovery email sent"},
    )

@app.get("/admin/reset-password", response_class=HTMLResponse)
async def reset_form(request: Request, token: str):
    try:
        verify_token(token)
        return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})
    except jwt.JWTError:
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": "Invalid or expired token"})

@app.post("/admin/reset-password")
async def reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        payload = verify_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=400, detail="Invalid token")

        update_admin_password(db, username, password)
        return RedirectResponse(url="/admin/login", status_code=HTTP_303_SEE_OTHER)
    except jwt.JWTError:
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": "Invalid or expired token"})
