from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine

MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@asynccontextmanager
async def handle_lifespan(app: FastAPI):
    if settings.DEMO:
        from app.core.demo_seed import handle_seed_demo_data

        handle_seed_demo_data(engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if ((settings.PROD == False)) else "",
    docs_url=f"{settings.API_V1_PREFIX}/docs" if ((settings.PROD == False)) else "",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if ((settings.PROD == False)) else "",
    lifespan=handle_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_URL,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def handle_block_mutations_in_demo(request: Request, call_next):
    if settings.DEMO and request.method in MUTATION_METHODS:
        return JSONResponse(status_code=403, content={"message": "Action disabled in demo version"})
    return await call_next(request)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
def handle_health_check():
    return {"status": "ok"}
