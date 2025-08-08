# ✅ init_db.py final con soporte para PasswordResetCode

from database import Base, engine, SessionLocal
from models import Project, Admin, PasswordResetCode  # 👈 Incluye el modelo
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from auth import hash_password

def create_admins_table_if_needed():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                username VARCHAR NOT NULL UNIQUE,
                email VARCHAR NOT NULL UNIQUE,
                password VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """))
        print("🧱 Tabla 'admins' creada manualmente (si no existía).")

def init_db():
    print("🔗 Conectando a la base de datos...")
    inspector = inspect(engine)
    print("📋 Tablas antes de crear:")
    print(inspector.get_table_names())

    # ✅ Crear todas las tablas de SQLAlchemy (incluye PasswordResetCode)
    Base.metadata.create_all(bind=engine)

    # ✅ Crear admins manualmente si no existe (PostgreSQL a veces requiere esto)
    if "admins" not in inspector.get_table_names():
        print("⚠️ Tabla 'admins' no detectada. Intentando crearla manualmente...")
        create_admins_table_if_needed()

    # Verificar tablas nuevamente
    inspector = inspect(engine)
    print("✅ Tablas después de crear:")
    print(inspector.get_table_names())

    # Crear admin por defecto solo si la tabla 'admins' existe
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
        except (IntegrityError, ProgrammingError) as e:
            print("❌ Error al insertar admin:", e)
        finally:
            db.close()
    else:
        print("❌ La tabla 'admins' no fue creada ni manualmente.")

# Ejecutar solo si se llama directamente
if __name__ == "__main__":
    init_db()
    print("📦 Base de datos creada correctamente.")
