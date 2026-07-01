from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.research import router as research_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Multi-Agent Research Workspace",
        version="0.1.0",
        description="Source collection, credibility scoring, and cited research brief generation.",
    )
    app.include_router(health_router)
    app.include_router(research_router)
    return app


app = create_app()
