from database import Base, engine
from models import Project
from sqlalchemy import inspect

print("Conectando a la base de datos...")
print(engine)

inspector = inspect(engine)
print("Antes de crear:")
print(inspector.get_table_names())

Base.metadata.create_all(bind=engine)

print("Después de crear:")
inspector = inspect(engine)  # Reinstancia para refrescar
print(inspector.get_table_names())
