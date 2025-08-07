from database import init_db

if __name__ == "__main__":
    init_db()
    print("Base de datos creada correctamente.")

def init_db():
    from models import Project
    Base.metadata.create_all(bind=engine)
    print("Base de datos inicializada correctamente.")
