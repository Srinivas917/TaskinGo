import uuid
from sqlalchemy.orm import Session

from src.entities.db_model import SessionLocal, User
from src.utils.auth_utils import hash_password
from src.utils.logging_utils import get_logger

logger = get_logger(__name__, __file__, logging_level="INFO")


COMMON_PASSWORD = "Password@123"  # Same password for all users


def seed_users():
    """
    Seed 10 users with same password.
    Avoid duplicates if users already exist.
    """

    db: Session = SessionLocal()

    try:
        logger.info("Starting user seeding...")

        # Hash password ONCE
        hashed_pwd = hash_password(COMMON_PASSWORD)

        for i in range(1, 11):
            username = f"user{i}"
            email = f"user{i}@example.com"

            existing_user = (
                db.query(User)
                .filter(User.username == username, User.is_deleted == False)
                .first()
            )

            if existing_user:
                logger.info(f"{username} already exists. Skipping.")
                continue

            user = User(
                username=username,
                email=email,
                password_hash=hashed_pwd,
            )

            db.add(user)
            logger.info(f"Created {username}")

        db.commit()
        logger.info("User seeding completed successfully!")

    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()