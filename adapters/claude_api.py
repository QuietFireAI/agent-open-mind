"""
AI Mind Reader - Claude API Adapter (Anthropic)

Claude 3.7+ with extended thinking enabled returns content blocks where
`type == "thinking"` contains the reasoning trace and `type == "text"`
contains the visible output.

Extended thinking must be explicitly enabled in the API call:
    client.messages.create(
        model="claude-sonnet-4-5",
        thinking={"type": "enabled", "budget_tokens": 10000},
        ...
    )

Without extended thinking, Claude produces no thinking blocks.
Zero thinking blocks = tainted result under AI Mind Reader integrity rules.

Usage - parse an Anthropic SDK response:
    from adapters.claude_api import ClaudeAdapter
    thinking, content = ClaudeAdapter.from_api_response(response)

Usage - read a JSONL log of logged Claude responses:
    traces = ClaudeAdapter.read_log("path/to/claude_log.jsonl")
"""

import json
from pathlib import Path
from datetime import datetime, timezone


class ClaudeAdapter:
    """
    Adapter for Anthropic Claude API responses with extended thinking.

    Response structure (with thinking enabled):
        response.content = [
            ContentBlock(type="thinking", thinking="Let me reason..."),
            ContentBlock(type="text",     text="Based on my analysis..."),
        ]
    """

    @staticmethod
    def parse_content_blocks(content_blocks: list) -> tuple[str, str]:
        """
        Parse a list of Claude content blocks.

        Args:
            content_blocks: List of content block objects or dicts.
                            Each has 'type' and either 'thinking' or 'text'.

        Returns:
            (thinking, content)
            thinking - concatenated text from all type=="thinking" blocks
            content - concatenated text from all type=="text" blocks
        """
        thinking_parts = []
        content_parts = []

        for block in content_blocks:
            # Support both SDK objects and plain dicts
            if isinstance(block, dict):
                block_type = block.get("type", "")
                if block_type == "thinking":
                    thinking_parts.append(block.get("thinking", "").strip())
                elif block_type == "text":
                    content_parts.append(block.get("text", "").strip())
            else:
                # Anthropic SDK ContentBlock object
                block_type = getattr(block, "type", "")
                if block_type == "thinking":
                    thinking_parts.append(getattr(block, "thinking", "").strip())
                elif block_type == "text":
                    content_parts.append(getattr(block, "text", "").strip())

        thinking = "\n\n".join(t for t in thinking_parts if t)
        content = "\n\n".join(c for c in content_parts if c)
        return thinking, content

    @staticmethod
    def from_api_response(response) -> tuple[str, str]:
        """
        Extract thinking from an Anthropic SDK response object.

        Compatible with: anthropic.messages.create() response.

        Args:
            response: Response from the Anthropic Python SDK

        Returns:
            (thinking, content)
        """
        content_blocks = []
        if hasattr(response, "content"):
            content_blocks = response.content or []
        elif isinstance(response, dict):
            content_blocks = response.get("content", [])

        return ClaudeAdapter.parse_content_blocks(content_blocks)

    @staticmethod
    def has_thinking(response) -> bool:
        """Return True if the response contains at least one thinking block."""
        thinking, _ = ClaudeAdapter.from_api_response(response)
        return bool(thinking.strip())

    @staticmethod
    def read_log(log_path: str) -> list[dict]:
        """
        Read a JSONL log file of Claude API responses and extract thinking traces.

        Expects each line to be a JSON-serialized Anthropic API response.
        Log your responses with: json.dumps(response.model_dump())

        Args:
            log_path: Path to the JSONL log file

        Returns:
            List of trace dicts with: step_index, thinking, content, created_at, model
        """
        path = Path(log_path)
        if not path.exists():
            raise FileNotFoundError(f"Claude log not found: {path}")

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

                content_blocks = entry.get("content", [])
                thinking, content = ClaudeAdapter.parse_content_blocks(content_blocks)

                if not thinking:
                    continue  # no thinking block - skip (but caller should flag as tainted)

                traces.append({
                    "step_index": idx,
                    "created_at": entry.get("created_at")
                                  or datetime.now(timezone.utc).isoformat(),
                    "thinking": thinking,
                    "content": content,
                    "tool_calls": [],
                    "model": entry.get("model", "unknown"),
                    "input_tokens": entry.get("usage", {}).get("input_tokens"),
                    "thinking_tokens": sum(
                        1 for b in content_blocks
                        if (isinstance(b, dict) and b.get("type") == "thinking")
                    ),
                })

        return traces
