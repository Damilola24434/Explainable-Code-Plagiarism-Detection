from sqlalchemy import text
from app.core.db import engine

def main():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1;"))
        print("DB connected. SELECT 1 returned:", result.scalar())

if __name__ == "__main__":
    main()
