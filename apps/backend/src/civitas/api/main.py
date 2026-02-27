import uvicorn
from fastapi import FastAPI

from civitas.api.routes import router

app = FastAPI(title="Civitas API", version="0.1.0")
app.include_router(router)


def run() -> None:
    uvicorn.run("civitas.api.main:app", host="0.0.0.0", port=8000, reload=False)
