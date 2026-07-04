"""
AI Mind Reader - Gemini API Adapter (Google)

Gemini 2.5 Pro and Flash Thinking return thought parts in the response
where `part.thought == True`. These parts contain the model's reasoning
before it produces the visible output.

Thinking is enabled automatically for Gemini 2.5 Pro.
For other models, use: GenerationConfig(thinking_config=ThinkingConfig(...))

Usage - parse a Gemini SDK response:
    from adapters.gemini_api import GeminiAdapter
    thinking, content = GeminiAdapter.from_api_response(response)

Usage - read a JSONL log of logged Gemini responses:
    traces = GeminiAdapter.read_log("path/to/gemini_log.jsonl")
"""

import json
from pathlib import Path
from datetime import datetime, timezone


class GeminiAdapter:
    """
    Adapter for Google Gemini API responses with thinking enabled.

    Response structure:
        response.candidates[0].content.parts = [
            Part(thought=True,  text="Let me reason through this..."),
            Part(thought=False, text="Based on my analysis..."),
        ]

    Compatible with: google-generativeai SDK, google-genai SDK,
                     Vertex AI generative models.
    """

    @staticmethod
    def parse_parts(parts: list) -> tuple[str, str]:
        """
        Parse a list of Gemini response parts.

        Args:
            parts: List of Part objects or dicts.
                   Thought parts have thought=True (or is_thought=True in some versions).
                   Content parts have thought=False or thought omitted.

        Returns:
            (thinking, content)
        """
        thinking_parts = []
        content_parts = []

        for part in parts:
            if isinstance(part, dict):
                # Dict representation (from JSON log or model_dump())
                is_thought = part.get("thought", False) or part.get("is_thought", False)
                text = part.get("text", "").strip()
                if is_thought:
                    thinking_parts.append(text)
                elif text:
                    content_parts.append(text)
            else:
                # SDK Part object
                is_thought = getattr(part, "thought", False) or getattr(part, "is_thought", False)
                text = getattr(part, "text", "").strip()
                if is_thought:
                    thinking_parts.append(text)
                elif text:
                    content_parts.append(text)

        thinking = "\n\n".join(t for t in thinking_parts if t)
        content = "\n\n".join(c for c in content_parts if c)
        return thinking, content

    @staticmethod
    def from_api_response(response) -> tuple[str, str]:
        """
        Extract thinking from a Gemini SDK response object.

        Compatible with responses from:
 - google.generativeai (genai.GenerativeModel.generate_content)
 - google.genai (genai.Client)
 - vertexai.generative_models

        Args:
            response: Response from any Gemini SDK

        Returns:
            (thinking, content)
        """
        parts = []

        try:
            # Standard: response.candidates[0].content.parts
            candidate = response.candidates[0]
            parts = candidate.content.parts
        except (AttributeError, IndexError, TypeError):
            pass

        if not parts:
            try:
                # Fallback: response.parts (some SDK versions)
                parts = response.parts
            except AttributeError:
                pass

        if not parts:
            # Dict fallback
            if isinstance(response, dict):
                candidates = response.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])

        return GeminiAdapter.parse_parts(parts)

    @staticmethod
    def has_thinking(response) -> bool:
        """Return True if the response contains at least one thought part."""
        thinking, _ = GeminiAdapter.from_api_response(response)
        return bool(thinking.strip())

    @staticmethod
    def read_log(log_path: str) -> list[dict]:
        """
        Read a JSONL log file of Gemini API responses and extract thinking traces.

        Expects each line to be a JSON-serialized Gemini response.
        Log your responses with: json.dumps(response.to_dict()) or similar.

        Args:
            log_path: Path to the JSONL log file

        Returns:
            List of trace dicts with: step_index, thinking, content, created_at, model
        """
        path = Path(log_path)
        if not path.exists():
            raise FileNotFoundError(f"Gemini log not found: {path}")

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

                # Extract parts from dict structure
                parts = []
                candidates = entry.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])

                thinking, content = GeminiAdapter.parse_parts(parts)
                if not thinking:
                    continue

                # Gemini usage metadata
                usage = entry.get("usage_metadata", {})
                thinking_tokens = usage.get("thoughts_token_count", 0)

                traces.append({
                    "step_index": idx,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "thinking": thinking,
                    "content": content,
                    "tool_calls": [],
                    "model": entry.get("model_version", "gemini-unknown"),
                    "thinking_tokens": thinking_tokens,
                    "total_tokens": usage.get("total_token_count"),
                })

        return traces
