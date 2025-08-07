from fastapi import FastAPI, Request, UploadFile, File, Form, Cookie, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import init_db
from models import Project
from database import SessionLocal, engine
from typing import List
import os
import shutil
from datetime import datetime, timedelta
from jose import jwt

print("Cambio de prueba para confirmar push")

app = FastAPI()

init_db()

print("\ud83d\ude80 Iniciando FastAPI...")

# === Configuraci\u00f3n de CORS ===
origins = [
    "http://localhost",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://tonydesignconstruction.com",
    "https://admin.tonydesignconstruction.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Usuario fijo para login ===
ADMIN_USER = "Tony"
ADMIN_PASS = "admin123"

# === JWT Token ===
SECRET = "jwt_secret_for_recovery"
ALGO = "HS256"

# === Cookie y sesi\u00f3n ===
def is_logged_in(session: str = Cookie(default=None)):
    if session != "active":
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/admin/login"})

# === Archivos est\u00e1ticos y plantillas ===
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# === Carpeta para im\u00e1genes de proyectos ===
PROJECT_IMAGE_FOLDER = "static/uploads/images_projects"
os.makedirs(PROJECT_IMAGE_FOLDER, exist_ok=True)

# Verificaci\u00f3n de base de datos
@app.on_event("startup")
def test_db_connection():
    try:
        print("\ud83d\udd04 Intentando conectar a la base de datos...")
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        print("\u2705 Conexi\u00f3n a la base de datos exitosa.")
        db.close()
    except Exception as e:
        print("\u274c Error al conectar a la base de datos:", e)

# === Rutas de autenticaci\u00f3n ===
@app.get("/admin/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/admin/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        response = RedirectResponse(url="/admin", status_code=302)
        response.set_cookie(key="session", value="active", httponly=True, max_age=3600)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/admin/logout")
def logout():
    response = RedirectResponse(url="/admin/login")
    response.delete_cookie("session")
    return response

@app.get("/admin/change-password", response_class=HTMLResponse)
def change_password_page(request: Request, _: str = Depends(is_logged_in)):
    return templates.TemplateResponse("change_password.html", {"request": request})

@app.post("/admin/change-password")
def change_password(request: Request, current_password: str = Form(...),
                    new_password: str = Form(...), confirm_password: str = Form(...),
                    _: str = Depends(is_logged_in)):
    global ADMIN_PASS
    if current_password != ADMIN_PASS:
        return templates.TemplateResponse("change_password.html", {"request": request, "error": "La contrase\u00f1a actual es incorrecta"})
    if new_password != confirm_password:
        return templates.TemplateResponse("change_password.html", {"request": request, "error": "Las nuevas contrase\u00f1as no coinciden"})
    ADMIN_PASS = new_password
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("session")
    return response

@app.get("/admin/recover-password", response_class=HTMLResponse)
def recover_password_page(request: Request):
    token = jwt.encode({"exp": datetime.utcnow() + timedelta(minutes=10)}, SECRET, algorithm=ALGO)
    return HTMLResponse(f'<p>Usa este enlace para resetear tu contrase\u00f1a (v\u00e1lido 10min):<br><a href="/admin/reset-password/{token}">Reset Password</a></p>')

@app.get("/admin/reset-password/{token}", response_class=HTMLResponse)
def reset_password_form(token: str, request: Request):
    try:
        jwt.decode(token, SECRET, algorithms=[ALGO])
    except jwt.ExpiredSignatureError:
        return HTMLResponse("El token expir\u00f3")
    except:
        return HTMLResponse("Token inv\u00e1lido")
    return templates.TemplateResponse("change_password.html", {"request": request})

@app.post("/admin/reset-password/{token}")
def reset_password(token: str, request: Request, new_password: str = Form(...), confirm_password: str = Form(...)):
    try:
        jwt.decode(token, SECRET, algorithms=[ALGO])
    except jwt.JWTError:
        return HTMLResponse("Token inv\u00e1lido o expirado")
    if new_password != confirm_password:
        return templates.TemplateResponse("change_password.html", {"request": request, "error": "Las contrase\u00f1as no coinciden"})
    global ADMIN_PASS
    ADMIN_PASS = new_password
    return HTMLResponse("Contrase\u00f1a actualizada. Por favor <a href='/admin/login'>log in</a> nuevamente.")

# === Rutas protegidas de administraci\u00f3n ===
@app.get("/admin", response_class=HTMLResponse)
def get_admin_page(request: Request, _: str = Depends(is_logged_in)):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/admin/projects", response_class=HTMLResponse)
def admin_projects(request: Request, _: str = Depends(is_logged_in)):
    db: Session = SessionLocal()
    projects = db.query(Project).all()
    db.close()
    return templates.TemplateResponse("projects_admin.html", {"request": request, "projects": projects})

@app.post("/admin/create-project")
async def create_project(
    title: str = Form(...),
    description: str = Form(...),
    video_url: str = Form(None),
    images: List[UploadFile] = File(...),
    _: str = Depends(is_logged_in)
):
    db: Session = SessionLocal()
    image_paths = []
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    for i, image in enumerate(images):
        clean_filename = image.filename.replace(" ", "_").replace("%", "_")
        filename = f"{timestamp}_{i}_{clean_filename}"
        filepath = os.path.join(PROJECT_IMAGE_FOLDER, filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        image_paths.append("/static/uploads/images_projects/" + filename)

    new_project = Project(
        title=title,
        description=description,
        video_url=video_url,
        image_paths=",".join(image_paths),
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    db.close()

    return RedirectResponse(url="/admin?success=1", status_code=303)

@app.post("/admin/delete-project/{project_id}")
def delete_project(project_id: int, _: str = Depends(is_logged_in)):
    db: Session = SessionLocal()
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        for img in project.image_paths.split(","):
            try:
                filepath = os.path.join(os.getcwd(), img.lstrip("/"))
                os.remove(filepath)
            except Exception as e:
                print(f"Error al eliminar {filepath}: {e}")
        db.delete(project)
        db.commit()
        db.close()
        return {"message": "Proyecto eliminado"}
    db.close()
    return JSONResponse(status_code=404, content={"error": "Proyecto no encontrado"})

# === Ruta API para el frontend ===
@app.get("/projects")
def get_projects():
    db: Session = SessionLocal()
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    db.close()
    return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "video_url": p.video_url,
            "images": p.image_paths.split(",") if p.image_paths else [],
        }
        for p in projects
    ]

@app.get("/")
def root():
    return RedirectResponse(url="/admin")
