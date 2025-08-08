from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

# ✅ Modelo de administrador
class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

# ✅ Modelo de proyectos
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    image_paths = Column(String(1000))  # 👈 corresponde a lo que usas en el backend
    video_url = Column(String(255))     # 👈 corresponde a lo que usas en el backend
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# ✅ Modelo para recuperación de contraseña
class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False)
    code = Column(String(6), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
