import asyncio
import logging
from typing import Any

import httpx
from fastapi import APIRouter

from app.core.config import settings
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/models",
    tags=["AI Models"],
)

FREE_TIER_NOTE = (
    "Free-tier access is subject to provider quotas and account availability; "
    "verify current provider pricing before use."
)


def _model(
    provider: str,
    model_id: str,
    name: str,
    description: str,
    *,
    available: bool = True,
    free: bool | None = True,
    configured_default: bool = False,
) -> dict[str, Any]:
    return {
        "provider": provider,
        "model": model_id,
        "name": name,
        "free": free,
        "available": available,
        "configured_default": configured_default,
        "description": description,
    }


def _configured_free_models(value: str) -> set[str]:
    return {
        model_id.strip()
        for model_id in value.split(",")
        if model_id.strip()
    }


def _include_backend_defaults(models: list[dict[str, Any]]) -> None:
    configured_defaults = [
        (
            settings.DEFAULT_MODEL_PROVIDER.strip().lower(),
            settings.DEFAULT_MODEL.strip(),
        ),
        (
            settings.LLM_PROVIDER.strip().lower(),
            (
                settings.OLLAMA_MODEL
                if settings.LLM_PROVIDER.strip().lower() == "ollama"
                else settings.GEMINI_MODEL
                if settings.LLM_PROVIDER.strip().lower() == "gemini"
                else settings.DEFAULT_MODEL
            ).strip(),
        ),
    ]

    for provider, model_id in configured_defaults:
        if provider not in {"ollama", "gemini", "openrouter"} or not model_id:
            continue

        existing = next(
            (
                item
                for item in models
                if item["provider"] == provider and item["model"] == model_id
            ),
            None,
        )
        if existing:
            existing["configured_default"] = True
            continue

        models.append(
            _model(
                provider,
                model_id,
                model_id,
                "Configured as a backend default model. "
                + (
                    "Runs locally."
                    if provider == "ollama"
                    else "Verify provider access, pricing, and quota."
                ),
                free=True if provider == "ollama" else None,
                configured_default=True,
            )
        )


async def _openrouter_models(
    status_info: dict[str, Any],
) -> list[dict[str, Any]]:
    if not settings.OPENROUTER_API_KEY:
        status_info.update(
            configured=False,
            message="Set OPENROUTER_API_KEY to enable OpenRouter.",
        )
        return []

    url = f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/models"
    headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                params={"max_price": "0"},
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data")
            if not isinstance(data, list):
                raise ValueError("OpenRouter model response is malformed")

        models = [
            _model(
                "openrouter",
                "openrouter/free",
                "OpenRouter Auto Free",
                "Automatically selects an available free model. "
                + FREE_TIER_NOTE,
            )
        ]
        model_ids = {"openrouter/free"}

        for item in data:
            pricing = item.get("pricing") or {}
            try:
                if (
                    float(pricing.get("prompt")) != 0
                    or float(pricing.get("completion")) != 0
                ):
                    continue
            except (TypeError, ValueError):
                continue

            model_id = item.get("id")
            if not model_id or model_id in model_ids:
                continue

            model_ids.add(model_id)
            models.append(
                _model(
                    "openrouter",
                    model_id,
                    item.get("name") or model_id,
                    "Zero-priced input and output tokens. "
                    + FREE_TIER_NOTE,
                )
            )

        status_info.update(
            configured=True,
            available=True,
            message=f"Loaded {len(models)} free OpenRouter models.",
        )
        return models
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        logger.exception("Could not load OpenRouter free model catalog")
        status_info.update(
            configured=True,
            available=False,
            message="Could not load OpenRouter models. Check the API key and connection.",
        )
        return []


async def _gemini_models(
    status_info: dict[str, Any],
) -> list[dict[str, Any]]:
    if not settings.GEMINI_API_KEY or llm_service.gemini_client is None:
        status_info.update(
            configured=False,
            message="Set GEMINI_API_KEY to enable Gemini.",
        )
        return []

    try:
        loop = asyncio.get_running_loop()
        catalog = await loop.run_in_executor(
            None,
            lambda: list(
                llm_service.gemini_client.models.list(
                    config={"page_size": 100}
                )
            ),
        )

        models = []
        free_model_ids = _configured_free_models(settings.GEMINI_FREE_MODELS)
        for item in catalog:
            name = getattr(item, "name", None)
            supported_actions = getattr(item, "supported_actions", None) or []
            if not name or "generateContent" not in supported_actions:
                continue

            model_id = name.rsplit("/", 1)[-1]
            if model_id not in free_model_ids:
                continue

            models.append(
                _model(
                    "gemini",
                    model_id,
                    getattr(item, "display_name", None) or model_id,
                    "Included in the configured Gemini free-model allowlist. "
                    + FREE_TIER_NOTE,
                    free=True,
                )
            )

        status_info.update(
            configured=True,
            available=True,
            message=(
                f"Loaded {len(models)} free Gemini models from "
                "GEMINI_FREE_MODELS."
            ),
        )
        return models
    except Exception:
        logger.exception("Could not load Gemini model catalog")
        status_info.update(
            configured=True,
            available=False,
            message="Could not load Gemini models. Check the API key and connection.",
        )
        return []


async def _ollama_models(
    status_info: dict[str, Any],
) -> list[dict[str, Any]]:
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
            data = payload.get("models")
            if not isinstance(data, list):
                raise ValueError("Ollama model response is malformed")

        models = []
        for item in data:
            model_id = item.get("name")
            if model_id:
                models.append(
                    _model(
                        "ollama",
                        model_id,
                        f"Ollama - {model_id}",
                        "Runs locally on your computer; no provider API quota.",
                    )
                )

        if not any(item["model"] == settings.OLLAMA_MODEL for item in models):
            models.append(
                _model(
                    "ollama",
                    settings.OLLAMA_MODEL,
                    f"Ollama - {settings.OLLAMA_MODEL}",
                    "Configured local model; download it in Ollama before use.",
                    available=False,
                )
            )

        status_info.update(
            configured=True,
            available=True,
            message=f"Loaded {len(models)} local Ollama models.",
        )
        return models
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        logger.exception("Could not load local Ollama model catalog")
        status_info.update(
            configured=True,
            available=False,
            message="Could not connect to Ollama. Check that Ollama is running.",
        )
        return [
            _model(
                "ollama",
                settings.OLLAMA_MODEL,
                f"Ollama - {settings.OLLAMA_MODEL}",
                "Configured local model; Ollama must be running and the model installed.",
                available=False,
            )
        ]


@router.get("")
async def get_available_models() -> dict[str, Any]:
    providers: dict[str, dict[str, Any]] = {
        provider: {
            "configured": False,
            "available": False,
            "message": "Loading model catalog.",
        }
        for provider in ("ollama", "gemini", "openrouter")
    }

    model_groups = await asyncio.gather(
        _ollama_models(providers["ollama"]),
        _gemini_models(providers["gemini"]),
        _openrouter_models(providers["openrouter"]),
    )
    models = [model for group in model_groups for model in group]
    _include_backend_defaults(models)

    return {
        "success": True,
        "count": len(models),
        "models": models,
        "providers": providers,
        "notice": FREE_TIER_NOTE,
    }
