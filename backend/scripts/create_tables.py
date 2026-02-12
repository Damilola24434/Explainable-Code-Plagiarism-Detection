from app.core.db import engine, Base
import app.models.models  # IMPORTANT: this loads all table definitions

def main():
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")

if __name__ == "__main__":
    main()
