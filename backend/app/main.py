from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import logging

from .config import settings
from .routers import profile, plans, sessions, dashboard, ai_usage, offline
from .routers import gamification, coaching

logger = logging.getLogger(__name__)

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
app.include_router(profile.router, dependencies=[Depends(verify_password)])
app.include_router(plans.router, dependencies=[Depends(verify_password)])
app.include_router(sessions.router, dependencies=[Depends(verify_password)])
app.include_router(dashboard.router, dependencies=[Depends(verify_password)])
app.include_router(ai_usage.router, dependencies=[Depends(verify_password)])
app.include_router(offline.router, dependencies=[Depends(verify_password)])
app.include_router(gamification.router, dependencies=[Depends(verify_password)])
app.include_router(coaching.router, dependencies=[Depends(verify_password)])


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "app": settings.app_name}


# ── Startup tasks ─────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup() -> None:
    _check_insecure_config()
    _seed_achievements()
    _start_scheduler()


def _check_insecure_config() -> None:
    import os
    env = os.getenv("APP_ENV", "development")
    if settings.app_password == "changeme":
        if env != "development":
            raise ValueError(
                "app_password must be changed from the default in non-development "
                "environments. Set APP_PASSWORD in your environment or .env file."
            )
        logger.warning(
            "app_password is set to the insecure default 'changeme'. "
            "Set APP_PASSWORD in your environment or .env file before deploying."
        )
    if "*" in settings.cors_origins:
        if env != "development":
            raise ValueError(
                "CORS_ORIGINS contains '*' (wildcard) which is forbidden in non-development "
                "environments. This would allow requests from any origin, exposing HTTP Basic "
                "credentials. Set specific origins in CORS_ORIGINS or set APP_ENV=development."
            )
        logger.warning(
            "CORS_ORIGINS contains '*' (wildcard) — this allows requests from any origin. "
            "Configure specific origins for production. Set APP_ENV=development to suppress this warning."
        )
    if settings.secret_key == "changeme-secret-key-32chars-minimum":
        logger.warning(
            "secret_key is still the insecure default — "
            "future signing/token features would be compromised. "
            "Set SECRET_KEY before deploying."
        )


def _seed_achievements() -> None:
    from .database import SessionLocal
    from .services.achievement_engine import seed_achievements
    db = SessionLocal()
    try:
        seed_achievements(db)
        logger.info("Achievements seeded.")
    except Exception:
        logger.exception("Failed to seed achievements — non-fatal.")
    finally:
        db.close()


def _start_scheduler() -> None:
    """Start a lightweight background scheduler for daily coaching tasks."""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        from .database import SessionLocal
        from .services.coaching_engine import generate_daily_motivation, generate_weekly_summary, generate_weekly_challenge

        scheduler = AsyncIOScheduler()

        async def _daily_motivation_job():
            db = SessionLocal()
            try:
                await generate_daily_motivation(db)
            except Exception:
                logger.exception("Scheduled daily motivation generation failed")
            finally:
                db.close()

        async def _weekly_summary_job():
            db = SessionLocal()
            try:
                await generate_weekly_summary(db)
                await generate_weekly_challenge(db)
            except Exception:
                logger.exception("Scheduled weekly summary/challenge generation failed")
            finally:
                db.close()

        # Daily motivation at 7am
        scheduler.add_job(_daily_motivation_job, CronTrigger(hour=7, minute=0))
        # Weekly summary Sunday at 8pm
        scheduler.add_job(_weekly_summary_job, CronTrigger(day_of_week="sun", hour=20, minute=0))

        scheduler.start()
        logger.info("Coaching scheduler started.")
    except ImportError:
        logger.warning("apscheduler not installed — scheduled coaching messages disabled.")
    except Exception:
        logger.exception("Failed to start scheduler — non-fatal.")
