from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from fastapi.params import Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select
from sqlmodel.sql.expression import Select

from ..db import ExeatRequest, ExeatRequestStatusEnum, Student, User, db_dependency
from .auth import get_current_student
from .common import (
    ExeatRequestResponse,
    PaginatedExeatsResponse,
    error_exeat_request_not_found,
    paginated_exeats_query,
)

title = "Student"
router = APIRouter(prefix="/student", tags=[title])


class ExeatRequestCreate(BaseModel):
    leave_start: datetime = Field(
        ..., description="Start date and time for the leave request"
    )
    leave_end: datetime = Field(
        ..., description="End date and time for the leave request"
    )
    reason: str = Field(..., max_length=255, description="Reason for the leave request")


@router.get("/exeat", response_model=PaginatedExeatsResponse)
async def get_exeats(
    db: Annotated[Session, Depends(db_dependency)],
    student: Annotated[Student, Depends(get_current_student)],
    page: Annotated[
        int,
        Query(
            ge=1,
            description="The page number to fetch. If the provided value exceeds the possible number of pages, the last page will be returned",
        ),
    ] = 1,  # Page number, default to 1
    page_size: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="The number of items per page. If the provided value exceeds the maximum, "
            "the maximum value will be used",
        ),
    ] = 20,  # Page size, default to 20, max 100
    _status: Annotated[
        f"{ExeatRequestStatusEnum.type_string} | None",
        Query(
            alias="status",
            description="The approval status of the exeats to be returned.",
        ),
    ] = None,
    sort: Annotated[
        Literal["last_updated", "leave_start", "leave_end"],
        Query(
            description="The attribute to sort by. May be one of `last_updated` (default), `leave_start` or `leave_end`."
        ),
    ] = "last_updated",
    ascending: Annotated[
        bool,
        Query(
            description="Whether or not to sort in ascending order. Defaults to `False` (descending order)."
        ),
    ] = False,
):
    """
    Retrieve all exeat requests submitted by the logged-in student, filtered by status and sorted.
    """
    logger.info(f"Fetching pending exeat requests for student ID {student.id}")
    # Retrieve exeat requests for the student
    # noinspection PyTypeChecker,Pydantic
    query: Select[ExeatRequest] = select(ExeatRequest).where(
        ExeatRequest.student_id == student.id
    )
    _status = ExeatRequestStatusEnum.from_safe_name(_status) if _status else None
    return paginated_exeats_query(
        db,
        query,
        page=page,
        page_size=page_size,
        status_id=_status,
        sort=sort,
        ascending=ascending,
    )


@router.get("/exeat/{exeat_id}", response_model=ExeatRequestResponse)
async def get_exeat(
    exeat_id: int,
    db: Annotated[Session, Depends(db_dependency)],
    current_student: Annotated[User, Depends(get_current_student)],
):
    """
    Retrieve a specific exeat request submitted by the logged-in student by its ID.
    """
    logger.info(
        f"Fetching exeat request with ID {exeat_id} for student ID {current_student.id}"
    )
    # noinspection PyTypeChecker,Pydantic
    query: Select[ExeatRequest] = select(ExeatRequest).where(
        ExeatRequest.student_id == current_student.id,
        ExeatRequest.id == exeat_id,
    )
    try:
        return db.exec(query).one()
    except NoResultFound:
        logger.error("Exeat request with ID {} not found", exeat_id)
        raise error_exeat_request_not_found


@router.post(
    "/submit",
    response_model=ExeatRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_exeat_request(
    exeat_request: ExeatRequestCreate,
    db: Annotated[Session, Depends(db_dependency)],
    current_student: Annotated[Student, Depends(get_current_student)],
):
    """
    Allows students to submit a new exeat request.
    """
    # Create the new exeat request
    new_exeat_request = ExeatRequest(
        student_id=current_student.id,
        leave_start=exeat_request.leave_start,
        leave_end=exeat_request.leave_end,
        reason=exeat_request.reason,
        status_id=ExeatRequestStatusEnum.PENDING,  # Initial status as pending
        submission_time=datetime.now(UTC),
    )

    # Add to the database and commit
    db.add(new_exeat_request)
    db.commit()
    db.refresh(new_exeat_request)

    logger.info(
        f"Student {current_student.id} submitted a new exeat request with ID {new_exeat_request.id}."
    )
    return new_exeat_request
