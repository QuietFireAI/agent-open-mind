"""
AI Mind Reader - Perplexity Adapter

Reads reasoning traces from Perplexity's Sonar Reasoning models.

Perplexity's reasoning models embed thinking inside <think>...</think>
tags in the response content - the same pattern as Ollama/DeepSeek-R1.
The tags are stripped from the final content; thinking is returned
separately.

Supported thinking models:
 - sonar-reasoning
 - sonar-reasoning-pro

Non-reasoning models (sonar, sonar-pro) return no thinking and are
flagged as tainted - use the above for thought capture.

API:  https://api.perplexity.ai/chat/completions  (OpenAI-compatible)
Auth: PERPLEXITY_API_KEY environment variable

Example:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["PERPLEXITY_API_KEY"],
                    base_url="https://api.perplexity.ai")
    response = client.chat.completions.create(
        model="sonar-reasoning",
        messages=[{"role": "user", "content": "..."}]
    )
    result = PerplexityAdapter.parse_response(response)
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

_THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)

REASONING_MODELS = {
    "sonar-reasoning",
    "sonar-reasoning-pro",
}


class PerplexityAdapter:
    """
    Adapter for Perplexity Sonar Reasoning models.

    Parses <think>...</think> tags from response content, identical to
    the Ollama adapter pattern. Non-reasoning Sonar models are tainted.
    """

    @classmethod
    def parse_response(cls, raw) -> dict:
        """
        Parse a Perplexity API response into a standardized thought result.

        Args:
            raw: Perplexity API response - OpenAI SDK object or plain dict.

        Returns:
            dict with keys:
              thinking (str), content (str), reasoning_tokens (int),
              model (str), tainted (bool), limitation_note (str)
        """
        if isinstance(raw, dict):
            choices = raw.get("choices", [])
            if not choices:
                return cls._tainted("No choices in response")
            message = choices[0].get("message", {})
            model   = raw.get("model", "")
            text    = (message.get("content") or "").strip()
        else:
            try:
                if not raw.choices:
                    return cls._tainted("No choices in response")
                message = raw.choices[0].message
                model   = getattr(raw, "model", "")
                text    = (getattr(message, "content", None) or "").strip()
            except AttributeError as exc:
                return cls._tainted(f"Unexpected response format: {exc}")

        thinking_blocks = _THINK_RE.findall(text)
        thinking = "\n\n".join(b.strip() for b in thinking_blocks).strip()
        content  = _THINK_RE.sub("", text).strip()

        if not thinking:
            if model in REASONING_MODELS:
                return cls._tainted(
                    f"Model '{model}' is a reasoning model but returned no "
                    "<think> tags. The model may not have engaged reasoning "
                    "for this query."
                )
            return cls._tainted(
                f"Model '{model}' does not appear to be a Perplexity reasoning "
                "model. Use sonar-reasoning or sonar-reasoning-pro."
            )

        return {
            "thinking":         thinking,
            "content":          content,
            "reasoning_tokens": len(thinking.split()),   # word count approximation
            "model":            model,
            "tainted":          False,
            "limitation_note":  "",
        }

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
            f"perplexity_result_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return out
