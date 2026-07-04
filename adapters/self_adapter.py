"""
AI Mind Reader - Self Adapter

The dispatcher reading its own thoughts.

This is the same mechanism as the sub-agent adapters, pointed inward.
The dispatcher's own reasoning traces are logged to transcript.jsonl
in exactly the same format as sub-agent traces.

The only difference: the conversation ID is your own.

Key behaviors beyond the standard adapter:
 - last_n:  read only the most recent N thinking steps (working memory window)
 - cursor:  track which steps have been read to avoid re-reading old thoughts
 - inject:  format output for direct context reflection into the next turn
 - watch:   monitor transcript for new thoughts as they're written (near real-time)

Usage:
    from adapters.self import SelfAdapter

    # Read own last 5 thoughts
    adapter = SelfAdapter(conversation_id="your-own-conv-id")
    thoughts = adapter.read_recent(last_n=5)
    injection = adapter.format_for_reflection(thoughts)

Environment:
    MIND_READER_OWN_ID       Your dispatcher conversation ID
    DISPATCHER_BRAIN_DIR     Path to brain directory
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Cursor - tracks how far into the transcript we've already read
# ─────────────────────────────────────────────────────────────────────────────

class ReadCursor:
    """
    Persists a read position in the transcript so we never re-read
    thoughts we've already processed.

    Stored as a simple JSON file in brain/self/<conversation_id>.cursor.json
    """

    def __init__(self, cursor_path: Path):
        self.path = cursor_path
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"last_step_index": -1, "last_read_at": None}

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    @property
    def last_step_index(self) -> int:
        return self._data.get("last_step_index", -1)

    def advance(self, step_index: int):
        if step_index > self.last_step_index:
            self._data["last_step_index"] = step_index
            self._data["last_read_at"] = datetime.now(timezone.utc).isoformat()
            self.save()


# ─────────────────────────────────────────────────────────────────────────────
# Self Adapter
# ─────────────────────────────────────────────────────────────────────────────

class SelfAdapter:
    """
    The dispatcher reads its own reasoning traces.

    The transcript.jsonl for the dispatcher's own conversation is written
    in exactly the same format as sub-agent transcripts - same PLANNER_RESPONSE
    type, same 'thinking' field, same structure.

    Pointing the adapter at the dispatcher's own conversation ID gives
    the dispatcher working memory of its own recent reasoning.

    This is not available to any LLM by default.
    AI Mind Reader builds it at the orchestration layer.
    """

    STEP_TYPE = "PLANNER_RESPONSE"
    THINKING_FIELD = "thinking"

    def __init__(
        self,
        conversation_id: str | None = None,
        brain_dir: str | None = None,
        platform: str = "antigravity",
    ):
        self.conversation_id = (
            conversation_id
            or os.environ.get("MIND_READER_OWN_ID")
        )
        if not self.conversation_id:
            raise ValueError(
                "conversation_id required. Pass it directly or set "
                "MIND_READER_OWN_ID environment variable."
            )

        brain = Path(brain_dir or os.environ.get("DISPATCHER_BRAIN_DIR", "./brain"))
        self.platform = platform

        # Resolve transcript path based on platform
        if platform == "antigravity":
            self.transcript_path = (
                brain / self.conversation_id
                / ".system_generated" / "logs" / "transcript.jsonl"
            )
        else:
            self.transcript_path = brain / self.conversation_id / "transcript.jsonl"

        # Cursor for incremental reading
        cursor_dir = brain / "self"
        self.cursor = ReadCursor(cursor_dir / f"{self.conversation_id}.cursor.json")

    def _parse_thinking_steps(self, lines: list[str]) -> list[dict]:
        """Parse JSONL lines into thinking steps."""
        steps = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                step = json.loads(line)
            except json.JSONDecodeError:
                continue

            if step.get("type") != self.STEP_TYPE:
                continue

            thinking = step.get(self.THINKING_FIELD, "").strip()
            if not thinking:
                continue

            tool_names = [
                tc.get("name", "") for tc in step.get("tool_calls", [])
                if isinstance(tc, dict)
            ]

            steps.append({
                "step_index": step.get("step_index"),
                "created_at": step.get("created_at"),
                "thinking": thinking,
                "content": step.get("content", "").strip(),
                "tool_calls": [t for t in tool_names if t],
            })
        return steps

    def read_all(self) -> list[dict]:
        """Read all thinking steps from own transcript."""
        if not self.transcript_path.exists():
            return []
        with open(self.transcript_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return self._parse_thinking_steps(lines)

    def read_recent(self, last_n: int = 5) -> list[dict]:
        """
        Read the most recent N thinking steps from own transcript.
        This is the working memory window - how far back the dispatcher looks.
        """
        all_steps = self.read_all()
        return all_steps[-last_n:] if len(all_steps) > last_n else all_steps

    def read_new(self) -> list[dict]:
        """
        Read only thinking steps that are newer than the last cursor position.
        Used for incremental / near-real-time reading.
        """
        all_steps = self.read_all()
        new_steps = [
            s for s in all_steps
            if (s.get("step_index") or 0) > self.cursor.last_step_index
        ]
        if new_steps:
            latest_idx = max(s.get("step_index", 0) for s in new_steps)
            self.cursor.advance(latest_idx)
        return new_steps

    def format_for_reflection(
        self,
        steps: list[dict],
        max_chars_per_thought: int = 300,
    ) -> str:
        """
        Format own recent thoughts for reflection into the next turn's context.

        Compact enough to fit in context without dominating it.
        Structured so the dispatcher can quickly orient itself.

        Returns a string ready to prepend to the next dispatcher turn.
        """
        if not steps:
            return ""

        lines = [
            "## My Recent Reasoning (self-reflection)",
            f"*Last {len(steps)} thinking steps from this session*",
            "",
        ]

        for s in steps:
            step_id = s.get("step_index", "?")
            ts = s.get("created_at", "")[:19] if s.get("created_at") else ""
            thinking = s.get("thinking", "")
            if len(thinking) > max_chars_per_thought:
                thinking = thinking[:max_chars_per_thought] + "..."

            tools = s.get("tool_calls", [])
            tool_str = f" [tools: {', '.join(tools)}]" if tools else ""

            lines.append(f"**Step {step_id}**{' @ ' + ts if ts else ''}{tool_str}")
            lines.append(f"> {thinking}")
            lines.append("")

        lines += [
            "---",
            "*End of self-reflection. Proceed with awareness of the above.*",
            "",
        ]

        return "\n".join(lines)

    def watch(
        self,
        callback,
        poll_interval_seconds: float = 2.0,
        max_iterations: int | None = None,
    ):
        """
        Monitor own transcript for new thinking steps.

        Calls callback(new_steps) whenever new thinking is detected.
        Runs until interrupted or max_iterations reached.

        This is as close to real-time self-reading as the architecture allows:
        the lag is one completed step + poll_interval_seconds.

        Args:
            callback:             Function called with list of new thinking steps
            poll_interval_seconds: How often to check for new steps
            max_iterations:       Stop after N checks (None = run forever)
        """
        iterations = 0
        print(f"Watching own transcript: {self.transcript_path}")
        print(f"Poll interval: {poll_interval_seconds}s | Ctrl+C to stop\n")

        while True:
            try:
                new_steps = self.read_new()
                if new_steps:
                    callback(new_steps)

                iterations += 1
                if max_iterations and iterations >= max_iterations:
                    break

                time.sleep(poll_interval_seconds)

            except KeyboardInterrupt:
                print("\nWatch stopped.")
                break
