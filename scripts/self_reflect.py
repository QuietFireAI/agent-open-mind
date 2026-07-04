#!/usr/bin/env python3
"""
AI Mind Reader - Self Reflect
The dispatcher reads its own thoughts between turns.

This closes the loop: AI Mind Reader can read sub-agent minds
AND its own. The same tool. Pointed inward.

Commands:
  self_reflect.py read --conversation-id <id> [--last-n 5]
  self_reflect.py reflect --conversation-id <id> [--last-n 5]
  self_reflect.py new --conversation-id <id>
  self_reflect.py watch --conversation-id <id> [--interval 2]
  self_reflect.py save --conversation-id <id> [--last-n 5] --output <file>

Configuration:
  MIND_READER_OWN_ID       Your dispatcher conversation ID (avoids passing every time)
  DISPATCHER_BRAIN_DIR     Path to brain directory

Typical dispatcher workflow:
  1. Complete a set of sub-agent tasks
  2. Before next delegation, run:
       python scripts/self_reflect.py reflect --last-n 5
  3. Prepend the output to your next context turn
  4. Dispatcher now knows what it just reasoned through
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from adapters.self_adapter import SelfAdapter


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

def cmd_read(adapter: SelfAdapter, last_n: int):
    """Print recent own thoughts as readable text."""
    steps = adapter.read_recent(last_n=last_n)

    if not steps:
        print("No thinking steps found in own transcript yet.")
        print(f"Transcript path: {adapter.transcript_path}")
        return

    print(f"\n{'=' * 60}")
    print(f"Own Reasoning - Last {len(steps)} Thinking Steps")
    print(f"Conversation: {adapter.conversation_id}")
    print(f"{'=' * 60}\n")

    for s in steps:
        step_id = s.get("step_index", "?")
        ts = s.get("created_at", "")[:19] if s.get("created_at") else ""
        tools = s.get("tool_calls", [])

        print(f"Step {step_id}" + (f"  [{ts}]" if ts else ""))
        if tools:
            print(f"Tools: {', '.join(tools)}")
        print(f"\nThinking:")
        print(f"  {s['thinking']}")
        if s.get("content"):
            preview = s["content"][:200] + ("..." if len(s["content"]) > 200 else "")
            print(f"\nSaid aloud:")
            print(f"  {preview}")
        print(f"\n{'-' * 40}\n")

    print(f"Total: {len(steps)} step(s) shown")


def cmd_reflect(adapter: SelfAdapter, last_n: int):
    """
    Print the reflection block - ready to prepend to the next dispatcher context.
    
    Pipe this into your dispatcher's next turn to give it working memory
    of its own recent reasoning.
    
    Example:
        python scripts/self_reflect.py reflect --last-n 5 > /tmp/my_thoughts.md
        # Then prepend /tmp/my_thoughts.md to next context
    """
    steps = adapter.read_recent(last_n=last_n)

    if not steps:
        print("<!-- No own thoughts available yet -->")
        return

    print(adapter.format_for_reflection(steps))


def cmd_new(adapter: SelfAdapter):
    """Print only thinking steps newer than the last cursor position."""
    steps = adapter.read_new()

    if not steps:
        print("No new thinking steps since last read.")
        return

    print(f"\n{len(steps)} new thinking step(s) since last read:\n")
    for s in steps:
        print(f"[Step {s.get('step_index', '?')}] {s['thinking'][:300]}")
        print()


def cmd_watch(adapter: SelfAdapter, interval: float):
    """
    Monitor own transcript for new thoughts in near-real-time.
    Prints new thinking steps as they're logged.
    
    The lag is: one completed dispatcher step + poll interval.
    This is the minimum possible - you cannot read a thought
    while it is still being generated.
    """
    print(f"Self-watch active. Lag: ~{interval}s after each completed step.")
    print("The dispatcher reads its own thoughts between turns.\n")

    def on_new_thoughts(steps: list):
        now = datetime.now(timezone.utc).isoformat()[:19]
        print(f"\n[{now}] {len(steps)} new thought(s):")
        for s in steps:
            print(f"\n  Step {s.get('step_index', '?')}:")
            print(f"  {s['thinking'][:400]}")
        print()

    adapter.watch(callback=on_new_thoughts, poll_interval_seconds=interval)


def cmd_save(adapter: SelfAdapter, last_n: int, output_path: str):
    """
    Save recent own thoughts to a file in brain/self/.
    Accumulates the dispatcher's own reasoning history.
    """
    steps = adapter.read_recent(last_n=last_n)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "conversation_id": adapter.conversation_id,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "last_n": last_n,
        "thought_count": len(steps),
        "source": "self",
        "thoughts": steps,
    }

    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(steps)} own thinking steps → {out.resolve()}")

    # Also write a markdown summary alongside
    md_path = out.with_suffix(".md")
    injection = adapter.format_for_reflection(steps)
    md_path.write_text(injection, encoding="utf-8")
    print(f"Summary → {md_path.resolve()}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AI Mind Reader - Self Reflect: the dispatcher reads its own thoughts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
The same tool that reads sub-agent minds, pointed inward.

Between turns, the dispatcher can read its own recent reasoning
and inject it as working memory into the next turn's context.

The lag is one completed step. You cannot read a thought as it
forms - only after the step completes. This is how human introspection
works too.
        """
    )

    parser.add_argument(
        "--conversation-id", "-c",
        help="Your own conversation ID (or set MIND_READER_OWN_ID)",
    )
    parser.add_argument(
        "--brain-dir",
        help="Brain directory path (or set DISPATCHER_BRAIN_DIR)",
    )
    parser.add_argument(
        "--platform",
        default="antigravity",
        choices=["antigravity", "generic"],
        help="Platform log format (default: antigravity)",
    )

    subparsers = parser.add_subparsers(dest="command")

    # read
    p_read = subparsers.add_parser("read", help="Print recent own thoughts")
    p_read.add_argument("--last-n", type=int, default=5,
                        help="How many recent steps to read (default: 5)")

    # inject
    p_reflect = subparsers.add_parser(
        "reflect",
        help="Print reflection block for prepending to next context turn"
    )
    p_reflect.add_argument("--last-n", type=int, default=5)

    # new
    subparsers.add_parser("new", help="Print only thoughts newer than last cursor position")

    # watch
    p_watch = subparsers.add_parser(
        "watch",
        help="Monitor own transcript for new thoughts in near-real-time"
    )
    p_watch.add_argument("--interval", type=float, default=2.0,
                         help="Poll interval in seconds (default: 2.0)")

    # save
    p_save = subparsers.add_parser("save", help="Save own thoughts to brain/self/")
    p_save.add_argument("--last-n", type=int, default=5)
    p_save.add_argument("--output", required=True,
                        help="Output JSON file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Build adapter
    try:
        adapter = SelfAdapter(
            conversation_id=args.conversation_id,
            brain_dir=args.brain_dir,
            platform=args.platform,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Dispatch
    if args.command == "read":
        cmd_read(adapter, args.last_n)
    elif args.command == "reflect":
        cmd_reflect(adapter, args.last_n)
    elif args.command == "new":
        cmd_new(adapter)
    elif args.command == "watch":
        cmd_watch(adapter, args.interval)
    elif args.command == "save":
        cmd_save(adapter, args.last_n, args.output)


if __name__ == "__main__":
    main()
