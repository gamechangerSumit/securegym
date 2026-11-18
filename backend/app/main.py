from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.observation_routes import router as observation_router
from app.api.routes import router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.models import Camera, Incident, Zone  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    get_settings().evidence_dir.mkdir(parents=True, exist_ok=True)
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-assisted gym equipment monitoring and incident management",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health():
    return {"status": "healthy", "service": "securegym-api", "version": "0.1.0"}


app.include_router(router, prefix=settings.api_prefix)
app.include_router(observation_router, prefix=settings.api_prefix, tags=["vision-ingest"])
