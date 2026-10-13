"""FastAPI-backend застосунку «Дієтокс»."""
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

load_dotenv()

from .ai import PlanImpossible, infer  # noqa: E402
from .schemas import ErrorResponse, PlanRequest, PlanResponse  # noqa: E402

log = logging.getLogger("dietox")
app = FastAPI(title="Dietox API", version="1.0.0")


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    fields = sorted({str(e["loc"][-1]) for e in exc.errors() if e.get("loc") and isinstance(e["loc"][-1], str)})
    where = ", ".join(fields) if fields else "тіло запиту"
    return _err(422, "VALIDATION_ERROR", "Некоректні дані у полях: " + where)


@app.exception_handler(Exception)
async def unhandled_handler(_: Request, exc: Exception):
    log.exception("Unhandled error")  # стек лише в лозі сервера, не клієнту
    return _err(500, "INTERNAL_ERROR", "Внутрішня помилка сервера. Спробуйте пізніше.")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/plan", response_model=PlanResponse,
          responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def create_plan(req: PlanRequest):
    try:
        return infer(req.model_dump())
    except PlanImpossible as exc:
        return _err(422, "PLAN_IMPOSSIBLE", str(exc))
