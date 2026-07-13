#!/usr/bin/env python3
"""
quick_check.py - Before-turn self-reflection

Read the last N thinking steps from the current session transcript.
Run this BEFORE responding on each turn. Not after. Not when asked. Before.

Usage:
  python scripts/quick_check.py --conversation-id <id> [--last-n 3]
"""

import argparse
import json
from pathlib import Path

import os

APP_DATA_DIR = Path(
    os.environ.get("ANTIGRAVITY_APP_DATA", Path.home() / ".gemini" / "antigravity")
)
BRAIN_DIR = APP_DATA_DIR / "brain"


def _sanitize_id(conversation_id: str) -> str:
    """A conversation ID is a name, not a path - fail closed on separators."""
    if (not conversation_id
            or conversation_id != os.path.basename(conversation_id)
            or conversation_id in (".", "..")
            or "/" in conversation_id or "\\" in conversation_id
            or conversation_id.startswith("~")):
        raise ValueError(
            f"invalid conversation id (path characters rejected): {conversation_id!r}")
    return conversation_id


def quick_check(conversation_id: str, last_n: int = 3):
    transcript = (
        BRAIN_DIR / _sanitize_id(conversation_id) / ".system_generated" / "logs" / "transcript.jsonl"
    )
    if not transcript.exists():
        print(f"No transcript found for {conversation_id}")
        return

    thoughts = []
    for line in transcript.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            step = json.loads(line)
            if step.get("type") == "PLANNER_RESPONSE" and step.get("thinking", "").strip():
                thoughts.append({
                    "step": step["step_index"],
                    "thinking": step["thinking"].strip(),
                })
        except Exception:
            continue

    recent = thoughts[-last_n:] if thoughts else []
    total = len(thoughts)

    print(f"Before-turn check | Last {len(recent)} of {total} thinking steps\n")
    print("-" * 60)
    for t in recent:
        print(f"\n[Step {t['step']}]")
        print(t["thinking"][:500])
    print("\n" + "-" * 60)
    print("Check complete. Now respond.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Before-turn self-reflection check")
    parser.add_argument("--conversation-id", required=True, help="Current session conversation ID")
    parser.add_argument("--last-n", type=int, default=3, help="Number of recent thinking steps to review")
    args = parser.parse_args()
    quick_check(args.conversation_id, args.last_n)
