#!/usr/bin/env python3
"""
extract_thoughts.py — Dispatcher Thought Loop utility
Extracts and analyzes sub-agent thinking traces from agent conversation logs.

Supports configurable platforms via config.yaml or environment variables.

Usage:
  python extract_thoughts.py extract   --conversation-id <id> --output <file>
  python extract_thoughts.py summarize --input <file> --output <file>
  python extract_thoughts.py compare   --inputs <file> <file> --output <file>
  python extract_thoughts.py audit     --registry <file>

Configuration (config.yaml or env vars):
  DISPATCHER_BRAIN_DIR     Path to brain directory (default: ./brain)
  DISPATCHER_PLATFORM      Platform adapter (default: generic)
  DISPATCHER_LOG_PATH      Full path to log file (overrides brain dir)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    """Load configuration from config.yaml if present, with env var overrides."""
    config = {
        "brain_dir": os.environ.get("DISPATCHER_BRAIN_DIR", "./brain"),
        "platform": os.environ.get("DISPATCHER_PLATFORM", "generic"),
        "log_schema": {
            "step_type_field": "type",
            "step_type_value": "PLANNER_RESPONSE",
            "thinking_field": "thinking",
            "content_field": "content",
            "step_index_field": "step_index",
            "timestamp_field": "created_at",
            "tool_calls_field": "tool_calls",
            "tool_name_field": "name",
        }
    }

    config_path = Path("config.yaml")
    if config_path.exists():
        try:
            import yaml  # optional dependency
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
            if user_config:
                if "brain_dir" in user_config:
                    config["brain_dir"] = user_config["brain_dir"]
                if "platform" in user_config:
                    config["platform"] = user_config["platform"]
                if "log_schema" in user_config:
                    config["log_schema"].update(user_config["log_schema"])
        except ImportError:
            pass  # yaml not installed, use defaults

    return config


CONFIG = load_config()
BRAIN_DIR = Path(CONFIG["brain_dir"])
SCHEMA = CONFIG["log_schema"]


# ─────────────────────────────────────────────────────────────────────────────
# Platform adapters
# ─────────────────────────────────────────────────────────────────────────────

def get_log_path(conversation_id: str) -> Path:
    """
    Resolve the log file path for a given conversation/agent ID.
    Override DISPATCHER_LOG_PATH env var for custom paths.
    """
    if os.environ.get("DISPATCHER_LOG_PATH"):
        return Path(os.environ["DISPATCHER_LOG_PATH"])

    platform = CONFIG["platform"]

    if platform == "antigravity":
        # Antigravity (Google DeepMind) structure
        # Brain dir is typically: <AppDataDir>/brain/
        return BRAIN_DIR / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"

    # Generic: brain/<conversation_id>/transcript.jsonl
    return BRAIN_DIR / conversation_id / "transcript.jsonl"


def parse_step(line: str) -> dict | None:
    """Parse a single JSONL line into a step dict. Returns None if not a thinking step."""
    try:
        step = json.loads(line.strip())
    except (json.JSONDecodeError, ValueError):
        return None

    # Check step type
    type_field = SCHEMA["step_type_field"]
    type_value = SCHEMA["step_type_value"]
    if step.get(type_field) != type_value:
        return None

    # Extract thinking
    thinking = step.get(SCHEMA["thinking_field"], "").strip()
    if not thinking:
        return None

    # Extract tool calls
    tool_calls_raw = step.get(SCHEMA["tool_calls_field"], [])
    tool_names = []
    if isinstance(tool_calls_raw, list):
        for tc in tool_calls_raw:
            if isinstance(tc, dict):
                name = tc.get(SCHEMA["tool_name_field"], "")
                if name:
                    tool_names.append(name)

    return {
        "step_index": step.get(SCHEMA["step_index_field"]),
        "created_at": step.get(SCHEMA["timestamp_field"]),
        "thinking": thinking,
        "content": step.get(SCHEMA["content_field"], "").strip(),
        "tool_calls": tool_names,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

def extract_thoughts(conversation_id: str, output_path: str):
    """Extract all thinking traces from a sub-agent's log."""
    log_path = get_log_path(conversation_id)

    if not log_path.exists():
        print(f"ERROR: Log not found at {log_path}", file=sys.stderr)
        print(f"  Set DISPATCHER_BRAIN_DIR or DISPATCHER_LOG_PATH to override.", file=sys.stderr)
        sys.exit(1)

    thoughts = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            step = parse_step(line)
            if step:
                thoughts.append(step)

    result = {
        "conversation_id": conversation_id,
        "platform": CONFIG["platform"],
        "log_path": str(log_path),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "thought_count": len(thoughts),
        "tainted": len(thoughts) == 0,
        "thoughts": thoughts,
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    if len(thoughts) == 0:
        print(f"WARNING: Zero thinking traces found. Result should be considered TAINTED.", file=sys.stderr)
        print(f"  Trigger HITL review. Spawn replacement agent. Do not use this result.", file=sys.stderr)
    else:
        print(f"Extracted {len(thoughts)} thinking traces → {out.resolve()}")


def summarize_thoughts(input_path: str, output_path: str):
    """Summarize extracted thoughts as readable markdown."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lines = [
        "# Thought Trace Summary",
        "",
        f"**Conversation ID:** `{data['conversation_id']}`  ",
        f"**Platform:** {data.get('platform', 'unknown')}  ",
        f"**Extracted:** {data['extracted_at']}  ",
        f"**Total thinking steps:** {data['thought_count']}  ",
        f"**Status:** {'⚠️ TAINTED — zero thoughts, HITL required' if data.get('tainted') else '✅ Valid'}  ",
        "",
        "---",
        "",
    ]

    if data.get("tainted"):
        lines += [
            "## ⚠️ TAINTED RESULT",
            "",
            "This agent completed its task with zero thinking traces.",
            "Per Dispatcher Integrity Protocol Rule 2:",
            "",
            "- This result is IGNORED",
            "- HITL review is MANDATORY",
            "- A replacement agent MUST be spawned",
            "- Compare replacement traces against this null record",
            "",
            "---",
            "",
        ]

    for i, t in enumerate(data["thoughts"], 1):
        lines.append(f"## Step {t['step_index']} — Thought {i}")
        if t.get("created_at"):
            lines.append(f"*{t['created_at']}*")
        lines.append("")
        lines.append("**Thinking:**")
        lines.append(f"> {t['thinking']}")
        lines.append("")
        if t.get("content"):
            preview = t["content"][:400]
            if len(t["content"]) > 400:
                preview += "..."
            lines.append("**Said aloud:**")
            lines.append(f"> {preview}")
            lines.append("")
        if t.get("tool_calls"):
            lines.append(f"**Tools called:** {', '.join(t['tool_calls'])}")
            lines.append("")
        lines.append("---")
        lines.append("")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Summary written → {out.resolve()}")


def compare_thoughts(input_paths: list, output_path: str):
    """Compare thought traces from two agents on the same task."""
    if len(input_paths) != 2:
        print("ERROR: compare requires exactly 2 input files.", file=sys.stderr)
        sys.exit(1)

    datasets = []
    for p in input_paths:
        with open(p, "r", encoding="utf-8") as f:
            datasets.append(json.load(f))

    a, b = datasets
    a_tainted = a.get("tainted", False)
    b_tainted = b.get("tainted", False)

    lines = [
        "# Thought Trace Comparison",
        "",
        f"**Agent A:** `{a['conversation_id']}` — {a['thought_count']} thoughts {'⚠️ TAINTED' if a_tainted else '✅'}  ",
        f"**Agent B:** `{b['conversation_id']}` — {b['thought_count']} thoughts {'⚠️ TAINTED' if b_tainted else '✅'}  ",
        "",
    ]

    if a_tainted or b_tainted:
        lines += [
            "## ⚠️ Tainted Agent Detected",
            "",
            "One or both agents returned zero thinking traces.",
            "This comparison serves as diagnostic evidence for HITL review.",
            "The non-tainted agent's traces show what reasoning the tainted agent should have produced.",
            "",
            "---",
            "",
        ]

    lines += ["## Agent A — Reasoning Patterns", ""]
    if a_tainted:
        lines.append("*No thinking traces. Result is TAINTED.*")
    else:
        for t in a["thoughts"]:
            lines.append(f"- **[Step {t['step_index']}]** {t['thinking'][:250]}")
    lines += ["", "## Agent B — Reasoning Patterns", ""]
    if b_tainted:
        lines.append("*No thinking traces. Result is TAINTED.*")
    else:
        for t in b["thoughts"]:
            lines.append(f"- **[Step {t['step_index']}]** {t['thinking'][:250]}")

    lines += [
        "",
        "---",
        "",
        "## Dispatcher Notes",
        "",
        "*(Record observations here: reasoning divergence, which approach was more effective,",
        "what assumptions differed, what to carry forward into future delegations)*",
        "",
        "| Dimension | Agent A | Agent B |",
        "|---|---|---|",
        "| Thought count | " + str(a['thought_count']) + " | " + str(b['thought_count']) + " |",
        "| Status | " + ("TAINTED" if a_tainted else "Valid") + " | " + ("TAINTED" if b_tainted else "Valid") + " |",
        "| Key assumption | | |",
        "| Hesitation point | | |",
        "| Approach | | |",
        "| Recommended for future | | |",
        "",
    ]

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Comparison written → {out.resolve()}")


def audit_registry(registry_path: str):
    """
    Audit a dispatcher registry file for unaccounted agents.
    Registry format: JSON array of {conversation_id, task, status, thoughts_path}
    """
    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    issues = []
    for entry in registry:
        cid = entry.get("conversation_id", "unknown")
        status = entry.get("status", "unknown")
        thoughts_path = entry.get("thoughts_path")

        if status not in ("completed", "running", "failed"):
            issues.append(f"UNACCOUNTED: {cid} — status '{status}' is not recognized")

        if status == "completed":
            if not thoughts_path:
                issues.append(f"TAINTED: {cid} — completed but no thoughts_path recorded")
            elif not Path(thoughts_path).exists():
                issues.append(f"TAINTED: {cid} — thoughts file missing: {thoughts_path}")
            else:
                with open(thoughts_path) as f:
                    data = json.load(f)
                if data.get("tainted") or data.get("thought_count", 0) == 0:
                    issues.append(f"TAINTED: {cid} — zero thoughts, HITL required")

    if issues:
        print(f"\n⚠️  Registry audit found {len(issues)} issue(s):\n")
        for issue in issues:
            print(f"  • {issue}")
        print("\nDispatcher must resolve all issues before proceeding.")
        sys.exit(1)
    else:
        print(f"✅ Registry audit clean — {len(registry)} agents accounted for.")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Dispatcher Thought Loop — extract and analyze sub-agent reasoning traces",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
  DISPATCHER_BRAIN_DIR    Path to brain directory
  DISPATCHER_PLATFORM     Platform adapter (antigravity, generic)
  DISPATCHER_LOG_PATH     Direct path to log file (overrides brain dir)
        """
    )
    subparsers = parser.add_subparsers(dest="command")

    p_extract = subparsers.add_parser("extract", help="Extract thinking traces from a log")
    p_extract.add_argument("--conversation-id", required=True, help="Sub-agent conversation/session ID")
    p_extract.add_argument("--output", required=True, help="Output JSON file path")

    p_summarize = subparsers.add_parser("summarize", help="Summarize extracted thoughts as markdown")
    p_summarize.add_argument("--input", required=True)
    p_summarize.add_argument("--output", required=True)

    p_compare = subparsers.add_parser("compare", help="Compare thoughts from two agents")
    p_compare.add_argument("--inputs", required=True, nargs=2)
    p_compare.add_argument("--output", required=True)

    p_audit = subparsers.add_parser("audit", help="Audit dispatcher registry for unaccounted agents")
    p_audit.add_argument("--registry", required=True, help="Path to registry JSON file")

    args = parser.parse_args()

    if args.command == "extract":
        extract_thoughts(args.conversation_id, args.output)
    elif args.command == "summarize":
        summarize_thoughts(args.input, args.output)
    elif args.command == "compare":
        compare_thoughts(args.inputs, args.output)
    elif args.command == "audit":
        audit_registry(args.registry)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
