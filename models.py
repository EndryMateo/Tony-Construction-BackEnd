from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

# ✅ Modelo de proyectos
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    image_paths = Column(String(1000))  # rutas separadas por coma
    video_url = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
