# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ⚠️ Reemplaza con tus datos reales de Postgres
POSTGRES_URL = "postgresql://postgres:admin007@localhost:5432/tonydb"

engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def init_db():
    from models import Project
    Base.metadata.create_all(bind=engine)