import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bcrypt
from core.config import settings
from models.sql_models import Admin, AdminRoleEnum, AdminStatusEnum, USERTYPE
from models.sql_models.base_model import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_super_admin():
    """
    Create a super admin user if one doesn't exist.
    Uses credentials from environment variables.
    """
    try:
        # Create database session
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Get credentials from settings
        email = settings.SUPER_ADMIN_EMAIL
        password = settings.SUPER_ADMIN_PASSWORD
        first_name = settings.SUPER_ADMIN_FIRST_NAME
        last_name = settings.SUPER_ADMIN_LAST_NAME

        if not email or not password:
            logger.error("SUPER_ADMIN_EMAIL or SUPER_ADMIN_PASSWORD not set in .env")
            return

        # Check if admin already exists
        existing_admin = db.query(Admin).filter(Admin.email == email).first()
        if existing_admin:
            logger.info(f"Admin with email {email} already exists.")
            return

        logger.info(f"Creating super admin: {email}")

        # Create new admin
        new_admin = Admin(
            email=email,
            hashed_password=get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            role=AdminRoleEnum.SUPER_ADMIN,
            status=AdminStatusEnum.ACTIVE,
            is_active=True,
            security_key=os.urandom(16).hex()
        )

        db.add(new_admin)
        db.commit()
        logger.info("Successfully created super admin user!")

    except Exception as e:
        logger.error(f"Error creating super admin: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()
