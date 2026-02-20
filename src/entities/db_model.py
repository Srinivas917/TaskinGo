import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from src.constants.properties import DATABASE_URL
from src.utils.logging_utils import get_logger

logger = get_logger(__name__, __file__, logging_level="DEBUG")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now)
    is_deleted = Column(Boolean, default=False)

    goals = relationship("Goal", back_populates="user")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    priority = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now)
    is_completed = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    user = relationship("User", back_populates="goals")
    tasks = relationship("Task", back_populates="goal")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500))
    priority = Column(String(50))
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    is_deleted = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now)

    goal = relationship("Goal", back_populates="tasks")

def initialize_db():
    """Initialize database connection and create tables"""
    try:
        logger.info("Initializing database connection...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


initialize_db()
