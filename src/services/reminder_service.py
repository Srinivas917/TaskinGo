from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.entities.db_model import Goal, Task, User, SessionLocal
from src.utils.email_utils import send_email
from src.utils.logging_utils import get_logger

logger = get_logger(__name__, __file__, logging_level="DEBUG")


def send_daily_goal_reminders():
    """
    Sends daily reminders for goals:
    - Goal is older than 24 hours
    - Goal not deleted
    - Either never notified OR last notified > 24h ago
    """

    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        threshold_24h = now - timedelta(hours=24)

        goals = db.query(Goal).filter(
            Goal.is_deleted == False,
            Goal.created_at <= threshold_24h,
            (
                (Goal.notified_at.is_(None)) |
                (Goal.notified_at <= threshold_24h)
            )
        ).all()

        logger.info(f"Found {len(goals)} goals eligible for reminder")

        for goal in goals:

            try:
                user = db.query(User).filter(User.id == goal.user_id, User.is_deleted == False).first()
                if not user:
                    continue

                pending_tasks = db.query(Task).filter(
                    Task.goal_id == goal.id,
                    Task.is_completed == False,
                    Task.is_deleted == False
                ).all()

                subject = f"Daily Reminder: {goal.title}"

                if pending_tasks:
                    task_list = "\n".join(
                        [f"- {task.title}" for task in pending_tasks]
                    )

                    message = f"""
                    Hi {user.username},

                    Here's your daily progress reminder for:

                    Goal: {goal.title}

                    Pending Tasks:
                    {task_list}

                    Stay consistent. Small progress daily compounds massively.

                    Taskingo
                    """
                else:
                    message = f"""
                    Hi {user.username},

                    Great work!

                    You have no pending tasks for your goal:
                    {goal.title}

                    Keep maintaining your momentum!

                    Taskingo
                    """

                # Send Email
                send_email(user.email, subject, message)

                # Update notification timestamp
                goal.notified_at = now
                db.commit()

                logger.info(f"Reminder sent for goal {goal.id}")

            except Exception as e:
                db.rollback()
                logger.exception(f"Failed to send reminder for goal {goal.id}")
                continue
    except Exception as e:
        logger.exception(f"Failed to send reminders: {str(e)}")
        raise e
    finally:
        db.close()


def send_goal_created_notification(goal_id: int):
    """
    Sends immediate notification when a goal is created.
    Does NOT update notified_at.
    """
    db: Session = SessionLocal()

    try:
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.is_deleted == False
        ).first()

        if not goal:
            return None

        user = db.query(User).filter(User.id == goal.user_id).first()
        if not user:
            return None

        subject = f"Goal Created: {goal.title}"

        message = f"""
        Hi {user.username},

        Your new goal has been successfully created:

        Goal: {goal.title}

        Start taking action today.
        Small steps daily lead to massive results.

        Taskingo
        """

        try:
            send_email(user.email, subject, message)
            logger.info(f"Immediate goal creation email sent for goal {goal_id}")
        except Exception:
            logger.exception(f"Failed to send immediate notification for goal {goal_id}")

    except Exception as e:
        logger.exception(f"Failed to send immediate notification for goal {goal_id}")
        raise e
    finally:
        db.close()