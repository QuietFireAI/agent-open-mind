"""
AI Mind Reader - Grok Adapter (xAI)

Reads reasoning traces from xAI's Grok thinking models.

Grok (unlike OpenAI's o1/o3) exposes reasoning content directly via the
`reasoning_content` field - similar to Claude's thinking blocks. The
thinking is NOT hidden. This makes Grok one of the most transparent
platforms for thought trace capture.

Supported thinking models:
 - grok-3-mini        (reasoning_effort: "low" | "medium" | "high")
 - grok-3-mini-fast   (reasoning_effort: "low" | "medium" | "high")

API:  https://api.x.ai/v1/chat/completions  (OpenAI-compatible)
Auth: X_AI_API_KEY environment variable

Example:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["X_AI_API_KEY"],
                    base_url="https://api.x.ai/v1")
    response = client.chat.completions.create(
        model="grok-3-mini",
        reasoning_effort="high",
        messages=[{"role": "user", "content": "..."}]
    )
    result = GrokAdapter.parse_response(response)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class GrokAdapter:
    """
    Adapter for xAI Grok thinking models.

    Grok exposes reasoning_content directly - no token counting, no
    artificial taint. If reasoning_content is empty the model either
    doesn't support thinking or reasoning_effort was not set.
    """

    THINKING_MODELS = {
        "grok-3-mini",
        "grok-3-mini-fast",
    }

    @classmethod
    def parse_response(cls, raw) -> dict:
        """
        Parse a Grok API response into a standardized thought result.

        Args:
            raw: xAI API response - OpenAI SDK object or plain dict.

        Returns:
            dict with keys:
              thinking (str), content (str), reasoning_tokens (int),
              model (str), tainted (bool), limitation_note (str)
        """
        if isinstance(raw, dict):
            choices = raw.get("choices", [])
            if not choices:
                return cls._tainted("No choices in response")
            message   = choices[0].get("message", {})
            model     = raw.get("model", "")
            usage     = raw.get("usage", {})
            content   = (message.get("content")   or "").strip()
            reasoning = (message.get("reasoning_content") or "").strip()
            reasoning_tokens = usage.get("reasoning_tokens", 0)
        else:
            try:
                if not raw.choices:
                    return cls._tainted("No choices in response")
                message  = raw.choices[0].message
                model    = getattr(raw, "model", "")
                usage    = getattr(raw, "usage", None)
                content  = (getattr(message, "content",           None) or "").strip()
                reasoning= (getattr(message, "reasoning_content", None) or "").strip()
                reasoning_tokens = getattr(usage, "reasoning_tokens", 0) if usage else 0
            except AttributeError as exc:
                return cls._tainted(f"Unexpected response format: {exc}")

        if not reasoning:
            if any(m in model.lower() for m in cls.THINKING_MODELS):
                return cls._tainted(
                    f"Model '{model}' supports thinking but returned no "
                    "reasoning_content. Set reasoning_effort='high' in the request."
                )
            return cls._tainted(
                f"Model '{model}' does not appear to be a Grok thinking model. "
                "Use grok-3-mini or grok-3-mini-fast with reasoning_effort set."
            )

        return {
            "thinking":         reasoning,
            "content":          content,
            "reasoning_tokens": reasoning_tokens,
            "model":            model,
            "tainted":          False,
            "limitation_note":  "",
        }

    @classmethod
    def has_thinking(cls, result: dict) -> bool:
        """Return True if the result contains accessible thinking."""
        return bool(result.get("thinking")) and not result.get("tainted")

    @classmethod
    def _tainted(cls, reason: str) -> dict:
        return {
            "thinking":         "",
            "content":          "",
            "reasoning_tokens": 0,
            "model":            "",
            "tainted":          True,
            "limitation_note":  reason,
        }

    @classmethod
    def save_result(cls, result: dict, output_path: str | None = None) -> Path:
        """Save parsed result to JSON for inspection or training."""
        out = Path(
            output_path or
            f"grok_result_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return out
