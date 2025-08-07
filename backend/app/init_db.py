# backend/app/init_db.py

from .database import engine, Base
from .models import Plaza, Incidente, Sustitucion

def initialize_database():
    """
    Connects to the database and creates all tables
    based on the models defined.
    """
    print("Connecting to the database to create tables...")
    try:
        # This command creates all tables that inherit from Base
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully (if they didn't exist).")
    except Exception as e:
        print(f"❌ An error occurred while creating tables: {e}")

if __name__ == "__main__":
    initialize_database()