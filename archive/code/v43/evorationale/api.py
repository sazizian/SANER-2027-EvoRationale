"""Optional FastAPI service. No secrets in responses; errors fail closed."""
from __future__ import annotations
from typing import Any
from .agent import EvoRationaleAgent

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError as exc:
    raise RuntimeError("Install optional API dependencies: pip install '.[api]'") from exc

app = FastAPI(title="EvoRationale", version="2.0.0-rc1")


class RevalidationRequest(BaseModel):
    state: dict[str, Any]
    history: list[dict[str, Any]]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "note": "offline reference mode unless separately configured"}


@app.post("/v1/revalidate")
def revalidate(payload: RevalidationRequest) -> dict[str, Any]:
    try:
        run = EvoRationaleAgent().run(payload.state, payload.history)
        return {"run_id": run.run_id, "status": run.status, "report": run.report, "trace": run.trace}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
