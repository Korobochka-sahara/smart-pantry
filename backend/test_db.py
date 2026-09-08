from app.db.database import engine


try:
    with engine.connect() as connection:
        print("Database connection: OK")
except Exception as e:
    print("Database connection: FAILED")
    print(e)