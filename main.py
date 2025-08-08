from fastapi import FastAPI, Request, Form, UploadFile, File, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional, List
from models import Project
from database import SessionLocal, engine, Base
import os
from uuid import uuid4

# --- 🔒 Seguridad
SECRET_KEY = "your_secret_key_here"  # Usa uno seguro en producción

# --- 🚀 Inicializar la app
app = FastAPI()

# --- 🧱 Crear tablas
Base.metadata.create_all(bind=engine)

# --- 📁 Archivos estáticos y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- 🧠 Middleware de sesión
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

# --- 📂 Ver proyectos
@app.get("/admin/projects", response_class=HTMLResponse)
def list_projects(request: Request):
    redirect = require_login(request)
    if redirect: return redirect
    db = SessionLocal()
    projects = db.query(Project).order_by(Project.id.desc()).all()
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

    # Eliminar imágenes del sistema
    for path in project.image_paths.split(","):
        try:
            os.remove(path.lstrip("/"))
        except:
            pass

    db.delete(project)
    db.commit()
    db.close()
    return JSONResponse(content={"message": "Project deleted successfully"})
