from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal, Self  # noqa

from bcrypt import checkpw, gensalt, hashpw
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import PyJWTError, decode, encode
from loguru import logger
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ValidationError,
    field_validator,
    SecretStr,
    model_validator,
)
from pydantic_core import PydanticCustomError
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from ..constants import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    PROFILE_PICTURE_PATH,
    STATIC_PATH,
    env,
)
from ..db import SecurityOperative, Staff, Student, User, UserTypeEnum, db_dependency
from ..db.models import Guardian
from ..revocation import is_jwt_revoked, revoke_jwt

SECRET_KEY = env.SECRET_KEY
ALGORITHM = "HS256"
error_invalid_credentials = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated.",
    headers={"WWW-Authenticate": "Bearer"},
)


def verify_password(plain_password: str, hashed_password: bytes):
    return checkpw(plain_password.encode("utf-8"), hashed_password)


def get_password_hash(password: str):
    return hashpw(password.encode("utf-8"), gensalt())


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    iat = datetime.now(UTC)
    if expires_delta:
        expire = iat + expires_delta
    else:
        expire = iat + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": iat})
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


title = "Authentication"
router = APIRouter(tags=[title])


# Error message for unauthorized profile type
PROFILE_UNAUTHORIZED = "User profile type does not have access to this resource."


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class UpdateUserInfo(BaseModel):
    first_name: str | None = Field(None, description="The user's first name.")
    last_name: str | None = Field(None, description="The user's last name.")
    email: EmailStr | None = Field(None, description="The user's email address.")


class ChangePassword(BaseModel):
    old_password: SecretStr = Field(
        ..., description="The password currently on the account."
    )
    new_password: SecretStr = Field(..., description="The new password to change to.")


class UserCreate(BaseModel):
    """
    Schema for creating a new user, including fields for optional profiles
    based on user type (Student, Staff, or SecurityOperative).
    """

    user_type: UserTypeEnum.type_string = Field(..., description="The user's type.")
    email: EmailStr = Field(..., description="The user's email address.")
    password: SecretStr = Field(..., description="The password chosen by the user.")
    first_name: str = Field(..., description="The user's first name.")
    last_name: str = Field(..., description="The user's last name.")
    phone_number: str = Field(..., description="The phone number of the user.")
    is_active: bool = Field(True, description="Whether the user is active.")
    is_verified: bool = Field(
        False, description="Whether the user's information is verified."
    )

    # Student-specific fields
    matriculation_number: str | None = Field(
        None,
        description="The matriculation number of the `student`. Mandatory for `student`s.",
    )
    course_of_study: str | None = Field(
        None, description="The `student`'s course of study. Mandatory for `student`s."
    )
    guardian_name: str | None = Field(
        None,
        description="The name of the `student`'s guardian. Mandatory for `student`s.",
    )
    guardian_phone_number: str | None = Field(
        None,
        description="The phone number of the `student`'s guardian. Mandatory for `student`s.",
    )
    guardian_relationship: str | None = Field(
        None,
        description='The relationship between the `student` and their guardian, e.g. `"Mother"`. Mandatory for `student`s.',
    )

    # Staff-specific fields
    staff_id: str | None = Field(
        None, description="The ID number of the `staff`. Mandatory for `staff`."
    )
    designation: str | None = Field(
        None,
        description="The designation assigned to the `staff` or `security_operative`. Mandatory for `staff` and `security_operatives`.",
    )

    # Security Operative-specific fields
    security_id: str | None = Field(
        None,
        description="The ID of the `security_operative`. Mandatory for `security_operatives`",
    )

    def _unset_check(self, fields: set[str]):
        unset = fields.difference(self.model_fields_set)
        if unset:
            raise PydanticCustomError(
                "missing_fields",
                "Missing some required fields for the {user_type} user_type: {unset}",
                {"user_type": self.user_type, "unset": ", ".join(unset)}
            )

    @model_validator(mode="after")
    def validate_based_on_user_type(self) -> Self:
        match self.user_type:
            case UserTypeEnum.STUDENT.safe_name:
                self._unset_check(
                    {
                        "matriculation_number",
                        "course_of_study",
                        "guardian_name",
                        "guardian_phone_number",
                        "guardian_relationship",
                    }
                )
            case UserTypeEnum.STAFF.safe_name:
                self._unset_check({"staff_id", "designation"})
            case UserTypeEnum.SECURITY_OPERATIVE.safe_name:
                self._unset_check({"security_id", "designation"})
        return self


class UserResponse(BaseModel):
    """
    Schema for the response after creating or retrieving a user,
    displaying basic user information.
    """

    first_name: str
    last_name: str
    email: str
    user_type: str
    is_active: bool
    is_verified: bool
    profile_picture: str | None = Field(validation_alias="profile_picture_id")
    time_joined: datetime = datetime.now(UTC)

    @field_validator("profile_picture")
    def set_profile_picture(cls, value):
        if value:
            value = (
                STATIC_PATH.stem
                + "/"
                + str(
                    (PROFILE_PICTURE_PATH / value).relative_to(STATIC_PATH).as_posix()
                )
                + ".webp"
            )
        return value


class Email(BaseModel):
    email: EmailStr


class MatriculationNumber(BaseModel):
    matriculation_number: str = Field(pattern=r"^\d{4}/\d{4,5}$")


