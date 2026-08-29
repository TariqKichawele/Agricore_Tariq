import logging

from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import User, UserRole

logger = logging.getLogger(__name__)


def ensure_bootstrap_admin(db: Session) -> None:
    email = settings.BOOTSTRAP_ADMIN_EMAIL.lower()
    try:
        existing = db.scalar(select(User).where(User.email == email))
    except ProgrammingError:
        db.rollback()
        logger.warning("users table missing — run: cd backend && alembic upgrade head")
        return

    if existing is not None:
        return

    admin = User(
        email=email,
        hashed_password=hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD),
        full_name=settings.BOOTSTRAP_ADMIN_NAME,
        role=UserRole.ADMIN,
        farm_id=None,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    logger.info("Created bootstrap admin %s", email)
