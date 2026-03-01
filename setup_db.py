from database import init_db, SessionLocal
from models import User, RoleEnum
from auth import hash_password

def setup():
    print("Initializing database...")
    init_db()
    
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("Creating default admin user...")
            hashed_password = hash_password("admin123")
            admin_user = User(
                username="admin",
                password_hash=hashed_password,
                role=RoleEnum.ADMIN
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created successfully (username: 'admin', password: 'admin123').")
        else:
            print("Admin user already exists.")
    except Exception as e:
        print(f"Error occurred during database setup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup()
