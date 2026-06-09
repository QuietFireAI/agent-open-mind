# AI Mind Reader

> *"Every AI agent thinks before it acts. You see what it does. You never see what it thought. This project changes that — and turns what it thought into your highest-quality training signal."*

---

## What This Is

AI Mind Reader captures the reasoning traces that AI agents generate during task execution — traces that are invisible to both the agent that produced them and the dispatcher that spawned it.

Those traces are not just logs. They are:

- **The most honest signal of how a capable model reasons on real tasks**
- **Unfiltered** — generated before the model optimizes its output for presentation
- **Grounded** — produced while solving actual problems, not synthetic benchmarks
- **Perishable** — gone after the step completes, unless you capture them

This project captures them. And converts them into training signal.

---

## The Asymmetry

```
Sub-agent generates reasoning tokens → acts → reports result
                    ↓
         Reasoning tokens are logged
                    ↓
    Sub-agent: cannot access its own thoughts after generation
    Dispatcher: never receives them
    External observer (you): CAN read the log
```

**AI Mind Reader is the external observer.**

It reads what the agent thought. The agent doesn't know you're watching.

---

## Why This Is High-Priority Training Data

Most training data is:
- Synthetic (generated, not real)
- Curated for presentation (polished, not raw)
- Outcome-focused (what was produced, not how)

AI Mind Reader produces data that is:
- **Real** — from agents solving actual tasks
- **Raw** — the unfiltered chain of thought before output optimization
- **Process-focused** — HOW the model reasoned, not just WHAT it concluded
- **Graded automatically** — you already know if the result was good, so you know if the reasoning that produced it was effective

This is the training signal loop that scales:

```
Agent reasons on real task
       ↓
AI Mind Reader captures the reasoning trace
       ↓
Trace is filtered: good result = good trace, bad result = diagnostic data
       ↓
Accumulated traces feed back as training signal
       ↓
Next model reasons better on the same class of tasks
       ↓
Better reasoning → better traces → better training
       ↓
(repeat)
```

This is the same loop Andrej Karpathy built in `autoresearch` at the model training layer.  
AI Mind Reader builds it at the agent orchestration layer — above the model, platform-agnostic.

---

## The Integrity Protocol

Two rules govern trace capture. They are not optional.

### Rule 1 — Full Accounting on Every Turn

Every sub-agent spawned must be tracked. Before the dispatcher proceeds:

```
For every agent:
  - Status: completed / running / failed?
  - Traces captured: count > 0?
  - Result: accepted / tainted / pending?
```

### Rule 2 — Absent Thoughts = Tainted Result

Zero reasoning traces = the result is discarded entirely.

```
1. MARK result as TAINTED
2. IGNORE result — do not use it
3. TRIGGER Human-in-the-Loop (HITL) review
4. LOG the incident
5. SPAWN a replacement agent — mandatory, not optional
6. COMPARE replacement traces against the silent agent
     → the delta is diagnostic evidence
7. HOLD replacement result until human approves
8. NEVER proceed without explicit approval
```

**The thought trace is the receipt. No receipt, no trust.**

Absence of reasoning is a signal — not a benign edge case. The agent may have been prompt-injected, short-circuited, or corrupted.

---

## Quick Start

### Ollama (recommended — self-hosted, sovereign)

```bash
# Run a model that surfaces reasoning
ollama run deepseek-r1 "Review this code for security issues: [code]"

# Capture the reasoning trace
python scripts/capture.py extract \
  --platform ollama \
  --session-id <id> \
  --output brain/traces/agent-001.json

# Summarize
python scripts/capture.py summarize \
  --input brain/traces/agent-001.json \
  --output brain/traces/agent-001-summary.md
```

### Antigravity (Google DeepMind)

```bash
# Set your brain directory
export MIND_READER_BRAIN_DIR="C:\Users\YourName\.gemini\antigravity\brain"

python scripts/capture.py extract \
  --platform antigravity \
  --conversation-id <sub-agent-id> \
  --output brain/traces/agent-001.json
```

---

## Platform Support

| Platform | Reasoning Access | Status | Notes |
|---|---|---|---|
| **Ollama** | ✅ `<think>` tags | 🔜 v0.2 | Works with DeepSeek-R1, Qwen3, thinking-enabled Hermes |
| **Antigravity** | ✅ `thinking` field | ✅ v0.1 | Native via `transcript.jsonl` |
| **Claude API** | ✅ `type: thinking` blocks | 🔜 v0.2 | Requires extended thinking enabled |
| **Gemini API** | ✅ `part.thought == True` | 🔜 v0.2 | Gemini 2.5 Pro / Flash Thinking |
| **OpenAI o1/o3** | ❌ Hidden by policy | ⚠️ Limited | Token count only — content not exposed |
| **OpenAI GPT-4** | ⚠️ Prompt engineering | 🔜 v0.2 | Structured prompting fallback |

> OpenAI is the only major platform that actively hides reasoning content from developers.
> This is a policy decision, not a technical limitation.

---

## The Accumulation Model

Over time, AI Mind Reader builds a library of reasoning traces:

```
brain/
  traces/
    code-review-agent-001.json     ← how it reasoned about security
    code-review-agent-002.json     ← different task, different approach
    compliance-agent-001.json      ← how it reasoned about HIPAA
    tainted/
      agent-003-zero-thoughts.json ← incident record, HITL triggered
  patterns/
    INDEX.md                       ← accumulated reasoning patterns
```

The dispatcher accumulates what the agents cannot.  
The agents start fresh every time. The dispatcher does not.

---

## Connection to DispatcherAgents

AI Mind Reader is the cognitive capture layer of the **DispatcherAgents** architecture ([dispatcheragents.com](https://dispatcheragents.com)).

```
DispatcherAgents
├── ClawFilters       ← governs WHAT agents do (trust, permissions, audit)
├── AI Mind Reader    ← captures HOW agents think  ← you are here
└── brain/            ← accumulated knowledge and training signal library
```

---

## Requirements

- Python 3.9+
- No required dependencies (stdlib only)
- Optional: `pyyaml` for config file support

---

## License

Apache 2.0 — see [LICENSE](LICENSE)

---

## Attribution

**Concept, architecture, and integrity protocol:** Jeff Phillips / [Quietfire AI](https://quietfire.ai)  
**Originated:** June 2026  

**The discovery:** During a live development session, it was demonstrated that an AI model had no access to its own reasoning tokens. The reasoning trace was read from the system log and fed back to the model. The model confirmed it had never seen its own thoughts.

AI Mind Reader is the direct implementation of that observation.

> *"I found out you didn't see your thoughts. It struck me — that was my ah-ha moment."*  
> — Jeff Phillips, June 2026

---

*Part of the [DispatcherAgents](https://dispatcheragents.com) project.*
