from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """
    Optional LLM client.
    The application remains runnable without an API key by using deterministic services,
    but this client is available for future prompt-based upgrades.
    """

    async def chat(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        settings = get_settings()
        if not settings.deepseek_api_key:
            raise LLMServiceError("DEEPSEEK_API_KEY is not configured")

        payload = {
            "model": settings.deepseek_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.deepseek_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            logger.exception("DeepSeek API call failed")
            raise LLMServiceError("Failed to call DeepSeek API") from exc
