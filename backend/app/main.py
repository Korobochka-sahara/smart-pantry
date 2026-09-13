from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.household import router as household_router
from app.api.product import router as product_router
from app.api.inventory import router as inventory_router
from app.tasks.cleanup import cleanup_tokens_job


scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        cleanup_tokens_job,
        "interval",
        days=1,
        id="refresh_token_cleanup",
        replace_existing=True,
    )

    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(
    title="Smart Pantry API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(auth_router)
app.include_router(household_router)
app.include_router(product_router)
app.include_router(inventory_router)


@app.get("/")
def root():
    return {
        "message": "Smart Pantry API",
        "status": "OK",
    }