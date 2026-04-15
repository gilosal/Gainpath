from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

from .config import settings
from .routers import profile, plans, sessions, dashboard, ai_usage, offline

app = FastAPI(
    title="PaceForge API",
    description="Personal fitness training platform — running, lifting, mobility",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Simple single-user auth ───────────────────────────────────────────────────
security = HTTPBasic()


def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    correct = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        settings.app_password.encode("utf-8"),
    )
    if not correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# ── Routers ───────────────────────────────────────────────────────────────────
# All routes are protected by HTTP Basic auth
app.include_router(profile.router, dependencies=[Depends(verify_password)])
app.include_router(plans.router, dependencies=[Depends(verify_password)])
app.include_router(sessions.router, dependencies=[Depends(verify_password)])
app.include_router(dashboard.router, dependencies=[Depends(verify_password)])
app.include_router(ai_usage.router, dependencies=[Depends(verify_password)])
app.include_router(offline.router, dependencies=[Depends(verify_password)])


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "app": settings.app_name}
