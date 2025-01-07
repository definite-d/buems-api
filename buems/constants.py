from os import getenv
from pathlib import Path
from tomllib import load

from dotenv import find_dotenv, load_dotenv
from starlette.staticfiles import StaticFiles

load_dotenv(find_dotenv())


class EnvironmentVariables:
    def __getattribute__(self, item) -> str:
        return getenv(item)


pyproject = load(open(Path(__file__).parent.parent.joinpath("pyproject.toml"), "rb"))
env = EnvironmentVariables()

TITLE = pyproject["project"]["name"]
VERSION = pyproject["project"]["version"]
DESCRIPTION = pyproject["project"]["description"]
ACCESS_TOKEN_EXPIRE_MINUTES = 30
MAX_PROFILE_PICTURE_SIZE = 1 * 1024 * 1024  # 1 MB

STATIC_PATH = Path(__file__).parent.parent / "static"
PROFILE_PICTURE_PATH = STATIC_PATH / "profile_pictures"
STATIC = StaticFiles(directory=STATIC_PATH)
