from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 🔐 URL de conexión desde variable de entorno
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL:
    raise RuntimeError("DATABASE_URL no está configurado")

# 🛠️ Fix para compatibilidad con postgres://
if POSTGRES_URL.startswith("postgres://"):
    POSTGRES_URL = POSTGRES_URL.replace("postgres://", "postgresql://", 1)

# 🧱 Configuración básica de SQLAlchemy
engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# 📦 Inicializar base de datos (solo Project)
def init_db():
    from models import Project
    Base.metadata.create_all(bind=engine)
