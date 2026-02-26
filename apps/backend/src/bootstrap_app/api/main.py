import uvicorn
from fastapi import FastAPI

from bootstrap_app.api.routes import router

app = FastAPI(title="Bootstrap App API", version="0.1.0")
app.include_router(router)


def run() -> None:
    uvicorn.run("bootstrap_app.api.main:app", host="0.0.0.0", port=8000, reload=False)
