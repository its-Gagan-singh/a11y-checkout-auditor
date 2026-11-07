import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles

from .crawler import audit_page
from .report import build_report
from .schemas import AuditRequest
from .security import is_public_url

app = FastAPI(
    title="A11y Checkout Auditor",
    description="AI-assisted WCAG 2.0 / Section 508 audits for payment checkout pages.",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/audit")
async def audit(req: AuditRequest):
    url = str(req.url)
    if not is_public_url(url):
        raise HTTPException(
            status_code=400,
            detail="That address is not allowed. Enter a public http(s) page URL.",
        )
    try:
        raw = await run_in_threadpool(audit_page, url)
    except Exception as exc:  # network errors, timeouts, blocked pages
        raise HTTPException(status_code=400, detail=f"Could not audit that page: {exc}")
    use_ml = os.getenv("USE_ML_ALT") == "1"
    return await run_in_threadpool(build_report, raw, use_ml)


# Serve the dashboard at "/" (must be registered after the API routes).
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
