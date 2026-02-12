from sqlalchemy import text
from app.core.db import engine

def main():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)).fetchall()

        print("Tables in public schema:")
        for r in rows:
            print("-", r[0])

if __name__ == "__main__":
    main()
