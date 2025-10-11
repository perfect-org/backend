from contextlib import asynccontextmanager
import logging
import uvicorn
import traceback_with_variables

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.database import init_db

from app.api.v1 import main_router

from app.exceptions.handler_errors import register_errors_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception:
        raise

    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="VitaminBox", lifespan=lifespan, version="1.0.0"
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(main_router, prefix=settings.API_V1)

    register_errors_handler(application)

    return application


app = create_app()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        uvicorn.run("main:app", reload=True)
    except Exception as e:
        traceback_with_variables.print_exc(e)
