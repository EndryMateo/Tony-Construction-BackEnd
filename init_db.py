# init_db.py ✅

from database import Base, engine, SessionLocal
from models import Project, Admin, PasswordResetCode
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from auth import hash_password

def init_db():
    print("🔗 Conectando a la base de datos...")
    inspector = inspect(engine)
    print("📋 Tablas antes de crear:")
    print(inspector.get_table_names())

    # Crear tablas
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    print("✅ Tablas después de crear:")
    print(inspector.get_table_names())

    # Crear admin
    if "admins" in inspector.get_table_names():
        db = SessionLocal()
        try:
            admin_exists = db.query(Admin).filter(Admin.username == "Tony").first()
            if not admin_exists:
                admin = Admin(
                    username="Tony",
                    email="info@tonydesignconstruction.com",
                    password=hash_password("admin123"),
                )
                db.add(admin)
                db.commit()
                print("🛠️ Admin inicial creado correctamente.")
            else:
                print("✔️ Admin 'Tony' ya existe.")
        except IntegrityError as e:
            print("❌ Error al insertar admin:", e)
        finally:
            db.close()
    else:
        print("❌ La tabla 'admins' no fue creada.")

# Ejecutar solo si se llama directamente
if __name__ == "__main__":
    init_db()
    print("📦 Base de datos creada correctamente.")
