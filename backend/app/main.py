import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routers import (
    agents,
    auth,
    conversations,
    courses,
    exercises,
    knowledge_base,
    knowledge_tracking,
    lesson_plans,
    rag_qa,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


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
    app.include_router(knowledge_base.router)
    app.include_router(rag_qa.router)
    app.include_router(exercises.router)
    app.include_router(lesson_plans.router)
    app.include_router(knowledge_tracking.router)
    app.include_router(conversations.router)
    app.include_router(agents.router)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    return app


app = create_app()
