from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response

from civitas.api.auth_routes import router as auth_router
from civitas.api.billing_routes import router as billing_router
from civitas.api.contract_checks import validate_app_contracts
from civitas.api.routes import router


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    validate_app_contracts(app)
    yield


app = FastAPI(title="Civitas API", version="0.1.0", lifespan=app_lifespan)
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> Response:
    if request.url.path == "/api/v1/schools":
        for error in exc.errors():
            location = tuple(error.get("loc", ()))
            if location == ("query", "postcode"):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "postcode must be a valid UK postcode."},
                )
            if location == ("query", "radius"):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "radius must be between 0 and 25 miles"},
                )

        return JSONResponse(status_code=400, content={"detail": "invalid request parameters."})

    return await request_validation_exception_handler(request, exc)


def run() -> None:
    uvicorn.run("civitas.api.main:app", host="0.0.0.0", port=8000, reload=False)
