from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import get_scalar_api_reference
from starlette.middleware.gzip import GZipMiddleware

from .constants import DESCRIPTION, STATIC, TITLE, VERSION
from .db import init_db
from .revocation import init_revocation_scheduler
from .routers import (
    account_router,
    auth_router,
    security_router,
    staff_router,
    student_router,
)

info = {
    "title": TITLE,
    "description": DESCRIPTION,
    "version": VERSION,
}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _app.mount("/STATIC", STATIC, name="STATIC")
    init_db()
    init_revocation_scheduler()
    yield


app = FastAPI(**info, lifespan=lifespan)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    GZipMiddleware,  # noqa
    minimum_size=100,
)


@app.get("/", tags=["Root"])
async def root():
    return info


app.include_router(auth_router)
app.include_router(account_router)
app.include_router(student_router)
app.include_router(security_router)
app.include_router(staff_router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("STATIC/favicon.png")


@app.get("/scalar", include_in_schema=False)
def scalar_html(request: Request):
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,  # noqa
        title=app.title,  # noqa
        scalar_favicon_url="/favicon.ico",
        hide_models=True,
        servers=[{"url": str(request.base_url), "description": "BUEMS API Server"}],
    )
