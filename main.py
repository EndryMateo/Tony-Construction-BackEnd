from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime, timedelta
from models import Project, Base
from database import engine, SessionLocal
from uuid import uuid4
from typing import List
import os
import shutil
import smtplib
import requests

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
Base.metadata.create_all(bind=engine)

# Settings
UPLOAD_FOLDER = "static/uploads"
ALLOWED_USERNAME = "admintony"
ALLOWED_PASSWORD = "admin123"
RESET_CODES = {}
RESET_TOKENS = {}

# Temporary email for testing
EMAIL_FROM = "endrymateod1011@gmail.com"
RESEND_API_KEY = "re_TNz9YirM_PceZu5yoyZuQVieSwVzn9AcP"

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Auth utilities
def is_logged_in(request: Request):
    return request.session.get("logged_in") is True


def require_login(request: Request):
    if not is_logged_in(request):
        raise HTTPException(status_code=401, detail="Unauthorized")


# Routes
@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/admin")


@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    require_login(request)
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/admin/projects", response_class=HTMLResponse)
def view_projects(request: Request, db=Depends(get_db)):
    require_login(request)
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return templates.TemplateResponse("projects_admin.html", {"request": request, "projects": projects})


@app.post("/admin/create-project")
def create_project(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    video_url: str = Form(""),
    images: List[UploadFile] = File(...),
    db=Depends(get_db)
):
    require_login(request)

    filenames = []
    for image in images:
        extension = os.path.splitext(image.filename)[1]
        new_filename = f"{uuid4()}{extension}"
        file_location = os.path.join(UPLOAD_FOLDER, new_filename)

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        filenames.append(f"/static/uploads/{new_filename}")

    project = Project(
        title=title,
        description=description,
        video_url=video_url,
        image_paths=",".join(filenames),
        created_at=datetime.now()
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return RedirectResponse(url="/admin?success=1", status_code=303)


@app.post("/admin/delete-project/{project_id}")
def delete_project(project_id: int, request: Request, db=Depends(get_db)):
    require_login(request)
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        return {"error": "Project not found."}

    # Delete images
    for path in project.image_paths.split(","):
        try:
            os.remove(path.strip("/"))
        except Exception:
            pass

    db.delete(project)
    db.commit()

    return {"message": "Project deleted successfully."}


@app.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/admin/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ALLOWED_USERNAME and password == ALLOWED_PASSWORD:
        request.session["logged_in"] = True
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})


@app.get("/admin/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=302)


@app.get("/admin/recover-password", response_class=HTMLResponse)
def recover_password(request: Request):
    return templates.TemplateResponse("recover_password.html", {"request": request})


@app.post("/admin/recover-password")
def send_recovery_code(email: str = Form(...)):
    if email != EMAIL_FROM:
        raise HTTPException(status_code=403, detail="Unauthorized email")

    code = str(uuid4())[:6]
    RESET_CODES[email] = {"code": code, "expires": datetime.utcnow() + timedelta(minutes=10)}

    # Send email using Resend API
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "from": f"TONY Design Construction <{EMAIL_FROM}>",
        "to": [EMAIL_FROM],
        "subject": "Your Password Reset Code",
        "html": f"<p>Hello,</p><p>Your code is:</p><h2>{code}</h2><p>It expires in 10 minutes.</p>"
    }

    response = requests.post("https://api.resend.com/emails", json=data, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return RedirectResponse(url="/admin/verify-code", status_code=302)


@app.get("/admin/verify-code", response_class=HTMLResponse)
def verify_code_page(request: Request):
    return templates.TemplateResponse("verify_code.html", {"request": request})


@app.post("/admin/verify-code")
def verify_code(email: str = Form(...), code: str = Form(...)):
    entry = RESET_CODES.get(email)

    if not entry or entry["code"] != code or datetime.utcnow() > entry["expires"]:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    token = str(uuid4())
    RESET_TOKENS[token] = email
    del RESET_CODES[email]

    return RedirectResponse(url=f"/admin/reset-password/{token}", status_code=302)


@app.get("/admin/reset-password/{token}", response_class=HTMLResponse)
def reset_password_page(token: str, request: Request):
    if token not in RESET_TOKENS:
        return RedirectResponse(url="/admin/login")
    return templates.TemplateResponse("change_password.html", {"request": request})


@app.post("/admin/reset-password/{token}")
def reset_password(token: str, new_password: str = Form(...), confirm_password: str = Form(...)):
    if token not in RESET_TOKENS:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    global ALLOWED_PASSWORD
    ALLOWED_PASSWORD = new_password

    del RESET_TOKENS[token]
    return RedirectResponse(url="/admin/login", status_code=302)
