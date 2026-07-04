"""
AI Mind Reader - Ollama Adapter

Ollama surfaces reasoning via <think>...</think> tags embedded in the
response text. Models that support this: DeepSeek-R1, Qwen3, some Hermes
builds, and any model configured to emit chain-of-thought tags.

Usage - parse a single response string:
    from adapters.ollama import OllamaAdapter
    thinking, content = OllamaAdapter.parse_response(raw_text)

Usage - read a JSONL log of Ollama responses:
    traces = OllamaAdapter.read_log("path/to/ollama_log.jsonl")
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone

# Matches <think>...</think> blocks, including multiline
_THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)


class OllamaAdapter:
    """
    Adapter for Ollama model responses.

    Ollama reasoning models embed chain-of-thought in <think> tags:

        <think>
        Let me consider the authentication flow first...
        The JWT expiration check looks wrong here.
        </think>

        Based on my analysis, I found two issues...

    The thinking is everything inside the tags.
    The content is everything outside the tags.
    """

    @staticmethod
    def parse_response(raw_text: str) -> tuple[str, str]:
        """
        Parse a raw Ollama response string.

        Returns:
            (thinking, content)
            thinking - concatenated text from all <think> blocks
            content - response text with <think> blocks removed
        """
        thoughts = _THINK_RE.findall(raw_text)
        thinking = "\n\n".join(t.strip() for t in thoughts)
        content = _THINK_RE.sub("", raw_text).strip()
        return thinking, content

    @staticmethod
    def has_thinking(raw_text: str) -> bool:
        """Return True if the response contains at least one <think> block."""
        return bool(_THINK_RE.search(raw_text))

    @staticmethod
    def read_log(log_path: str, response_field: str = "response") -> list[dict]:
        """
        Read a JSONL log file of Ollama responses and extract thinking traces.

        Expects each line to be a JSON object containing the raw model response.
        Common fields: "response", "message.content", "content".

        Args:
            log_path:       Path to the JSONL log file
            response_field: JSON field name containing the response text
                            Use dot notation for nested fields: "message.content"

        Returns:
            List of trace dicts with: step_index, thinking, content, created_at
        """
        path = Path(log_path)
        if not path.exists():
            raise FileNotFoundError(f"Ollama log not found: {path}")

        traces = []
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Resolve nested field via dot notation
                raw_text = entry
                for key in response_field.split("."):
                    if isinstance(raw_text, dict):
                        raw_text = raw_text.get(key, "")
                    else:
                        raw_text = ""
                        break

                if not isinstance(raw_text, str) or not raw_text.strip():
                    continue

                thinking, content = OllamaAdapter.parse_response(raw_text)
                if not thinking:
                    continue  # no <think> block - skip

                traces.append({
                    "step_index": idx,
                    "created_at": entry.get("created_at") or entry.get("timestamp")
                                  or datetime.now(timezone.utc).isoformat(),
                    "thinking": thinking,
                    "content": content,
                    "tool_calls": [],
                    "model": entry.get("model", "unknown"),
                })

        return traces

    @staticmethod
    def from_api_response(response_obj) -> tuple[str, str]:
        """
        Extract thinking from an Ollama Python SDK response object.

        Compatible with: ollama.chat(), ollama.generate() responses.

        Args:
            response_obj: Response object from the Ollama Python library

        Returns:
            (thinking, content)
        """
        # ollama.generate() → response.response
        # ollama.chat()     → response.message.content
        raw = ""
        if hasattr(response_obj, "response"):
            raw = response_obj.response or ""
        elif hasattr(response_obj, "message"):
            msg = response_obj.message
            raw = getattr(msg, "content", "") or ""
        elif isinstance(response_obj, dict):
            raw = response_obj.get("response") or response_obj.get("message", {}).get("content", "")

        return OllamaAdapter.parse_response(raw)
