from fastapi import FastAPI, Request, Form, UploadFile, File, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional, List
from models import Project
from database import SessionLocal, engine, Base
from resend_utils import send_recovery_email
import os
from uuid import uuid4
import random

# --- 🔒 Seguridad
SECRET_KEY = "your_secret_key_here"  # Usa uno seguro en producción

# --- 🚀 Inicializar la app
app = FastAPI()

# --- 🧱 Crear tablas
Base.metadata.create_all(bind=engine)

# --- 📁 Archivos estáticos y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- 🔀 Middleware de sesión
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# --- 🔐 Verificación de sesión
def require_login(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

# --- 🌐 Redirección raíz
@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse("/admin")

# --- 🔑 Login
@app.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/admin/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "tony" and password == "admin123":
        request.session["user"] = username
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

# --- 🔚 Logout
@app.get("/admin/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

# --- 📋 Panel admin
@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    redirect = require_login(request)
    if redirect: return redirect
    return templates.TemplateResponse("admin.html", {"request": request})

# --- 📂 Ver proyectos (excluyendo recoveries)
@app.get("/admin/projects", response_class=HTMLResponse)
def list_projects(request: Request):
    redirect = require_login(request)
    if redirect: return redirect
    db = SessionLocal()
    projects = (
        db.query(Project)
        .filter(~Project.title.startswith("recovery-"))
        .order_by(Project.id.desc())
        .all()
    )
    db.close()
    return templates.TemplateResponse("projects_admin.html", {"request": request, "projects": projects})

# --- ➕ Crear nuevo proyecto
@app.post("/admin/create-project", response_class=HTMLResponse)
async def create_project(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    video_url: Optional[str] = Form(None),
    images: List[UploadFile] = File(...)
):
    redirect = require_login(request)
    if redirect: return redirect

    upload_dir = "static/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    filenames = []
    for image in images:
        extension = image.filename.split(".")[-1]
        filename = f"{uuid4().hex}.{extension}"
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(await image.read())
        filenames.append(f"/static/uploads/{filename}")

    image_paths = ",".join(filenames)

    db = SessionLocal()
    new_project = Project(title=title, description=description, video_url=video_url, image_paths=image_paths)
    db.add(new_project)
    db.commit()
    db.close()

    return RedirectResponse(url="/admin?success=1", status_code=status.HTTP_302_FOUND)

# --- ❌ Eliminar proyecto
@app.post("/admin/delete-project/{project_id}")
def delete_project(request: Request, project_id: int):
    redirect = require_login(request)
    if redirect: return redirect

    db = SessionLocal()
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        db.close()
        return JSONResponse(status_code=404, content={"error": "Project not found"})

    for path in project.image_paths.split(","):
        try:
            os.remove(path.lstrip("/"))
        except:
            pass

    db.delete(project)
    db.commit()
    db.close()
    return JSONResponse(content={"message": "Project deleted successfully"})

# --- 🔁 Página de recuperación de contraseña
@app.get("/admin/recover-password", response_class=HTMLResponse)
def recover_password_page(request: Request):
    return templates.TemplateResponse("recover_password.html", {"request": request})

# --- 📩 Solicitud de código de recuperación
@app.post("/admin/request-password")
def request_password(request: Request, email: str = Form(...)):
    db = SessionLocal()

    VALID_ADMIN_EMAIL = "endrymateod1011@gmail.com"
    if email != VALID_ADMIN_EMAIL:
        db.close()
        return templates.TemplateResponse("recover_password.html", {
            "request": request,
            "error": "Email not found"
        })

    code = f"{random.randint(100000, 999999)}"

    recovery_project = Project(
        title=f"recovery-{email}",
        description=code,
        video_url=None,
        image_paths=""
    )
    db.add(recovery_project)
    db.commit()

    success = send_recovery_email(email, code)
    db.close()

    if success:
        request.session["verified_email"] = email
        return templates.TemplateResponse("verify_code.html", {
            "request": request,
            "email": email
        })
    else:
        return templates.TemplateResponse("recover_password.html", {
            "request": request,
            "error": "Failed to send email. Please try again later."
        })

# --- 🔐 Verificar código
@app.get("/admin/verify-code", response_class=HTMLResponse)
def verify_code_page(request: Request):
    return templates.TemplateResponse("verify_code.html", {"request": request})

@app.post("/admin/verify-code")
def verify_code(request: Request, code: str = Form(...)):
    db = SessionLocal()
    email = request.session.get("verified_email")

    recovery_project = (
        db.query(Project)
        .filter(Project.title == f"recovery-{email}", Project.description == code)
        .order_by(Project.id.desc())
        .first()
    )
    db.close()

    if not recovery_project:
        return templates.TemplateResponse("verify_code.html", {
            "request": request,
            "error": "Invalid code"
        })

    request.session["verified_code"] = code
    return RedirectResponse(url="/admin/change-password", status_code=status.HTTP_302_FOUND)

# --- 🔑 Página de cambio de contraseña
@app.get("/admin/change-password", response_class=HTMLResponse)
def change_password_page(request: Request):
    if "verified_code" not in request.session:
        return RedirectResponse(url="/admin/recover-password", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("change_password.html", {"request": request})

@app.post("/admin/change-password")
def change_password(request: Request, new_password: str = Form(...), confirm_password: str = Form(...)):
    if "verified_code" not in request.session or "verified_email" not in request.session:
        return RedirectResponse(url="/admin/recover-password", status_code=status.HTTP_302_FOUND)

    if new_password != confirm_password:
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "error": "Passwords do not match"
        })

    if request.session["verified_email"] == "endrymateod1011@gmail.com":
        with open("secrets.txt", "w") as f:
            f.write(new_password)

    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
