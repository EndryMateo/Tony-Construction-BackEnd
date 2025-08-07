from database import Base, engine, SessionLocal
from models import Project, Admin, PasswordResetCode
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

def init_db():
    print("🔗 Conectando a la base de datos...")
    print(engine)

    inspector = inspect(engine)
    print("📋 Tablas antes de crear:")
    print(inspector.get_table_names())

    # Crear todas las tablas necesarias
    Base.metadata.create_all(bind=engine)

    # Refrescar el inspector para mostrar tablas después de la creación
    inspector = inspect(engine)
    print("✅ Tablas después de crear:")
    print(inspector.get_table_names())

    # Crear admin inicial si no existe
    db = SessionLocal()
    try:
        admin_exists = db.query(Admin).filter(Admin.username == "Tony").first()
        if not admin_exists:
            admin = Admin(
                username="Tony",
                email="info@tonydesignconstruction.com",
                password="admin123",  # ⚠️ Puedes cambiarla luego desde el panel de recuperación
            )
            db.add(admin)
            db.commit()
            print("🛠️ Admin inicial creado correctamente.")
        else:
            print("✔️ Admin 'Tony' ya existe. No se creó uno nuevo.")
    except IntegrityError as e:
        print("❌ Error al insertar admin:", e)
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
