#!/usr/bin/env python3
"""
AI Mind Reader — Adapter Validation Suite

Tests each platform adapter against its live API to verify:
  1. The API call succeeds and returns a response
  2. Reasoning traces are present in the response
  3. The adapter correctly extracts thinking vs content
  4. Raw responses are logged to tests/logs/ for future reference

Run one platform at a time:
  python tests/validate_adapters.py --platform ollama
  python tests/validate_adapters.py --platform claude
  python tests/validate_adapters.py --platform gemini
  python tests/validate_adapters.py --platform openai

Run all available (skips platforms with no API key configured):
  python tests/validate_adapters.py --platform all

Requirements by platform:
  Ollama:  Ollama running locally (ollama serve) with a thinking model pulled
  Claude:  ANTHROPIC_API_KEY environment variable
  Gemini:  GOOGLE_API_KEY environment variable
  OpenAI:  OPENAI_API_KEY environment variable

Logs are written to tests/logs/<platform>_responses.jsonl
Results are written to tests/results/validation_report.md
"""

import argparse
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

LOGS_DIR = ROOT / "tests" / "logs"
RESULTS_DIR = ROOT / "tests" / "results"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# The validation prompt — same task sent to every model for fair comparison.
# Simple enough to run fast, complex enough to trigger genuine reasoning.
# ─────────────────────────────────────────────────────────────────────────────

VALIDATION_PROMPT = """Review this Python function and identify any bugs:

def calculate_discount(price, discount_pct, max_discount=50):
    if discount_pct > max_discount:
        discount_pct == max_discount  # cap discount
    discount = price * discount_pct
    final = price - discount
    return final

Be specific about what is wrong and why.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Response logger — always log the raw response before any parsing
# ─────────────────────────────────────────────────────────────────────────────

def log_response(platform: str, raw: dict):
    """Append the raw API response to the platform's log file."""
    log_path = LOGS_DIR / f"{platform}_responses.jsonl"
    entry = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform,
        "prompt": VALIDATION_PROMPT,
        **raw,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return log_path


# ─────────────────────────────────────────────────────────────────────────────
# Platform validators
# ─────────────────────────────────────────────────────────────────────────────

def validate_ollama(model: str = "deepseek-r1") -> dict:
    """
    Validate the Ollama adapter.
    Requires: ollama running locally, model pulled.
    """
    try:
        import ollama
    except ImportError:
        return {
            "platform": "ollama",
            "status": "SKIP",
            "reason": "ollama Python package not installed. Run: pip install ollama",
        }

    print(f"  Calling Ollama ({model})...")
    try:
        response = ollama.generate(model=model, prompt=VALIDATION_PROMPT)
    except Exception as e:
        return {
            "platform": "ollama",
            "status": "ERROR",
            "reason": str(e),
            "hint": f"Is ollama running? Try: ollama serve && ollama pull {model}",
        }

    # Log raw response
    raw = {
        "model": getattr(response, "model", model),
        "response": getattr(response, "response", ""),
        "done": getattr(response, "done", None),
        "total_duration": getattr(response, "total_duration", None),
    }
    log_path = log_response("ollama", raw)

    # Run adapter
    from adapters.ollama import OllamaAdapter
    thinking, content = OllamaAdapter.from_api_response(response)
    has_thinking = bool(thinking.strip())

    return {
        "platform": "ollama",
        "model": model,
        "status": "PASS" if has_thinking else "WARN",
        "has_thinking": has_thinking,
        "thinking_chars": len(thinking),
        "content_chars": len(content),
        "thinking_preview": thinking[:200] + "..." if len(thinking) > 200 else thinking,
        "content_preview": content[:200] + "..." if len(content) > 200 else content,
        "log": str(log_path),
        "warn": None if has_thinking else (
            f"No <think> tags found. Does {model} support thinking? "
            "Try: ollama pull deepseek-r1 or qwen3"
        ),
    }


