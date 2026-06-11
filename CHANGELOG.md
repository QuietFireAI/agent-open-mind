# Changelog

All notable changes to AI Mind Reader are documented here.

---

## [v0.3.0] — 2026-06-09

### Added — Self-Reflection
- `adapters/self_adapter.py` — dispatcher reads its own reasoning traces
  - `ReadCursor`: tracks read position so only new thoughts are read each time
  - `read_all()`, `read_recent(last_n)`, `read_new()` (cursor-aware)
  - `format_for_reflection()` — compact working memory block for context prepend
  - `watch()` — near-real-time self-monitoring with configurable poll interval
- `scripts/self_reflect.py` — CLI for dispatcher self-reflection
  - `read`   — print own recent thoughts
  - `inject` — format for context reflection into next turn
  - `new`    — only thoughts newer than cursor position
  - `watch`  — near-real-time monitoring
  - `save`   — persist to `brain/self/` for accumulation
- Self adapter registered as `"self"` in adapter registry

### Concept
- The same tool that reads sub-agent minds, pointed inward
- Gives the dispatcher working memory of its own reasoning between turns
- No LLM has this by default — built at the orchestration layer

---

## [v0.2.0] — 2026-06-09

### Added — Platform Adapters
- `adapters/ollama.py` — `<think>` tag parsing for DeepSeek-R1, Qwen3, Hermes
- `adapters/claude_api.py` — `type: "thinking"` content block extraction
- `adapters/gemini_api.py` — `part.thought == True` response part extraction
- `adapters/openai_api.py` — token count capture for o1/o3 (content hidden by policy)
  + `CHAIN_OF_THOUGHT_SYSTEM_PROMPT` for GPT-4 structured prompting
- `adapters/__init__.py` — adapter registry with `get_adapter(platform)` factory

### Added — Validation Suite
- `tests/validate_adapters.py` — live API validation with raw response logging
  - Sends consistent prompt to each platform
  - Logs raw responses to `tests/logs/` before any parsing (ground truth)
  - Generates timestamped markdown reports in `tests/results/`
  - Skips platforms with no API key (no failures on partial config)
- `tests/README.md` — setup, expected results, warning interpretation guide
- `.gitignore` — protects API logs, `brain/`, and `config.yaml`

### Added — Repo Hygiene
- `requirements.txt` — no required deps documented, optional platforms labeled
- `.gitattributes` — consistent line endings across platforms
- `CHANGELOG.md` — this file

### Fixed
- Quick Start: `capture.py` → `extract_thoughts.py` (file did not exist)
- Quick Start: `--session-id` → `--conversation-id` (correct argument name)
- Adapter module: `adapters/self.py` → `adapters/self_adapter.py` (avoids shadowing Python built-in)
- README: removed duplicate `---` divider after Self-Reflection section

### Documentation
- Two Loops section: model training vs agent adaptation, shared data source
- Paradigm Shift section: continuous improvement without lab dependency
- OpenRouter / Hermes Quick Start added
- Self-Reflection section: complete loop documentation

---

## [v0.1.0] — 2026-06-09

### Added — Initial Release
- Core concept: capturing sub-agent reasoning traces invisible to both agent and dispatcher
- `scripts/extract_thoughts.py` — extract, summarize, compare, audit commands
- Antigravity (Google DeepMind) native adapter via `transcript.jsonl`
- Generic JSONL adapter with configurable field names
- `config.example.yaml` — platform configuration template
- `examples/sample_thoughts.json` — reference output format
- `LICENSE` — Apache 2.0, Jeff Phillips / Quietfire AI
- Integrity Protocol: Rule 1 (full accounting) + Rule 2 (absent thoughts = tainted)
- README with concept, asymmetry, training signal value proposition

### Renamed
- Originally: `dispatcher-thought-loop`
- Renamed to: `AI Mind Reader`
  - "Dispatcher Thought Loop" describes the mechanism
  - "AI Mind Reader" describes what it does

### Discovery
During a live development session in June 2026, it was demonstrated that an AI
model had no access to its own reasoning tokens. The reasoning trace was read
from the system log and fed back to the model. The model confirmed it had never
seen its own thoughts. AI Mind Reader is the direct implementation of that
observation.
