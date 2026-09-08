from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.household import router as household_router

app = FastAPI(
    title = "Smart Pantry API",
    version = "0.1.0",
)

app.include_router(auth_router)
app.include_router(household_router)

@app.get("/")
def root():
    return {
        "message": "Smart Pantry API",
        "status": "OK",
    }