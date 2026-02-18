from functools import wraps
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response
import time
from typing import Callable, Any

from src.entities.db_model import SessionLocal, engine
from src.utils.logging_utils import get_logger


logger = get_logger(__name__, __file__, logging_level="DEBUG")


async def db_session_middleware(request: Request, call_next) -> Response:
    """
    Manage database connection per request.
    
    Args:
        request: Incoming HTTP request object
        call_next: Next middleware or route handler in the chain

    Returns:
        Response object after processing request
        Ensures database session is attached to request state and properly closed
    """
    response = Response("Internal server error", status_code=500)
    db: Session = SessionLocal()
    try:
        request.state.db = db
        response = await call_next(request)
    finally:
        db.close()
    return response

def get_connection_pool_status() -> dict:
    """
    Get current connection pool status for monitoring
    
    Returns:
        Dictionary containing:
        - pool_size: Total size of connection pool
        - checked_out: Number of active connections
        - overflow: Number of overflow connections
        - error: Error message if retrieval fails.
    """
    try:
        # Access the connection pool attributes
        pool = engine.pool
        pool_info = {
            "pool_size": getattr(pool, "size", lambda: "Unknown")(),
            "checked_out": getattr(pool, "checkedout", lambda: "Unknown")(),
            "overflow": getattr(pool, "overflow", lambda: "Unknown")(),
        }


        return pool_info
    except Exception as e:
        logger.error(f"Failed to get connection pool status: {str(e)}")
        return {"error": str(e)}


def log_connection_pool_status():
    """Log current connection pool status for monitoring"""
    status = get_connection_pool_status()
    logger.info(f"Connection Pool Status: {status}")
