from fastapi import FastAPI, Request, UploadFile, File, Form
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
from datetime import datetime

print("🔁 Cambio de prueba para confirmar push")

app = FastAPI()

init_db()

print("🚀 Iniciando FastAPI...")

# Habilitar CORS
origins = [
    "http://localhost",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://tu-sitio-en-cloudflare.pages.dev",  # Reemplaza con tu dominio real
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos y plantillas
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Carpeta para imágenes de proyectos
PROJECT_IMAGE_FOLDER = "static/uploads/images_projects"
os.makedirs(PROJECT_IMAGE_FOLDER, exist_ok=True)

# ✅ Probar conexión a la base de datos al iniciar
@app.on_event("startup")
def test_db_connection():
    try:
        print("🔄 Intentando conectar a la base de datos...")
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        print("✅ Conexión a la base de datos exitosa.")
        db.close()
    except Exception as e:
        print("❌ Error al conectar a la base de datos:", e)

# ✅ Crear un proyecto con redirect
@app.post("/admin/create-project")
async def create_project(
    title: str = Form(...),
    description: str = Form(...),
    video_url: str = Form(...),
    images: List[UploadFile] = File(...),
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

    # 🔁 Redirigir al panel con mensaje
    return RedirectResponse(url="/admin?success=1", status_code=303)

# Ver todos los proyectos (admin panel)
@app.get("/admin/projects", response_class=HTMLResponse)
def admin_projects(request: Request):
    db: Session = SessionLocal()
    projects = db.query(Project).all()
    db.close()
    return templates.TemplateResponse("projects_admin.html", {"request": request, "projects": projects})

# Eliminar un proyecto
@app.post("/admin/delete-project/{project_id}")
def delete_project(project_id: int):
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

# Ruta API para el frontend
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

# Ruta al panel de admin principal
@app.get("/admin", response_class=HTMLResponse)
def get_admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/")
def root():
    return RedirectResponse(url="/admin")
