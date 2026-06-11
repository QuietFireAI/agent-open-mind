"""
AI Mind Reader — Meta Llama Adapter

Reads reasoning traces from Meta's Llama thinking models.

Meta's Llama API is OpenAI-compatible. Llama 4 reasoning models may
expose thinking via:
  - <think>...</think> tags in content (most common via inference providers)
  - reasoning_content field (if Meta adopts xAI's pattern)

This adapter handles both formats, falling back gracefully. Validate
against the actual API before production use — the exact format for
Meta's official Llama API (api.llama.com) should be confirmed as the
API matures.

Supported thinking models (as of June 2026):
  - Llama-4-Scout-17B-16E-Instruct-FP8   (via Together, Fireworks, Groq)
  - Llama-4-Maverick-17B-128E-Instruct   (via inference providers)
  - meta-llama/Llama-4-Scout-*           (via Together AI)

API (Meta official): https://api.llama.com/v1  (OpenAI-compatible)
API (Together AI):   https://api.together.xyz/v1
Auth: LLAMA_API_KEY or TOGETHER_API_KEY environment variable

NOTE: If running Llama locally via Ollama, use the Ollama adapter instead
— it handles <think> tags identically and does not require API keys.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

_THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)

# Known thinking-capable Llama model name fragments
_THINKING_MODEL_HINTS = (
    "llama-4",
    "llama4",
    "scout",
    "maverick",
)


class MetaAdapter:
    """
    Adapter for Meta Llama thinking models.

    Attempts both <think> tag parsing and reasoning_content field
    extraction. Whichever produces a non-empty result is used.
    Falls back to tainted if neither produces thinking.

    VALIDATION REQUIRED: Confirm exact response format against
    api.llama.com before production deployment.
    """

    @classmethod
    def parse_response(cls, raw) -> dict:
        """
        Parse a Meta Llama API response into a standardized thought result.

        Args:
            raw: Llama API response — OpenAI SDK object or plain dict.

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
            text      = (message.get("content")           or "").strip()
            reasoning = (message.get("reasoning_content") or "").strip()
            reasoning_tokens = usage.get("reasoning_tokens", 0)
        else:
            try:
                if not raw.choices:
                    return cls._tainted("No choices in response")
                message  = raw.choices[0].message
                model    = getattr(raw, "model", "")
                usage    = getattr(raw, "usage", None)
                text     = (getattr(message, "content",           None) or "").strip()
                reasoning= (getattr(message, "reasoning_content", None) or "").strip()
                reasoning_tokens = getattr(usage, "reasoning_tokens", 0) if usage else 0
            except AttributeError as exc:
                return cls._tainted(f"Unexpected response format: {exc}")

        # Try reasoning_content field first (matches xAI Grok pattern)
        if reasoning:
            return {
                "thinking":         reasoning,
                "content":          text,
                "reasoning_tokens": reasoning_tokens,
                "model":            model,
                "tainted":          False,
                "limitation_note":  "",
            }

        # Fall back to <think> tag parsing (matches Ollama/Perplexity pattern)
        thinking_blocks = _THINK_RE.findall(text)
        thinking = "\n\n".join(b.strip() for b in thinking_blocks).strip()
        content  = _THINK_RE.sub("", text).strip()

        if thinking:
            return {
                "thinking":         thinking,
                "content":          content,
                "reasoning_tokens": len(thinking.split()),
                "model":            model,
                "tainted":          False,
                "limitation_note":  "",
            }

        # No thinking found
        model_lower = model.lower()
        is_thinking_model = any(hint in model_lower for hint in _THINKING_MODEL_HINTS)

        if is_thinking_model:
            return cls._tainted(
                f"Model '{model}' appears to support reasoning but returned "
                "no thinking traces. Confirm API format at api.llama.com — "
                "the thinking field name may differ. VALIDATION REQUIRED."
            )

        return cls._tainted(
            f"Model '{model}' does not appear to be a Llama thinking model. "
            "Use Llama 4 Scout or Maverick variants with reasoning enabled."
        )

    @classmethod
    def has_thinking(cls, result: dict) -> bool:
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
        out = Path(
            output_path or
            f"meta_result_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return out
