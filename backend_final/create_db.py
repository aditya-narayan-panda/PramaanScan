from app.db.session import engine
from app.db.base import Base


def create_database():
    print("=" * 70)
    print("PRAMAANSCAN DATABASE INITIALIZATION")
    print("=" * 70)

    print()
    print("Database URL:")
    print(engine.url)

    print()
    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print()
    print("DATABASE INITIALIZED SUCCESSFULLY")
    print()
    print("Tables created:")

    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

    print()
    print("=" * 70)


if __name__ == "__main__":
    create_database()