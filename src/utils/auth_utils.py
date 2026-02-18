from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import uuid

from src.constants.properties import ACCESS_TOKEN_EXPIRE_MINUTES, ACCESS_TOKEN_SECRET_KEY, ACCESS_TOKEN_ALGORITHM, \
    REFRESH_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_SECRET_KEY
from src.entities.db_model import User, SessionLocal
from src.utils.logging_utils import get_logger


logger = get_logger(__name__, __file__, logging_level="DEBUG")


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.

    Args:
        password: Plain text password string

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hashed password.

    Args:
        plain_password: User provided plain text password
        hashed_password: Stored hashed password

    Returns:
        Boolean indicating whether password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


# JWT Helpers
def create_access_token(data: dict):
    """
    Generate JWT access token.

    Args:
        data: Dictionary containing payload data

    Returns:
        Encoded JWT access token string with expiration claim
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, ACCESS_TOKEN_SECRET_KEY, algorithm=ACCESS_TOKEN_ALGORITHM)


def decode_access_token(token: str):
    """
    Decode and validate JWT access token.

    Args:
        token: Encoded JWT access token string.

    Returns:
        Decoded token payload dictionary.

    Raises:
        HTTPException (401) if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, ACCESS_TOKEN_SECRET_KEY, algorithms=[ACCESS_TOKEN_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    """
    Generate refresh token.

    Args:
        data: Dictionary containing payload data.
        expires_delta: Optional custom expiration timedelta.

    Returns:
        Encoded JWT refresh token string with expiration claim.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ACCESS_TOKEN_ALGORITHM)
    return encoded_jwt


def decode_refresh_token(token: str):
    """
    Decode and validate JWT refresh token.

    Args:
        token: Encoded JWT refresh token string.

    Returns:
        Decoded token payload dictionary.

    Raises:
        HTTPException (401) if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, REFRESH_TOKEN_SECRET_KEY, algorithms=[ACCESS_TOKEN_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Retrieve currently authenticated user from access token.

    Args:
        credentials: HTTP authorization credentials containing bearer token.

    Returns:
        User object if token is valid and user exists.

    Raises:
        HTTPException (401) if token is invalid or user not found.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    db: Session = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.id == user_id, User.is_deleted == False)
            .first()
        )
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except:
        raise
    finally:
        db.close()


def create_user(user_creds):
    """
    Create new users in database if they do not already exist.

    Args:
        user_creds: List of dictionaries containing user credentials
    """
    db: Session = SessionLocal()
    try:
        for user_info in user_creds:
            user = (
                db.query(User)
                .filter(User.username == user_info.get("username"), User.is_deleted == False)
                .first()
            )
            if not user:
                user = User(
                    id=str(uuid.uuid4()),
                    username=user_info.get("username"),
                    email=user_info.get("email"),
                    hashed_password=hash_password(user_info.get("password")),
                )
                db.add(user)
        db.commit()
    finally:
        db.close()