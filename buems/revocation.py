from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from sqlalchemy.orm import Query, Session

from .constants import ACCESS_TOKEN_EXPIRE_MINUTES
from .db import RevokedToken
from .db.db import sessionmaker_instance


def revoke_jwt(db: Session, jwt: str, exp: int):
    """
    Revoke a JWT by storing its signature and expiration time.
    """
    sig = jwt.rsplit(".", 1)[1]
    exp = datetime.fromtimestamp(exp, UTC)
    revoked_token_entry = RevokedToken(sig=sig, exp=exp)
    db.merge(revoked_token_entry)
    db.commit()


def is_jwt_revoked(db: Session, jwt: str) -> bool:
    """Check if a JWT is revoked."""
    sig = jwt.rsplit(".", 1)[1]
    # noinspection PyTypeChecker,Pydantic
    revoked_token: RevokedToken | None = db.get(RevokedToken, sig)
    return revoked_token is not None


def cleanup_expired_revoked_tokens():
    with sessionmaker_instance() as db:
        now = datetime.now(UTC)
        # noinspection PyTypeChecker,Pydantic
        tokens: Query[RevokedToken] = db.query(RevokedToken).where(
            RevokedToken.exp < now
        )
        if tokens.one_or_none():
            tokens.delete()
            db.commit()
            logger.info("Expired tokens cleaned up.")


def init_revocation_scheduler():
    scheduler = BackgroundScheduler()

    # Run cleanup periodically.
    scheduler.add_job(
        cleanup_expired_revoked_tokens,
        "interval",
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    scheduler.start()
