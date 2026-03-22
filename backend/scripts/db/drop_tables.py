from app.core.db import engine, Base
import app.models.models  # IMPORTANT: this loads all table definitions

def main():
    # Drop all tables in reverse order to handle foreign keys
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped successfully.")

if __name__ == "__main__":
    main()