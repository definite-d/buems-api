from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Query
from loguru import logger
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select
from sqlmodel.sql.expression import Select

from ..db import (
    ExeatRequest,
    ExeatRequestStatusEnum,
    SecurityOperative,
    db_dependency,
    get_exeat_request,
)
from .auth import get_current_security_operative
from .common import (
    ExeatRequestResponse,
    PaginatedExeatsResponse,
    error_exeat_request_not_found,
    paginated_exeats_query,
)

title = "Security Operative"
router = APIRouter(
    prefix="/security",
    tags=[title],
    dependencies=[Depends(get_current_security_operative)],
    responses={404: {"description": "Not found"}},
)


@router.get("/exeat", response_model=PaginatedExeatsResponse)
async def get_exeats(
    db: Annotated[Session, Depends(db_dependency)],
    security_operative: Annotated[
        SecurityOperative, Depends(get_current_security_operative)
    ],
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
) -> PaginatedExeatsResponse:
    """
    Retrieve all approved exeat requests. Only accessible to security operatives.
    Only approved requests are visible, by Least Responsibility Principle.
    """
    logger.info(
        f"Fetching approved exeat requests for security operative ID {security_operative.id}"
    )
    return paginated_exeats_query(
        db,
        page=page,
        page_size=page_size,
        status_id=ExeatRequestStatusEnum.APPROVED,
        sort=sort,
        ascending=ascending,
    )


# noinspection PyUnusedLocal
@router.get("/exeat/{exeat_id}", response_model=ExeatRequestResponse)
async def get_exeat(
    db: Annotated[Session, Depends(db_dependency)],
    exeat_id: int,
    security_operative: Annotated[
        SecurityOperative, Depends(get_current_security_operative)
    ],
):
    """
    Retrieve an exeat request by ID. Only accessible to security operatives.
    """
    # This is the most permissive variant of this endpoint, as security operatives
    #  must be able to view all exeat requests.
    # noinspection PyTypeChecker,Pydantic
    query: Select[ExeatRequest] = select(ExeatRequest).where(
        ExeatRequest.id == exeat_id
    )
    try:
        return db.exec(query).one()
    except NoResultFound:
        logger.error("Exeat request with ID {} not found", exeat_id)
        raise error_exeat_request_not_found
