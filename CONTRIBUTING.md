# Contributing to AI Mind Reader

First - thank you. This project exists because one person noticed something
nobody else had written down. If you're here, you've probably noticed something
too. That's exactly the right reason to contribute.

---

## What We're Building

AI Mind Reader captures the reasoning traces AI agents generate but cannot
access themselves. The goal is a small, focused, dependency-free library that
works across every platform that exposes reasoning content.

**The guiding principle:** Every line of code should serve the core loop - 
capture reasoning, enforce integrity, accumulate knowledge.

---

## Quick Start for Contributors

```bash
git clone https://github.com/QuietfireAI/ai-mind-reader.git
cd ai-mind-reader

# No setup required - core is stdlib only
python -c "from adapters import get_adapter; print('Ready')"

# Run the unit tests (no API keys needed)
python -m pytest tests/unit/ -v

# Run live validation (API keys required per platform)
python tests/validate_adapters.py --platform ollama
```

---

## The Highest-Value Contribution: A New Adapter

If you can add a working, tested adapter for a platform not yet covered,
that is the most valuable thing you can contribute.

### Adapter Requirements

Every adapter must implement:

```python
class MyPlatformAdapter:

    @staticmethod
    def from_api_response(response) -> tuple[str, str]:
        """
        Returns (thinking, content).
        thinking: the raw chain-of-thought, unmodified
        content:  the visible output with thinking removed
        """
        ...

    @staticmethod
    def has_thinking(response) -> bool:
        """True if the response contains at least one thinking block."""
        ...

    @staticmethod
    def read_log(log_path: str) -> list[dict]:
        """
        Read a JSONL log of platform responses.
        Returns list of trace dicts, each with:
          step_index, created_at, thinking, content, tool_calls, model
        """
        ...
```

### Integrity Rule for Adapters

If `has_thinking()` returns False, the result is tainted under the integrity
protocol. Your adapter must never paper over absent thinking - if the platform
didn't return reasoning content, the adapter must surface that honestly.

### Adapter Template

```python
"""
AI Mind Reader - [Platform] Adapter

[Explain how this platform exposes reasoning content]
[Note any requirements: API version, model names, flags to enable thinking]
"""

import json
from pathlib import Path
from datetime import datetime, timezone


class MyAdapter:

    @staticmethod
    def from_api_response(response) -> tuple[str, str]:
        thinking_parts = []
        content_parts = []
        # ... extract from response structure
        return "\n\n".join(thinking_parts), "\n\n".join(content_parts)

    @staticmethod
    def has_thinking(response) -> bool:
        thinking, _ = MyAdapter.from_api_response(response)
        return bool(thinking.strip())

    @staticmethod
    def read_log(log_path: str) -> list[dict]:
        path = Path(log_path)
        if not path.exists():
            raise FileNotFoundError(f"Log not found: {path}")
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
                thinking, content = MyAdapter.from_api_response(entry)
                if not thinking:
                    continue
                traces.append({
                    "step_index": idx,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "thinking": thinking,
                    "content": content,
                    "tool_calls": [],
                    "model": entry.get("model", "unknown"),
                })
        return traces
```

### Register Your Adapter

Add it to `adapters/__init__.py`:

```python
from .my_platform import MyAdapter

ADAPTERS = {
    ...
    "myplatform": MyAdapter,
}
```

### Add Live Validation

Add a `validate_myplatform()` function in `tests/validate_adapters.py`
following the pattern of existing validators. The same prompt goes to every
platform - this is intentional for fair comparison.

### Add Unit Tests

Add `tests/unit/test_my_platform.py` with tests that run without API keys:

```python
def test_parse_response_with_thinking():
    raw = "<think>Let me reason...</think>Here is my answer."
    thinking, content = MyAdapter.parse_response(raw)
    assert "Let me reason" in thinking
    assert "Here is my answer" in content
    assert "<think>" not in content

def test_parse_response_no_thinking():
    raw = "Here is my answer with no thinking."
    thinking, content = MyAdapter.parse_response(raw)
    assert thinking == ""
    assert content == raw
```

---

## Other Ways to Contribute

### Bug Reports
Open an issue using the **Bug Report** template. Include:
- Platform and model name
- The raw API response (sanitize any API keys)
- What the adapter returned vs what you expected

### Documentation
The README and CHANGELOG are the face of this project. Clear, honest writing
that doesn't oversell is more valuable than technical content that misleads.

### Platform Research
Know of a platform that exposes reasoning tokens in a way we haven't covered?
Open a **Feature Request** issue with the API documentation link. Even if you
can't write the adapter yourself, the research helps.

---

## Code Style

- **Python 3.9+** - no walrus operator in public APIs, no 3.10+ match statements
- **No required dependencies** - stdlib only for core. Platform packages are
  optional and must be imported lazily inside the function that needs them
- **Honest documentation** - if a platform hides reasoning content (like OpenAI
  o1/o3), document that clearly. Don't hide limitations.
- **Type hints** on all public methods
- **Docstrings** on all classes and public methods - explain the platform's
  reasoning format, not just what the function does

---

## Pull Request Process

1. Fork the repo and create a branch: `git checkout -b adapter/myplatform`
2. Write the adapter following the template above
3. Add unit tests that pass without API keys
4. Run live validation if you have API access: `python tests/validate_adapters.py --platform myplatform`
5. Update `CHANGELOG.md` under a new `[Unreleased]` section
6. Open a PR - the template will guide you through what to include

PRs that add adapters without unit tests will be asked to add them before merge.
PRs that hide platform limitations will be asked to document them honestly.

---

## The Integrity Protocol Is Non-Negotiable

The two integrity rules in the README are not suggestions. Any contribution
that weakens them - by silently dropping absent traces, by ignoring taint flags,
by proceeding without HITL when required - will not be merged.

*The reasoning trace is the receipt. No receipt, no trust.*

---

## Questions

Open a GitHub Discussion or reach out at jeff@quietfire.ai.
