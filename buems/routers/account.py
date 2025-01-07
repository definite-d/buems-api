from io import BytesIO
from os import mkdir
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from filetype import guess_extension
from loguru import logger
from PIL import Image
from sqlmodel import Session, select
from starlette import status

from ..constants import MAX_PROFILE_PICTURE_SIZE, PROFILE_PICTURE_PATH
from ..db import SecurityOperative, Staff, Student, User, UserTypeEnum, db_dependency
from .auth import (
    ChangePassword,
    UpdateUserInfo,
    UserResponse,
    get_current_user,
    get_password_hash,
    verify_password,
)

title = "Account Management"
router = APIRouter(prefix="/account", tags=[title])


@router.get("/", response_model=UserResponse)
async def get_account_info(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Get current user's account information.
    """
    logger.info(f"User {current_user.id} accessed their account info.")
    return UserResponse(
        **current_user.model_dump(),
        user_type=UserTypeEnum(current_user.user_type_id).safe_name,
    )


@router.put("/update", response_model=UserResponse)
async def update_account_info(
    updates: UpdateUserInfo,
    db: Annotated[Session, Depends(db_dependency)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Update current user's personal account information.
    """
    # Update fields if provided
    user_updated = False
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
        user_updated = True

    if user_updated:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
        logger.info(f"User {current_user.id} updated their account information.")
    else:
        logger.warning(f"User {current_user.id} attempted an update without changes.")

    return UserResponse(
        **current_user.model_dump(),
        user_type=UserTypeEnum(current_user.user_type_id).safe_name,
    )


@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    passwords: ChangePassword,
    db: Annotated[Session, Depends(db_dependency)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Change current user's password.
    """
    # Verify old password
    if not verify_password(passwords.old_password, current_user.hashed_password):
        logger.warning(f"User {current_user.id} provided an incorrect old password.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect password"
        )

    # Update password
    current_user.hashed_password = get_password_hash(passwords.new_password)
    db.add(current_user)
    db.commit()
    logger.info(f"User {current_user.id} successfully changed their password.")
    return {"message": "Password updated successfully."}


@router.delete("/delete", status_code=status.HTTP_200_OK)
async def delete_account(
    db: Annotated[Session, Depends(db_dependency)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Delete current user's account.
    """
    db.delete(current_user)
    db.commit()
    logger.info(f"User {current_user.id} deleted their account.")
    return {"message": "Account deleted successfully."}


@router.get("/profile")
async def get_user_profile(
    db: Annotated[Session, Depends(db_dependency)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get the profile of the current user, whether student, staff, or security operative.
    """
    # Check if the user has a Student profile
    # noinspection PyTypeChecker,Pydantic
    student_profile = db.exec(
        select(Student).where(Student.user_id == current_user.id)
    ).first()
    if student_profile:
        logger.info(f"User {current_user.id} retrieved their Student profile.")
        return {"user_type": UserTypeEnum.STUDENT.safe_name, "profile": student_profile}

    # Check if the user has a Staff profile
    # noinspection PyTypeChecker,Pydantic
    staff_profile = db.exec(
        select(Staff).where(Staff.user_id == current_user.id)
    ).first()
    if staff_profile:
        logger.info(f"User {current_user.id} retrieved their Staff profile.")
        return {"user_type": UserTypeEnum.STAFF.safe_name, "profile": staff_profile}

    # Check if the user has a Security Operative profile
    # noinspection PyTypeChecker,Pydantic
    security_profile = db.exec(
        select(SecurityOperative).where(SecurityOperative.user_id == current_user.id)
    ).first()
    if security_profile:
        logger.info(
            f"User {current_user.id} retrieved their Security Operative profile."
        )
        return {
            "user_type": UserTypeEnum.SECURITY_OPERATIVE.safe_name,
            "profile": security_profile,
        }

    # If no profile is found, raise an error
    logger.error(f"User {current_user.id} has no associated profile.")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
    )


@router.post("/upload-profile-picture", status_code=status.HTTP_200_OK)
async def upload_profile_picture(
    file: Annotated[
        UploadFile,
        File(
            ...,
            description=f"The profile picture to upload. "
            f"Maximum size: {MAX_PROFILE_PICTURE_SIZE/(1024**2)}MiB. "
            f"Must be a `JPEG`, `PNG`, or `WebP` file",
        ),
    ],
    db: Annotated[Session, Depends(db_dependency)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Upload a profile picture for the current user.
    """
    if file.size > MAX_PROFILE_PICTURE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Profile picture is too large to upload "
            f"({file.size/(1024**2):.2f}MiB > {MAX_PROFILE_PICTURE_SIZE/(1024**2)}MiB).",
        )
    file = BytesIO(await file.read())
    if guess_extension(file) not in ["jpeg", "png", "webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile picture must be a JPEG, PNG, or WebP file.",
        )
    ppid = user.profile_picture_id or str(uuid4())

    profile_picture = Image.open(file)
    profile_picture.thumbnail((300, 300))
    if not PROFILE_PICTURE_PATH.exists():
        mkdir(PROFILE_PICTURE_PATH)
    with open(PROFILE_PICTURE_PATH / f"{ppid}.webp", "wb") as f:
        profile_picture.save(f, format="webp", optimize=True)

    user.profile_picture_id = ppid
    db.merge(user)
    db.commit()

    logger.info(f"User {user.id} uploaded a profile picture.")
    return {"message": "Profile picture uploaded successfully."}