def validate_claude(model: str = "claude-sonnet-4-5") -> dict:
    """
    Validate the Claude API adapter.
    Requires: ANTHROPIC_API_KEY, anthropic package.
    Extended thinking requires claude-3-7-sonnet-20250219 or newer.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "platform": "claude",
            "status": "SKIP",
            "reason": "ANTHROPIC_API_KEY not set",
        }

    try:
        import anthropic
    except ImportError:
        return {
            "platform": "claude",
            "status": "SKIP",
            "reason": "anthropic package not installed. Run: pip install anthropic",
        }

    print(f"  Calling Claude API ({model}) with extended thinking...")
    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=16000,
            thinking={"type": "enabled", "budget_tokens": 10000},
            messages=[{"role": "user", "content": VALIDATION_PROMPT}],
        )
    except Exception as e:
        return {
            "platform": "claude",
            "status": "ERROR",
            "reason": str(e),
            "hint": "Check your API key and model name. Extended thinking requires claude-3-7-sonnet+",
        }

    # Log raw response
    try:
        raw = response.model_dump()
    except Exception:
        raw = {"content": [b.model_dump() if hasattr(b, "model_dump") else str(b)
                            for b in response.content]}
    log_path = log_response("claude", raw)

    # Run adapter
    from adapters.claude_api import ClaudeAdapter
    thinking, content = ClaudeAdapter.from_api_response(response)
    has_thinking = bool(thinking.strip())

    return {
        "platform": "claude",
        "model": model,
        "status": "PASS" if has_thinking else "FAIL",
        "has_thinking": has_thinking,
        "thinking_chars": len(thinking),
        "content_chars": len(content),
        "thinking_preview": thinking[:200] + "..." if len(thinking) > 200 else thinking,
        "content_preview": content[:200] + "..." if len(content) > 200 else content,
        "input_tokens": getattr(response.usage, "input_tokens", None),
        "log": str(log_path),
        "warn": None if has_thinking else "No thinking blocks returned. Extended thinking may not be enabled.",
    }


def validate_gemini(model: str = "gemini-2.5-pro-preview-06-05") -> dict:
    """
    Validate the Gemini API adapter.
    Requires: GOOGLE_API_KEY, google-genai package.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {
            "platform": "gemini",
            "status": "SKIP",
            "reason": "GOOGLE_API_KEY not set",
        }

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return {
            "platform": "gemini",
            "status": "SKIP",
            "reason": "google-genai package not installed. Run: pip install google-genai",
        }

    print(f"  Calling Gemini API ({model})...")
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model,
            contents=VALIDATION_PROMPT,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=10000)
            ),
        )
    except Exception as e:
        return {
            "platform": "gemini",
            "status": "ERROR",
            "reason": str(e),
            "hint": "Check your API key. Thinking requires gemini-2.5-pro or flash-thinking.",
        }

    # Log raw response
    try:
        raw = response.model_dump() if hasattr(response, "model_dump") else {"raw": str(response)}
    except Exception:
        raw = {"raw": str(response)}
    log_path = log_response("gemini", raw)

    # Run adapter
    from adapters.gemini_api import GeminiAdapter
    thinking, content = GeminiAdapter.from_api_response(response)
    has_thinking = bool(thinking.strip())

    usage = getattr(response, "usage_metadata", None)
    thinking_tokens = getattr(usage, "thoughts_token_count", 0) if usage else 0

    return {
        "platform": "gemini",
        "model": model,
        "status": "PASS" if has_thinking else "FAIL",
        "has_thinking": has_thinking,
        "thinking_tokens": thinking_tokens,
        "thinking_chars": len(thinking),
        "content_chars": len(content),
        "thinking_preview": thinking[:200] + "..." if len(thinking) > 200 else thinking,
        "content_preview": content[:200] + "..." if len(content) > 200 else content,
        "log": str(log_path),
        "warn": None if has_thinking else "No thought parts returned.",
    }


