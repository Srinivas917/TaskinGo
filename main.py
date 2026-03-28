import warnings
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends
from langchain_core._api.deprecation import LangChainDeprecationWarning
from apscheduler.schedulers.background import BackgroundScheduler
from src.services.reminder_service import send_daily_goal_reminders

from src.apis import auth_router, goal_router, task_router, notes_router, insight_router
from src.entities.db_model import engine
from src.utils.db_utils import db_session_middleware, log_connection_pool_status
from src.utils.logging_utils import get_logger

warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
logger = get_logger(__name__, __file__, logging_level="DEBUG")

scheduler = BackgroundScheduler()

def daily_reminder_job():
    try:
        logger.info("Running daily reminder job...")
        send_daily_goal_reminders()
    except Exception as e:
        logger.exception("Daily reminder job failed.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown lifecycle.

    Args:
        app: FastAPI application instance

    Returns:
        Async context manager that:
        - On startup:
            - Verifies database connectivity
            - Logs connection pool status
        - On shutdown:
            - Disposes database engine connections
    """
    # --- Startup ---
    logger.info("Starting up application...")
    try:
        # Touch engine to ensure DB connectivity
        with engine.connect() as conn:
            pass
        logger.info("Database connection established")
        log_connection_pool_status()
        logger.info("Database initialization completed successfully")
        scheduler.add_job(
            daily_reminder_job,
            trigger="cron",
            hour=11,
            minute=0,
            id="daily_goal_reminder",
            replace_existing=True
        )

        scheduler.start()
        logger.info("Scheduler started successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

    # Yield control back to FastAPI
    yield

    # --- Shutdown ---
    logger.info("Shutting down application...")
    try:
        scheduler.shutdown()
        logger.info("Scheduler stopped successfully.")

        engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error during database cleanup: {str(e)}")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def home():
    """Read Route for API health check"""
    return {"Message": "API Reached..!"}


app.include_router(auth_router.router)
app.include_router(goal_router.router)
app.include_router(insight_router.router)
app.include_router(task_router.router)
app.include_router(notes_router.router)

if __name__ == "__main__":
    uvicorn.run(app, port=9000)
