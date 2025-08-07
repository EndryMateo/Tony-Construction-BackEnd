from database import Base, engine
from models import Project, Admin, PasswordResetCode  # ✅ Importar todos los modelos
from sqlalchemy import inspect

print("Conectando a la base de datos...")
print(engine)

# Inspecciona antes
inspector = inspect(engine)
print("Antes de crear:")
print(inspector.get_table_names())

# Crea todas las tablas
Base.metadata.create_all(bind=engine)

# Inspecciona después
inspector = inspect(engine)  # Refresca el inspector
print("Después de crear:")
print(inspector.get_table_names())