def decoded_token(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    try:
        return decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        raise error_invalid_credentials


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    token_payload: Annotated[dict[str, ...], Depends(decoded_token)],
    db: Annotated[Session, Depends(db_dependency)],
):
    if is_jwt_revoked(db, token):
        raise error_invalid_credentials
    email: str = token_payload.get("sub")
    iat: datetime = datetime.fromtimestamp(token_payload.get("iat"))
    if email is None:
        raise error_invalid_credentials
    # noinspection PyTypeChecker,Pydantic
    user: User | None = db.query(User).where(User.email == email).first()
    if user is None:
        raise error_invalid_credentials
    if user.time_joined > iat:
        raise error_invalid_credentials
    return user


def get_current_student(
    db: Annotated[Session, Depends(db_dependency)],
    user: Annotated[User, Depends(get_current_user)],
) -> Student:
    """
    Dependency that verifies the current user is a Student.
    """
    # noinspection PyTypeChecker,Pydantic
    student = db.query(Student).where(Student.user_id == user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=PROFILE_UNAUTHORIZED
        )
    return student


def get_current_staff(
    db: Annotated[Session, Depends(db_dependency)],
    user: Annotated[User, Depends(get_current_user)],
) -> Staff:
    """
    Dependency that verifies the current user is a Staff member.
    """
    # noinspection PyTypeChecker,Pydantic
    staff = db.query(Staff).where(Staff.user_id == user.id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=PROFILE_UNAUTHORIZED
        )
    return staff


def get_current_security_operative(
    db: Annotated[Session, Depends(db_dependency)],
    user: Annotated[User, Depends(get_current_user)],
) -> SecurityOperative:
    """
    Dependency that verifies the current user is a Security Operative.
    """
    # noinspection PyTypeChecker,Pydantic
    security_operative = (
        db.query(SecurityOperative).where(SecurityOperative.user_id == user.id).first()
    )
    if not security_operative:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=PROFILE_UNAUTHORIZED
        )
    return security_operative


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """
    Authenticate a user using either their email.

    :param db: Database session instance.
    :param email: Email of the user.
    :param password: Password of the user.
    :return: User object if authentication is successful, otherwise None.
    """
    logger.info('Authenticating user with email "{}"', email)
    try:
        # noinspection PyTypeChecker
        Email(email=email)
    except ValidationError:
        return None
    # noinspection PyTypeChecker,Pydantic
    user = db.query(User).where(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/token", response_model=Token)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(db_dependency)],
):
    """
    Login a user to get an access token.

    The username is the user's email address.
    """
    user = authenticate_user(db, form.username, form.password)
    if not user:
        logger.warning('Invalid login attempt for username "{}"', form.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": user.email})
    logger.info(f"User {user.email} logged in successfully")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    db: Annotated[Session, Depends(db_dependency)],
    token: Annotated[str, Depends(oauth2_scheme)],
    token_payload: Annotated[dict[str, ...], Depends(decoded_token)],
):
    """
    Logout a user by revoking the access token supplied.
    """
    revoke_jwt(db, jwt=token, exp=token_payload["exp"])
    logger.info("User logged out")


@router.post("/signup")
async def signup(
    user_data: UserCreate,
    db: Annotated[Session, Depends(db_dependency)],
):
    """
    Creates a new user and an associated profile based on user type.
    """

    # Check user type and ensure it exists in UserTypeEnum
    try:
        user_type = UserTypeEnum.from_safe_name(user_data.user_type)
    except ValueError:
        logger.error("Unsupported user type during profile creation.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported user type for profile creation.",
        )

    # Hash the password before saving
    hashed_password: bytes = get_password_hash(user_data.password.get_secret_value())

    # Create the basic User entry
    user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=str(user_data.email),
        hashed_password=hashed_password,
        user_type_id=user_type.value,
        is_active=user_data.is_active,
        is_verified=user_data.is_verified,
        phone_number=user_data.phone_number,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    try:
        # Determine and create the appropriate profile
        match user_type:
            case UserTypeEnum.STUDENT:
                guardian = Guardian(
                    name=user_data.guardian_name,
                    phone_number=user_data.guardian_phone_number,
                )
                guardian = db.merge(guardian)
                db.commit()
                profile = Student(
                    user_id=user.id,
                    matriculation_number=user_data.matriculation_number,
                    course_of_study=user_data.course_of_study,
                    guardian_id=guardian.id,
                    guardian_relationship=user_data.guardian_relationship,
                )
            case UserTypeEnum.STAFF:
                profile = Staff(
                    user_id=user.id,
                    staff_id=user_data.staff_id,
                    designation=user_data.designation,
                )
            case UserTypeEnum.SECURITY_OPERATIVE:
                profile = SecurityOperative(
                    user_id=user.id,
                    security_id=user_data.security_id,
                    designation=user_data.designation,
                )
            case _:
                db.delete(user)
                db.commit()
                logger.error("Unsupported user type during profile creation.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported user type for profile creation.",
                )
    except SQLAlchemyError:
        db.delete(user)
        db.commit()
        logger.error("Error during profile creation.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error during profile creation.",
        )
    # Add profile to the database
    db.add(profile)
    db.commit()
    db.refresh(profile)
    logger.info(
        f"Created new user with ID {user.id} and profile type {profile.__class__.__name__}."
    )

    # Log the user in
    access_token = create_access_token({"sub": user.email})
    logger.info(f"User {user.email} logged in successfully")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserResponse(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            user_type=user_type.safe_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            profile_picture_id=user.profile_picture_id,
        ),
    }
