from datetime import datetime
from enum import IntEnum
from typing import List, Optional

from sqlalchemy.sql.functions import now
from sqlmodel import Field, Relationship, SQLModel


class UserTypeEnum(IntEnum):
    ADMIN = 1
    STUDENT = 2
    STAFF = 3
    SECURITY_OPERATIVE = 4

    @property
    def safe_name(self):
        return self.name.lower()

    @classmethod
    @property
    def type_string(cls):
        _names = ", ".join(
            f'"{user_type.safe_name}"' for user_type in cls if user_type != cls.ADMIN
        )
        return f"Literal[{_names}]"

    @classmethod
    def from_safe_name(cls, name):
        return cls[name.upper()]


class ExeatRequestStatusEnum(IntEnum):
    PENDING = 1
    APPROVED = 2
    DENIED = 3

    @property
    def safe_name(self):
        return self.name.lower()

    @classmethod
    @property
    def type_string(cls):
        _names = ", ".join(f'"{user_type.safe_name}"' for user_type in cls)
        return f"Literal[{_names}]"

    @classmethod
    def from_safe_name(cls, name):
        return cls[name.upper()]


class UserType(SQLModel, table=True):
    """
    Reference table for the types of users which exist within the system.
    """

    __tablename__ = "user_type"

    id: int = Field(default=None, primary_key=True)
    type_name: str = Field(unique=True, index=True)


class RevokedToken(SQLModel, table=True):
    """
    For storing revoked JWTs.
    """

    __tablename__ = "revoked_token"

    sig: str = Field(
        primary_key=True, index=True, unique=True
    )  # Primary key: Signature of the JWT
    exp: datetime = Field(..., index=True)  # Store expiration timestamp


class ExeatRequestStatus(SQLModel, table=True):
    """
    Reference table for the status of exeat requests within the system.
    """

    __tablename__ = "exeat_request_status"

    id: int = Field(default=None, primary_key=True)
    status_name: str = Field(unique=True, index=True)


class User(SQLModel, table=True):
    """
    User model for the system.
    """

    __tablename__ = "user"

    id: int = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(unique=True, index=True)
    phone_number: str
    hashed_password: bytes
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    user_type_id: int = Field(
        foreign_key="user_type.id", index=True
    )  # References user_type table
    profile_picture_id: str | None = None
    time_joined: datetime = Field(default_factory=now)


class Guardian(SQLModel, table=True):
    """
    Guardian profile model. Attached to a single student.
    """

    __tablename__ = "guardian"

    id: int = Field(default=None, primary_key=True)
    name: str
    phone_number: str

    students: list["Student"] = Relationship(back_populates="guardian")


class Student(SQLModel, table=True):
    """
    Student profile model. Attached to a single user.
    """

    __tablename__ = "student"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    matriculation_number: str = Field(index=True)
    course_of_study: str

    guardian_id: int = Field(foreign_key="guardian.id", index=True)
    guardian_relationship: str

    requested_exeats: List["ExeatRequest"] = Relationship(
        back_populates="requesting_student",
    )
    guardian: "Guardian" = Relationship(back_populates="students")


class Staff(SQLModel, table=True):
    """
    Staff profile model. Attached to a single user.
    The staff are responsible for granting or denying exeat requests, and thus have a relationship of
    """

    __tablename__ = "staff"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    staff_id: str = Field(index=True)
    designation: str

    addressed_exeats: List["ExeatRequest"] = Relationship(
        back_populates="reviewing_staff",
    )


class SecurityOperative(SQLModel, table=True):
    """
    Security Operative profile model. Attached to a single user.
    """

    __tablename__ = "security_operative"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    security_id: str = Field(index=True)
    designation: str


class ExeatRequest(SQLModel, table=True):
    """
    The ExeatRequest model for the system. Contains the details of the exeat request.
    """

    __tablename__ = "exeat_request"

    id: int = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id", index=True)
    leave_start: datetime
    leave_end: datetime
    submission_time: datetime = Field(default_factory=now)
    reason: str
    status_id: int = Field(foreign_key="exeat_request_status.id", index=True)
    staff_id: int | None = Field(default=None, foreign_key="staff.id", index=True)
    staff_review_time: datetime | None = None
    staff_comment: str | None = None

    # Relationships
    requesting_student: "Student" = Relationship(back_populates="requested_exeats")
    reviewing_staff: "Staff" = Relationship(back_populates="addressed_exeats")
