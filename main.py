from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from models import Project
from utils import (
    authenticate_user,
    create_access_token,
    send_recovery_email,
    generate_token as verify_code_and_generate_token,
    update_admin_password as update_password,
)
from database import SessionLocal
import secrets

app = FastAPI()

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Middleware
SECRET_KEY = secrets.token_hex(32)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Utils
def require_login(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)


# Home redirect
@app.get("/", response_class=HTMLResponse)
def read_root():
    return RedirectResponse(url="/admin")


# Login
@app.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/admin/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = authenticate_user(db, username, password)
    db.close()
    if user:
        request.session["user"] = username
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})


# Admin Panel
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    redirect = require_login(request)
    if redirect: return redirect
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/admin/projects", response_class=HTMLResponse)
def admin_projects(request: Request):
    redirect = require_login(request)
    if redirect: return redirect
    from utils import get_all_projects
    projects = get_all_projects()
    return templates.TemplateResponse("projects_admin.html", {"request": request, "projects": projects})


@app.post("/admin/create", response_class=HTMLResponse)
def create_project(request: Request, title: str = Form(...), description: str = Form(...), images: str = Form(...), video_link: Optional[str] = Form(None)):
    redirect = require_login(request)
    if redirect: return redirect
    from utils import create_project
    new_project = Project(title=title, description=description, image_paths=images, video_url=video_link)
    create_project(new_project)
    return RedirectResponse(url="/admin/projects", status_code=status.HTTP_302_FOUND)


@app.post("/admin/delete/{project_id}", response_class=HTMLResponse)
def delete_project(request: Request, project_id: int):
    redirect = require_login(request)
    if redirect: return redirect
    from utils import delete_project_by_id
    delete_project_by_id(project_id)
    return RedirectResponse(url="/admin/projects", status_code=status.HTTP_302_FOUND)


# Recovery
@app.get("/admin/recover-password", response_class=HTMLResponse)
def recover_password_page(request: Request):
    return templates.TemplateResponse("recover_password_form.html", {"request": request})


@app.post("/admin/request-password", response_class=HTMLResponse)
def request_password(request: Request, email: str = Form(...)):
    db = SessionLocal()
    code_sent = send_recovery_email(db, email)
    db.close()
    if not code_sent:
        return templates.TemplateResponse("recover_password_form.html", {"request": request, "error": "Email not found"})
    request.session["recovery_email"] = email
    return RedirectResponse(url="/admin/verify-code", status_code=status.HTTP_302_FOUND)


@app.get("/admin/verify-code", response_class=HTMLResponse)
def verify_code_page(request: Request):
    return templates.TemplateResponse("verify_code.html", {"request": request})


@app.post("/admin/verify-code", response_class=HTMLResponse)
def verify_code(request: Request, code: str = Form(...)):
    email = request.session.get("recovery_email")
    if not email:
        return RedirectResponse(url="/admin/recover-password", status_code=status.HTTP_302_FOUND)

    db = SessionLocal()
    token = verify_code_and_generate_token(db, code)
    db.close()

    if not token:
        return templates.TemplateResponse("verify_code.html", {"request": request, "error": "Invalid or expired code"})

    request.session["reset_token"] = token
    return RedirectResponse(url="/admin/reset-password", status_code=status.HTTP_302_FOUND)


@app.get("/admin/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request):
    return templates.TemplateResponse("change_password.html", {"request": request})


@app.post("/admin/reset-password", response_class=HTMLResponse)
def reset_password(request: Request, new_password: str = Form(...), confirm_password: str = Form(...)):
    if new_password != confirm_password:
        return templates.TemplateResponse("change_password.html", {"request": request, "error": "Passwords do not match"})

    token = request.session.get("reset_token")
    if not token:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    db = SessionLocal()
    success = update_password(db, token, new_password)
    db.close()

    if success:
        request.session.clear()
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("change_password.html", {"request": request, "error": "Password update failed"})


# Logout
@app.get("/admin/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