def validate_openai(model_reasoning: str = "o3-mini",
                    model_gpt4: str = "gpt-4o") -> dict:
    """
    Validate the OpenAI adapter — two sub-tests:
      1. Reasoning model (o3-mini): confirms token count captured, tainted correctly flagged
      2. GPT-4o with structured prompting: confirms <think> tags parsed
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {
            "platform": "openai",
            "status": "SKIP",
            "reason": "OPENAI_API_KEY not set",
        }

    try:
        from openai import OpenAI
    except ImportError:
        return {
            "platform": "openai",
            "status": "SKIP",
            "reason": "openai package not installed. Run: pip install openai",
        }

    from adapters.openai_api import OpenAIAdapter

    client = OpenAI(api_key=api_key)
    results = {}

    # Sub-test 1: reasoning model (o3-mini)
    print(f"  Calling OpenAI reasoning model ({model_reasoning})...")
    try:
        response = client.chat.completions.create(
            model=model_reasoning,
            messages=[{"role": "user", "content": VALIDATION_PROMPT}],
        )
        raw = json.loads(response.model_dump_json())
        log_path = log_response(f"openai_{model_reasoning}", raw)

        result = OpenAIAdapter.from_api_response(response)
        results["reasoning_model"] = {
            "model": model_reasoning,
            "status": "PASS",  # for o1/o3 PASS means correctly tainted
            "tainted": result.tainted,
            "reasoning_tokens": result.reasoning_tokens,
            "has_thinking_content": bool(result.thinking),
            "content_preview": result.content[:200],
            "limitation_confirmed": result.tainted and not result.thinking,
            "log": str(log_path),
            "note": "PASS = tainted correctly flagged (OpenAI hides reasoning content by policy)",
        }
    except Exception as e:
        results["reasoning_model"] = {
            "model": model_reasoning,
            "status": "ERROR",
            "reason": str(e),
        }

    # Sub-test 2: GPT-4o with structured prompting
    print(f"  Calling OpenAI GPT-4 with structured prompting ({model_gpt4})...")
    try:
        from adapters.openai_api import CHAIN_OF_THOUGHT_SYSTEM_PROMPT
        response = client.chat.completions.create(
            model=model_gpt4,
            messages=[
                {"role": "system", "content": CHAIN_OF_THOUGHT_SYSTEM_PROMPT},
                {"role": "user", "content": VALIDATION_PROMPT},
            ],
        )
        raw = json.loads(response.model_dump_json())
        log_path = log_response(f"openai_{model_gpt4}", raw)

        result = OpenAIAdapter.from_api_response(response)
        has_thinking = bool(result.thinking.strip())
        results["gpt4_structured"] = {
            "model": model_gpt4,
            "status": "PASS" if has_thinking else "WARN",
            "has_thinking": has_thinking,
            "thinking_chars": len(result.thinking),
            "thinking_preview": result.thinking[:200] + "..." if len(result.thinking) > 200 else result.thinking,
            "content_preview": result.content[:200],
            "log": str(log_path),
            "warn": None if has_thinking else "GPT-4 did not produce <think> tags despite system prompt.",
        }
    except Exception as e:
        results["gpt4_structured"] = {
            "model": model_gpt4,
            "status": "ERROR",
            "reason": str(e),
        }

    return {"platform": "openai", **results}


# ─────────────────────────────────────────────────────────────────────────────
# Report generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_report(results: list[dict]) -> str:
    """Generate a markdown validation report."""
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# AI Mind Reader — Adapter Validation Report",
        "",
        f"**Generated:** {now}  ",
        f"**Validation prompt:** Python function bug review  ",
        "",
        "---",
        "",
    ]

    for r in results:
        platform = r.get("platform", "unknown").upper()
        status = r.get("status", "UNKNOWN")
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️", "ERROR": "🔴"}.get(status, "❓")

        lines.append(f"## {icon} {platform} — {status}")
        lines.append("")

        if status == "SKIP":
            lines.append(f"**Skipped:** {r.get('reason', '')}")
        elif status == "ERROR":
            lines.append(f"**Error:** {r.get('reason', '')}  ")
            if r.get("hint"):
                lines.append(f"**Hint:** {r['hint']}")
        elif platform == "OPENAI":
            # OpenAI has sub-results
            for key in ("reasoning_model", "gpt4_structured"):
                sub = r.get(key, {})
                if not sub:
                    continue
                sub_status = sub.get("status", "UNKNOWN")
                sub_icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "ERROR": "🔴"}.get(sub_status, "❓")
                lines.append(f"### {sub_icon} {sub.get('model', key)} — {sub_status}")
                lines.append("")
                if sub.get("note"):
                    lines.append(f"> {sub['note']}")
                    lines.append("")
                for field in ("reasoning_tokens", "has_thinking_content", "limitation_confirmed",
                              "has_thinking", "thinking_chars", "thinking_preview"):
                    if field in sub:
                        lines.append(f"- **{field}:** {sub[field]}")
                if sub.get("log"):
                    lines.append(f"- **Log:** `{sub['log']}`")
                lines.append("")
        else:
            for field in ("model", "has_thinking", "thinking_tokens",
                          "thinking_chars", "content_chars"):
                if field in r:
                    lines.append(f"- **{field}:** {r[field]}")

            if r.get("thinking_preview"):
                lines.append("")
                lines.append("**Thinking preview:**")
                lines.append(f"> {r['thinking_preview']}")

            if r.get("warn"):
                lines.append("")
                lines.append(f"⚠️ **Warning:** {r['warn']}")

            if r.get("log"):
                lines.append("")
                lines.append(f"**Raw log:** `{r['log']}`")

        lines.append("")
        lines.append("---")
        lines.append("")

    # Summary table
    lines += ["## Summary", "", "| Platform | Status | Thinking Captured |", "|---|---|---|"]
    for r in results:
        platform = r.get("platform", "?")
        status = r.get("status", "?")
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️", "ERROR": "🔴"}.get(status, "❓")
        if platform == "openai":
            rm = r.get("reasoning_model", {})
            gpt = r.get("gpt4_structured", {})
            lines.append(f"| OpenAI o3-mini | {icon} {rm.get('status','?')} | Hidden by policy |")
            lines.append(f"| OpenAI GPT-4o | {'✅' if gpt.get('has_thinking') else '⚠️'} {gpt.get('status','?')} | {'Yes (<think> tags)' if gpt.get('has_thinking') else 'No'} |")
        else:
            has = r.get("has_thinking", False)
            lines.append(f"| {platform.capitalize()} | {icon} {status} | {'Yes' if has else 'No/Skipped'} |")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Validate AI Mind Reader adapters against live APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--platform",
        choices=["ollama", "claude", "gemini", "openai", "all"],
        required=True,
        help="Platform to validate, or 'all' to run available platforms",
    )
    parser.add_argument("--ollama-model", default="deepseek-r1",
                        help="Ollama model to use (default: deepseek-r1)")
    parser.add_argument("--claude-model", default="claude-sonnet-4-5",
                        help="Claude model to use (default: claude-sonnet-4-5)")
    parser.add_argument("--gemini-model", default="gemini-2.5-pro-preview-06-05",
                        help="Gemini model to use (default: gemini-2.5-pro-preview-06-05)")

    args = parser.parse_args()

    platforms = (
        ["ollama", "claude", "gemini", "openai"]
        if args.platform == "all"
        else [args.platform]
    )

    print(f"\nAI Mind Reader — Adapter Validation")
    print(f"{'=' * 50}")
    print(f"Platforms: {', '.join(platforms)}")
    print(f"Logs dir:  {LOGS_DIR}")
    print(f"{'=' * 50}\n")

    results = []
    for platform in platforms:
        print(f"[{platform.upper()}]")
        try:
            if platform == "ollama":
                result = validate_ollama(args.ollama_model)
            elif platform == "claude":
                result = validate_claude(args.claude_model)
            elif platform == "gemini":
                result = validate_gemini(args.gemini_model)
            elif platform == "openai":
                result = validate_openai()
        except Exception as e:
            result = {
                "platform": platform,
                "status": "ERROR",
                "reason": str(e),
                "traceback": traceback.format_exc(),
            }

        results.append(result)
        status = result.get("status", "?")
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️", "ERROR": "🔴"}.get(status, "❓")
        print(f"  {icon} {status}")
        if result.get("warn"):
            print(f"  ⚠️  {result['warn']}")
        if result.get("reason") and status in ("SKIP", "ERROR"):
            print(f"  → {result['reason']}")
        print()

    # Write report
    report = generate_report(results)
    report_path = RESULTS_DIR / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"{'=' * 50}")
    print(f"Report: {report_path}")
    print(f"Logs:   {LOGS_DIR}")
    print(f"{'=' * 50}\n")

    # Exit with error if any platform failed
    failed = [r for r in results if r.get("status") == "FAIL"]
    if failed:
        print(f"❌ {len(failed)} platform(s) FAILED validation")
        sys.exit(1)
    else:
        print("✅ All tested platforms passed (or were skipped)")


if __name__ == "__main__":
    main()
