from .account import router as account_router
from .account import title as account_title
from .auth import router as auth_router
from .auth import title as auth_title
from .security import router as security_router
from .security import title as security_title
from .staff import router as staff_router
from .staff import title as staff_title
from .student import router as student_router
from .student import title as student_title

__all__ = (
    "auth_router",
    "auth_title",
    "account_router",
    "account_title",
    "security_router",
    "security_title",
    "student_router",
    "student_title",
    "staff_router",
    "staff_title",
)
