from loguru import logger
from sqlalchemy.orm import Session

from .models import ExeatRequest, SecurityOperative, Staff, Student, User


# EXCEPTIONS
class DBException(Exception):
    pass


class UserNotFound(DBException):
    pass


class ExeatRequestNotFound(DBException):
    pass


class StudentNotFound(DBException):
    pass


class StaffNotFound(DBException):
    pass


class SecurityOperativeNotFound(DBException):
    pass


# CRUD FUNCTIONS


# User
def create_user(db: Session, user: User) -> User:
    logger.info("Creating user with email {}", user.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("User created with ID {}", user.id)
    return user


def get_user(db: Session, user_id: int) -> User:
    user: User | None = db.get(User, user_id)
    if not user:
        logger.error("User with ID {} not found", user_id)
        raise UserNotFound(f"User with ID {user_id} not found")
    return user


def update_user(db: Session, user_id: int, **updates) -> User:
    user = get_user(db, user_id)
    for key, value in updates.items():
        if value is not None:
            setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Updated user with ID {}", user_id)
    return user


def delete_user(db: Session, user_id: int) -> None:
    user = get_user(db, user_id)
    db.delete(user)
    db.commit()
    logger.info("Deleted user with ID {}", user_id)


# Student
def create_student(db: Session, student: Student) -> Student:
    logger.info(
        "Creating student with matriculation number {}", student.matriculation_number
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    logger.info("Student created with ID {}", student.id)
    return student


def get_student(db: Session, student_id: int) -> Student:
    student: Student | None = db.get(Student, student_id)
    if not student:
        logger.error("Student with ID {} not found", student_id)
        raise StudentNotFound(f"Student with ID {student_id} not found")
    return student


def update_student(db: Session, student_id: int, **updates) -> Student:
    student = get_student(db, student_id)
    for key, value in updates.items():
        if value is not None:
            setattr(student, key, value)
    db.add(student)
    db.commit()
    db.refresh(student)
    logger.info("Updated student with ID {}", student_id)
    return student


def delete_student(db: Session, student_id: int) -> None:
    student = get_student(db, student_id)
    db.delete(student)
    db.commit()
    logger.info("Deleted student with ID {}", student_id)


# Staff
def create_staff(db: Session, staff: Staff) -> Staff:
    logger.info("Creating staff with ID {}", staff.staff_id)
    db.add(staff)
    db.commit()
    db.refresh(staff)
    logger.info("Staff created with ID {}", staff.id)
    return staff


def get_staff(db: Session, staff_id: int) -> Staff:
    staff: Staff | None = db.get(Staff, staff_id)
    if not staff:
        logger.error("Staff with ID {} not found", staff_id)
        raise StaffNotFound(f"Staff with ID {staff_id} not found")
    return staff


def update_staff(db: Session, staff_id: int, **updates) -> Staff:
    staff = get_staff(db, staff_id)
    for key, value in updates.items():
        if value is not None:
            setattr(staff, key, value)
    db.add(staff)
    db.commit()
    db.refresh(staff)
    logger.info("Updated staff with ID {}", staff_id)
    return staff


def delete_staff(db: Session, staff_id: int) -> None:
    staff = get_staff(db, staff_id)
    db.delete(staff)
    db.commit()
    logger.info("Deleted staff with ID {}", staff_id)


# Security Operative
def create_security_operative(
    db: Session, security_operative: SecurityOperative
) -> SecurityOperative:
    logger.info(
        "Creating security operative with ID {}", security_operative.security_id
    )
    db.add(security_operative)
    db.commit()
    db.refresh(security_operative)
    logger.info("Security operative created with ID {}", security_operative.id)
    return security_operative


def get_security_operative(
    db: Session, security_operative_id: int
) -> SecurityOperative:
    security_operative: SecurityOperative | None = db.get(
        SecurityOperative, security_operative_id
    )
    if not security_operative:
        logger.error("Security operative with ID {} not found", security_operative_id)
        raise SecurityOperativeNotFound(
            f"Security operative with ID {security_operative_id} not found"
        )
    return security_operative


def update_security_operative(
    db: Session, security_operative_id: int, **updates
) -> SecurityOperative:
    security_operative = get_security_operative(db, security_operative_id)
    for key, value in updates.items():
        if value is not None:
            setattr(security_operative, key, value)
    db.add(security_operative)
    db.commit()
    db.refresh(security_operative)
    logger.info("Updated security operative with ID {}", security_operative_id)
    return security_operative


def delete_security_operative(db: Session, security_operative_id: int) -> None:
    security_operative = get_security_operative(db, security_operative_id)
    db.delete(security_operative)
    db.commit()
    logger.info("Deleted security operative with ID {}", security_operative_id)


# ExeatRequest
def create_exeat_request(db: Session, exeat_request: ExeatRequest) -> ExeatRequest:
    logger.info("Creating exeat request for student ID {}", exeat_request.student_id)
    db.add(exeat_request)
    db.commit()
    db.refresh(exeat_request)
    logger.info("Exeat request created with ID {}", exeat_request.id)
    return exeat_request


def get_exeat_request(db: Session, exeat_request_id: int) -> ExeatRequest:
    exeat_request: ExeatRequest | None = db.get(ExeatRequest, exeat_request_id)
    if not exeat_request:
        logger.error("Exeat request with ID {} not found", exeat_request_id)
        raise ExeatRequestNotFound(
            f"Exeat request with ID {exeat_request_id} not found"
        )
    return exeat_request


def update_exeat_request(db: Session, exeat_request_id: int, **updates) -> ExeatRequest:
    exeat_request = get_exeat_request(db, exeat_request_id)
    for key, value in updates.items():
        if value is not None:
            setattr(exeat_request, key, value)
    db.add(exeat_request)
    db.commit()
    db.refresh(exeat_request)
    logger.info("Updated exeat request with ID {}", exeat_request_id)
    return exeat_request


def delete_exeat_request(db: Session, exeat_request_id: int) -> None:
    exeat_request = get_exeat_request(db, exeat_request_id)
    db.delete(exeat_request)
    db.commit()
    logger.info("Deleted exeat request with ID {}", exeat_request_id)
