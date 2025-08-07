from database import Base, engine, SessionLocal
from models import Project, Admin, PasswordResetCode
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from auth import hash_password
import sys

def init_db():
    print("🔗 Conectando a la base de datos...")
    try:
        inspector = inspect(engine)
        print("📋 Tablas antes de crear:")
        print(inspector.get_table_names())

        # Crear todas las tablas necesarias si no existen
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        print("✅ Tablas después de crear:")
        print(inspector.get_table_names())

        # Crear admin por defecto si no existe
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
                print("✔️ Admin 'Tony' ya existe. No se creó uno nuevo.")
        except IntegrityError as e:
            print("❌ Error de integridad al insertar admin:", e)
        finally:
            db.close()

    except Exception as e:
        print("❌ Error al conectar o inicializar la base de datos:", e)
        sys.exit(1)

# Solo se ejecuta si corres `python init_db.py`
if __name__ == "__main__":
    init_db()
