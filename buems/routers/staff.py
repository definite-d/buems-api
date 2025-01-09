from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, or_, select
from sqlmodel.sql.expression import Select

from ..db import (
    ExeatRequest,
    ExeatRequestStatusEnum,
    Staff,
    db_dependency,
    get_exeat_request,
)
from .auth import get_current_staff
from .common import (
    ExeatRequestResponse,
    PaginatedExeatsResponse,
    error_exeat_request_not_found,
    paginated_exeats_query,
)

title = "Staff"
router = APIRouter(
    prefix="/staff", tags=[title], dependencies=[Depends(get_current_staff)]
)


@router.get("/exeat", response_model=PaginatedExeatsResponse)
async def get_exeats(
    db: Annotated[Session, Depends(db_dependency)],
    staff: Annotated[Staff, Depends(get_current_staff)],
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
        str,
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

    Only the exeats concerning the currently logged in staff are returned
    (i.e. all pending, and only specific exeats approved or denied by the staff).
    """
    logger.info(f"Fetching pending exeat requests for staff ID {staff.id}")
    # noinspection PyTypeChecker,Pydantic,PyComparisonWithNone
    query: Select[ExeatRequest] = select(ExeatRequest).where(
        or_(ExeatRequest.staff_id == staff.id, ExeatRequest.staff_id == None)
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


# noinspection PyUnusedLocal
@router.get("/exeat/{exeat_id}", response_model=ExeatRequestResponse)
async def get_exeat(
    db: Annotated[Session, Depends(db_dependency)],
    exeat_id: int,
    staff: Annotated[Staff, Depends(get_current_staff)],
):
    """
    Retrieve an exeat request by ID. Only accessible to staff.

    Only the exeats concerning the currently logged in staff are returned
    (i.e. all pending, and only specific approved or denied exeats).
    """
    # noinspection PyTypeChecker,Pydantic,PyComparisonWithNone
    query: Select[ExeatRequest] = (
        select(ExeatRequest)
        .where(ExeatRequest.id == exeat_id)
        .where(or_(ExeatRequest.staff_id == staff.id, ExeatRequest.staff_id == None))
    )
    try:
        return db.exec(query).one()
    except NoResultFound:
        logger.error("Exeat request with ID {} not found", exeat_id)
        raise error_exeat_request_not_found


@router.post("/approve/{exeat_id}", response_model=ExeatRequestResponse)
def approve_exeat_request(
    db: Annotated[Session, Depends(db_dependency)],
    staff: Annotated[Staff, Depends(get_current_staff)],
    exeat_id: int,
    comment: str | None = None,
):
    """
    Approve a pending exeat request and add an optional comment.
    """
    exeat_request = get_exeat_request(db, exeat_id)
    if not exeat_request:
        logger.error(f"Exeat request ID {exeat_id} not found for approval.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exeat request not found"
        )

    if exeat_request.status_id != ExeatRequestStatusEnum.PENDING:
        logger.warning(f"Exeat request ID {exeat_id} is not pending.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending"
        )

    # Update status to APPROVED
    exeat_request.status_id = ExeatRequestStatusEnum.APPROVED
    exeat_request.staff_id = staff.id
    exeat_request.staff_comment = comment
    exeat_request.staff_review_time = datetime.now(UTC)

    db.merge(exeat_request)
    db.commit()
    db.refresh(exeat_request)

    logger.info(f"Exeat request ID {exeat_id} approved by staff ID {staff.id}")
    return exeat_request


@router.post("/deny/{exeat_id}", response_model=ExeatRequestResponse)
def deny_exeat_request(
    db: Annotated[Session, Depends(db_dependency)],
    staff: Annotated[Staff, Depends(get_current_staff)],
    exeat_id: int,
    comment: str | None = None,
):
    """
    Deny a pending exeat request and add an optional comment.
    """
    exeat_request = get_exeat_request(db, exeat_id)
    if not exeat_request:
        logger.error(f"Exeat request ID {exeat_id} not found for denial.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exeat request not found"
        )

    if exeat_request.status_id != ExeatRequestStatusEnum.PENDING:
        logger.warning(f"Exeat request ID {exeat_id} is not pending.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending"
        )

    # Update status to DENIED
    exeat_request.status_id = ExeatRequestStatusEnum.DENIED
    exeat_request.staff_id = staff.id
    exeat_request.staff_comment = comment
    exeat_request.staff_review_time = datetime.now(UTC)

    db.merge(exeat_request)
    db.commit()
    db.refresh(exeat_request)

    logger.info(f"Exeat request ID {exeat_id} denied by staff ID {staff.id}")
    return exeat_request
