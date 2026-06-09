"""
AI Mind Reader — OpenAI Adapter

Honest assessment of what OpenAI exposes:

  o1, o1-mini, o3, o3-mini:
    Reasoning tokens are generated internally but the CONTENT is hidden
    by policy. OpenAI returns a reasoning_tokens COUNT in usage metadata
    but does not expose what the model actually thought.

    This is a deliberate policy decision by OpenAI, not a technical limit.
    AI Mind Reader can tell you that reasoning happened and how many tokens
    it used — it cannot tell you what the reasoning contained.

  gpt-4o, gpt-4-turbo, gpt-4:
    No native reasoning tokens. Use structured prompting to elicit
    explicit chain-of-thought in the response itself. This is not the
    same as capturing internal reasoning — it's asking the model to
    narrate its thinking in the output. Better than nothing.

  Summary:
    OpenAI is the only major platform where AI Mind Reader has a
    fundamental limitation for reasoning models. Claude, Gemini, and
    Ollama-based models all expose reasoning content.

Usage:
    from adapters.openai_api import OpenAIAdapter
    result = OpenAIAdapter.from_api_response(response)
    # result.thinking will be empty for o1/o3 — this is expected and documented
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class OpenAIThoughtResult:
    """Result of OpenAI thought extraction."""
    thinking: str           # Empty for o1/o3 — reasoning content hidden by OpenAI
    content: str            # The visible model output
    reasoning_tokens: int   # Count of reasoning tokens used (o1/o3 only)
    model: str              # Model identifier
    tainted: bool           # True if reasoning existed but content is hidden
    limitation_note: str    # Human-readable explanation of the limitation


_OPENAI_LIMITATION = (
    "OpenAI reasoning models (o1, o3) generate reasoning tokens internally "
    "but do not expose the content. Only the token count is available. "
    "This is an OpenAI policy decision. The result is flagged as tainted "
    "because reasoning occurred but cannot be verified. HITL review recommended."
)

_REASONING_MODELS = {"o1", "o1-mini", "o1-preview", "o3", "o3-mini", "o3-pro"}

# Structured prompting prefix for GPT-4 models
# Elicits explicit chain-of-thought in the output itself
CHAIN_OF_THOUGHT_SYSTEM_PROMPT = """Before giving your final answer, work through
your reasoning step by step inside <think> tags. Be explicit about what you're
considering, what you're uncertain about, and why you're making each decision.

Format:
<think>
[your reasoning here]
</think>
[your answer here]

This reasoning is required. Do not skip it."""


class OpenAIAdapter:
    """
    Adapter for OpenAI API responses.

    For o1/o3 models: captures token counts, flags as tainted (content hidden).
    For GPT-4 models: parses <think> tags from structured-prompted responses.
    """

    @staticmethod
    def from_api_response(response) -> OpenAIThoughtResult:
        """
        Extract available reasoning data from an OpenAI SDK response.

        Args:
            response: Response from openai.chat.completions.create()

        Returns:
            OpenAIThoughtResult with thinking, content, and tainted flag
        """
        model = ""
        content = ""
        reasoning_tokens = 0

        # Extract model
        if hasattr(response, "model"):
            model = response.model or ""
        elif isinstance(response, dict):
            model = response.get("model", "")

        # Extract content
        try:
            if hasattr(response, "choices"):
                content = response.choices[0].message.content or ""
            elif isinstance(response, dict):
                content = response["choices"][0]["message"]["content"] or ""
        except (IndexError, KeyError, AttributeError):
            content = ""

        # Extract reasoning token count
        try:
            if hasattr(response, "usage"):
                usage = response.usage
                if hasattr(usage, "completion_tokens_details"):
                    details = usage.completion_tokens_details
                    reasoning_tokens = getattr(details, "reasoning_tokens", 0) or 0
                elif isinstance(usage, dict):
                    reasoning_tokens = (
                        usage.get("completion_tokens_details", {})
                        .get("reasoning_tokens", 0) or 0
                    )
        except (AttributeError, TypeError):
            reasoning_tokens = 0

        # Determine if this is a reasoning model
        model_base = model.split("-")[0].lower() if model else ""
        is_reasoning_model = any(model.lower().startswith(m) for m in _REASONING_MODELS)

        if is_reasoning_model:
            # Reasoning model: content hidden by OpenAI policy
            tainted = reasoning_tokens > 0  # reasoning happened but we can't see it
            return OpenAIThoughtResult(
                thinking="",
                content=content,
                reasoning_tokens=reasoning_tokens,
                model=model,
                tainted=tainted,
                limitation_note=_OPENAI_LIMITATION if tainted else
                    "No reasoning tokens detected. Standard tainted result rules apply.",
            )
        else:
            # GPT-4 / standard model: try to parse <think> tags from output
            # (only present if CHAIN_OF_THOUGHT_SYSTEM_PROMPT was used)
            import re
            think_re = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)
            thoughts = think_re.findall(content)
            thinking = "\n\n".join(t.strip() for t in thoughts)
            clean_content = think_re.sub("", content).strip()

            return OpenAIThoughtResult(
                thinking=thinking,
                content=clean_content,
                reasoning_tokens=0,
                model=model,
                tainted=not bool(thinking),
                limitation_note="" if thinking else
                    "No <think> blocks found. Use CHAIN_OF_THOUGHT_SYSTEM_PROMPT "
                    "to elicit explicit reasoning from GPT-4 models.",
            )

    @staticmethod
    def read_log(log_path: str) -> list[dict]:
        """
        Read a JSONL log of OpenAI API responses.

        For o1/o3 responses: records the reasoning token count and flags as tainted.
        For GPT-4 responses: parses <think> tags from content.

        Returns:
            List of trace dicts. Tainted entries have thinking == "" and tainted == True.
        """
        path = Path(log_path)
        if not path.exists():
            raise FileNotFoundError(f"OpenAI log not found: {path}")

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

                result = OpenAIAdapter.from_api_response(entry)

                traces.append({
                    "step_index": idx,
                    "created_at": entry.get("created")
                                  or datetime.now(timezone.utc).isoformat(),
                    "thinking": result.thinking,
                    "content": result.content,
                    "tool_calls": [],
                    "model": result.model,
                    "tainted": result.tainted,
                    "reasoning_tokens": result.reasoning_tokens,
                    "limitation_note": result.limitation_note,
                })

        return traces

    @staticmethod
    def get_system_prompt() -> str:
        """
        Return the structured prompting system prompt for GPT-4 models.

        Inject this as the system message to elicit explicit chain-of-thought
        in <think> tags. Not available for o1/o3 reasoning models.
        """
        return CHAIN_OF_THOUGHT_SYSTEM_PROMPT
