from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routers import auth, courses


def create_app() -> FastAPI:
    app = FastAPI(title="Education AI Platform API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(courses.router)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    return app


app = create_app()
