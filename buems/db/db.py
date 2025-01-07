from typing import Any

from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

from ..constants import env
from .models import ExeatRequestStatus, ExeatRequestStatusEnum, UserType, UserTypeEnum

engine = create_engine(env.DB_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

sessionmaker_instance: sessionmaker[Session | Any] = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


async def db_dependency() -> sessionmaker[Session]:
    with sessionmaker_instance() as db:
        yield db


usertypes = (UserType(id=v.value, type_name=v.safe_name) for v in UserTypeEnum)
statuses = (
    ExeatRequestStatus(id=v.value, status_name=v.safe_name)
    for v in ExeatRequestStatusEnum
)


def init_db():
    SQLModel.metadata.create_all(engine)
    with sessionmaker_instance() as db:
        for instance in (*usertypes, *statuses):
            db.merge(instance)
        db.commit()
