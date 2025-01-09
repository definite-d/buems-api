from collections.abc import Iterable
from datetime import datetime
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlmodel import Session, asc, desc, func, or_, select
from sqlmodel.sql.expression import Select
from starlette import status

from ..db import ExeatRequest, ExeatRequestStatusEnum

error_exeat_request_not_found = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Exeat request not found"
)


class ExeatRequestResponse(BaseModel):
    id: int
    leave_start: datetime
    leave_end: datetime
    submission_time: datetime
    reason: str
    status: str = (
        ExeatRequestStatusEnum.PENDING.safe_name
    )
    staff_comment: str | None = None
    staff_date: datetime | None = (
        None  # Date the request was approved or denied, if applicable
    )

    @model_validator(mode="before")
    def validate_status(cls, values: dict[str, ...] | ExeatRequest):
        if isinstance(values, ExeatRequest):
            values = values.model_dump()
            values["status"] = ExeatRequestStatusEnum(values["status_id"]).safe_name
        elif isinstance(values, dict):
            status_id = values.pop("status_id", None)
            if status_id is not None:
                values["status"] = ExeatRequestStatusEnum(status_id).safe_name
        return values


class PaginatedExeatsResponse(BaseModel):
    total_items: int = Field(examples=[109])
    total_pages: int = Field(examples=[11])
    page_size: int = Field(examples=[2])
    current_page: int = Field(examples=[1])
    items: Iterable[ExeatRequestResponse] = Field(
        examples=[
            [
                ExeatRequestResponse(
                    id=23,
                    leave_start=datetime(2023, 6, 14),
                    leave_end=datetime(2023, 7, 2),
                    submission_time=datetime(2023, 1, 1),
                    reason="Vacation",
                    status=ExeatRequestStatusEnum.APPROVED.safe_name,
                    staff_comment=None,
                    staff_date=None,
                ),
                ExeatRequestResponse(
                    id=82,
                    leave_start=datetime(2023, 8, 12),
                    leave_end=datetime(2023, 8, 15),
                    submission_time=datetime(2023, 8, 11),
                    reason="Urgent family emergency",
                    status=ExeatRequestStatusEnum.APPROVED.safe_name,
                    staff_comment=None,
                    staff_date=None,
                ),
            ]
        ]
    )


def paginated_exeats_query(
    db: Session,
    query: Select[ExeatRequest] = select(ExeatRequest),
    page: int = 1,
    page_size: int = 20,
    status_id: ExeatRequestStatusEnum | None = None,
    sort: Literal["last_updated", "leave_start", "leave_end"] = "last_updated",
    ascending: bool = False,
) -> PaginatedExeatsResponse:
    # Filter by status
    if status_id:
        # noinspection Pydantic
        query = query.where(ExeatRequest.status_id == status_id)

    # Sort
    sort_func = asc if ascending else desc
    match sort:
        case "last_updated":
            # noinspection Pydantic,PyTypeChecker
            query = query.order_by(
                sort_func(
                    or_(ExeatRequest.staff_review_time, ExeatRequest.submission_time)
                )
            )
        case "leave_start":
            # noinspection Pydantic
            query = query.order_by(sort_func(ExeatRequest.leave_start))
        case "leave_end":
            # noinspection Pydantic
            query = query.order_by(sort_func(ExeatRequest.leave_end))

    # Get the total count of exeats for the query.
    total_items: int = db.scalar(func.count(query.c.id))

    # Pagination calculations.
    total_pages: int = int((total_items + page_size - 1) // page_size)
    page: int = min(page, total_pages)
    start: int = (page - 1) * page_size

    # Apply pagination to the query
    items: Iterable[dict] = (
        value for value in db.exec(query.offset(start).limit(page_size)).all()
    )

    return PaginatedExeatsResponse(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
        items=items,
    )
