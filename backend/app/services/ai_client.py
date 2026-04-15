"""
ai_client.py — Model-agnostic OpenRouter service layer.

All AI calls in PaceForge go through this module. It wraps OpenRouter's
OpenAI-compatible endpoint, enforces structured JSON output, validates
responses with Pydantic, retries transient errors, falls back to a
secondary model, and records every call to ai_usage_log.
"""
from __future__ import annotations

import json
import time
import logging
from typing import Type, TypeVar, Optional

import httpx
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from ..config import settings
from ..models.ai_usage import AIUsageLog

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Errors that are safe to retry (network blips, timeouts)
_RETRYABLE = (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)


class AIGenerationError(Exception):
    """Raised when all attempts (primary + fallback) fail."""


class AIClient:
    def __init__(self) -> None:
        self.base_url = settings.openrouter_base_url
        self.api_key = settings.openrouter_api_key
        self.default_model = settings.ai_model
        self.fallback_model = settings.ai_fallback_model

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        feature: str = "other",
        plan_type: Optional[str] = None,
        db=None,
        model_override: Optional[str] = None,
    ) -> T:
        """
        Generate a structured AI response validated against *response_model*.

        Tries the primary model first; falls back to *ai_fallback_model* on
        any non-retryable failure, then raises AIGenerationError if both fail.
        """
        primary = model_override or self.default_model
        models_to_try = [primary]
        if self.fallback_model and self.fallback_model != primary:
            models_to_try.append(self.fallback_model)

        last_exc: Exception = AIGenerationError("No models configured.")
        for model in models_to_try:
            try:
                return await self._call_with_retry(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=response_model,
                    feature=feature,
                    plan_type=plan_type,
                    db=db,
                    model=model,
                )
            except AIGenerationError as exc:
                logger.warning("Model %s failed: %s — trying next.", model, exc)
                last_exc = exc

        raise last_exc

    # ── Internal ──────────────────────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=False,
    )
    async def _call_with_retry(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        feature: str,
        plan_type: Optional[str],
        db,
        model: str,
    ) -> T:
        start_ms = time.time()
        success = False
        error_msg: Optional[str] = None
        usage_data: dict = {}
        request_id: Optional[str] = None

        try:
            response = await self._http_post(
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            data = response.json()
            request_id = data.get("id")
            usage_data = data.get("usage", {})

            raw_content = data["choices"][0]["message"]["content"]
            parsed_json = json.loads(raw_content)
            result = response_model.model_validate(parsed_json)
            success = True
            return result

        except (httpx.HTTPStatusError, json.JSONDecodeError, ValidationError, KeyError) as exc:
            error_msg = str(exc)
            raise AIGenerationError(f"[{model}] {error_msg}") from exc

        finally:
            duration_ms = int((time.time() - start_ms) * 1000)
            self._log_usage(
                db=db,
                model=model,
                feature=feature,
                plan_type=plan_type,
                usage=usage_data,
                duration_ms=duration_ms,
                success=success,
                error_message=error_msg,
                request_id=request_id,
            )

    async def _http_post(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://paceforge.local",
            "X-Title": "PaceForge",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=settings.ai_timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp

    @staticmethod
    def _log_usage(
        *,
        db,
        model: str,
        feature: str,
        plan_type: Optional[str],
        usage: dict,
        duration_ms: int,
        success: bool,
        error_message: Optional[str],
        request_id: Optional[str],
    ) -> None:
        if db is None:
            return
        try:
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            # OpenRouter may embed cost directly in usage
            cost_usd = float(usage.get("cost", 0.0))

            log = AIUsageLog(
                model=model,
                feature=feature,
                plan_type=plan_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                request_id=request_id,
            )
            db.add(log)
            db.commit()
        except Exception:
            logger.exception("Failed to persist AI usage log — non-fatal.")


# Module-level singleton
ai_client = AIClient()
