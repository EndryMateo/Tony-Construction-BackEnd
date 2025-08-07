from fastapi import FastAPI, Request, Form, status, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from typing import Optional

from database import create_project, get_all_projects, delete_project_by_id
from models import Project
from auth import authenticate_user, create_access_token, send_recovery_email, verify_code_and_generate_token, update_password

import secrets

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Secret key for sessions
SECRET_KEY = secrets.token_hex(32)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Redirect to login if not authenticated
def require_login(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)


@app.get("/", response_class=HTMLResponse)
def read_root():
    return RedirectResponse(url="/admin")


@app.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/admin/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if authenticate_user(username, password):
        request.session["user"] = username
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    redirect = require_login(request)
    if redirect: return redirect
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/admin/projects", response_class=HTMLResponse)
def admin_projects(request: Request):
    redirect = require_login(request)
    if redirect: return redirect
    projects = get_all_projects()
    return templates.TemplateResponse("projects_admin.html", {"request": request, "projects": projects})


@app.post("/admin/create", response_class=HTMLResponse)
def create(request: Request, title: str = Form(...), description: str = Form(...), images: str = Form(...), video_link: Optional[str] = Form(None)):
    redirect = require_login(request)
    if redirect: return redirect
    new_project = Project(title=title, description=description, images=images, video_link=video_link)
    create_project(new_project)
    return RedirectResponse(url="/admin/projects", status_code=status.HTTP_302_FOUND)


@app.post("/admin/delete/{project_id}", response_class=HTMLResponse)
def delete_project(request: Request, project_id: int):
    redirect = require_login(request)
    if redirect: return redirect
    delete_project_by_id(project_id)
    return RedirectResponse(url="/admin/projects", status_code=status.HTTP_302_FOUND)


@app.get("/admin/recover-password", response_class=HTMLResponse)
def recover_password_page(request: Request):
    return templates.TemplateResponse("recover_password_form.html", {"request": request})


@app.post("/admin/request-password", response_class=HTMLResponse)
def request_password(request: Request, email: str = Form(...)):
    success = send_recovery_email(email)
    if not success:
        return templates.TemplateResponse("recover_password_form.html", {"request": request, "error": "Email not found"})
    request.session["recovery_email"] = email
    return RedirectResponse(url="/admin/verify-code", status_code=status.HTTP_302_FOUND)


@app.get("/admin/verify-code", response_class=HTMLResponse)
def verify_code_page(request: Request):
    return templates.TemplateResponse("verify_code.html", {"request": request})


@app.post("/admin/verify-code", response_class=HTMLResponse)
def verify_code(request: Request, code: str = Form(...)):
    email = request.session.get("recovery_email")
    if not email or not verify_code_and_generate_token(email, code):
        return templates.TemplateResponse("verify_code.html", {"request": request, "error": "Invalid or expired code"})
    request.session["reset_token"] = code  # token temporal para cambiar contraseña
    return RedirectResponse(url="/admin/reset-password", status_code=status.HTTP_302_FOUND)


@app.get("/admin/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request):
    return templates.TemplateResponse("change_password.html", {"request": request})


@app.post("/admin/reset-password", response_class=HTMLResponse)
def reset_password(request: Request, new_password: str = Form(...), confirm_password: str = Form(...)):
    if new_password != confirm_password:
        return templates.TemplateResponse("change_password.html", {"request": request, "error": "Passwords do not match"})

    email = request.session.get("recovery_email")
    token = request.session.get("reset_token")

    if not email or not token:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    success = update_password(email, new_password)
    if success:
        request.session.clear()
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("change_password.html", {"request": request, "error": "Password update failed"})


@app.get("/admin/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
