from __future__ import annotations

import logging
import re
import time
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

    def is_configured(self) -> bool:
        return bool(get_settings().deepseek_api_key)

    def chat(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
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

        max_attempts = max(settings.deepseek_max_retries + 1, 1)
        last_exc: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                with httpx.Client(timeout=settings.deepseek_timeout_seconds) as client:
                    response = client.post(
                        f"{settings.deepseek_base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                response.raise_for_status()
                return response.json()
            except httpx.ReadTimeout as exc:
                last_exc = exc
                logger.warning("DeepSeek API read timeout on attempt %s/%s", attempt, max_attempts)
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                status_code = exc.response.status_code if exc.response else 0
                logger.warning(
                    "DeepSeek API status error %s on attempt %s/%s",
                    status_code,
                    attempt,
                    max_attempts,
                )
                if 400 <= status_code < 500 and status_code != 429:
                    break
            except httpx.HTTPError as exc:
                last_exc = exc
                logger.warning("DeepSeek API transport error on attempt %s/%s", attempt, max_attempts)

            if attempt < max_attempts:
                time.sleep(min(1.2 * attempt, 3.0))

        logger.exception("DeepSeek API call failed")
        if isinstance(last_exc, httpx.ReadTimeout):
            raise LLMServiceError("DeepSeek API timeout") from last_exc
        raise LLMServiceError("Failed to call DeepSeek API") from last_exc

    def chat_text(self, system_prompt: str, user_prompt: str) -> str:
        response = self.chat(system_prompt=system_prompt, user_prompt=user_prompt)
        choices = response.get("choices", [])
        if not choices:
            raise LLMServiceError("DeepSeek response missing choices")
        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMServiceError("DeepSeek response content is empty")
        return content.strip()

    def extract_json_block(self, content: str) -> str:
        fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", content, flags=re.DOTALL)
        if fenced_match:
            return fenced_match.group(1).strip()
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            return content[start : end + 1]
        raise LLMServiceError("DeepSeek response does not contain JSON object")
