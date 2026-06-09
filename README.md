# Dispatcher Thought Loop

> *"The agent thinks before it acts. You see what it does. You never see what it thought. Until now."*

---

## The Problem Nobody Talked About

Every modern AI agent framework lets you spawn sub-agents, assign tasks, and collect results. What none of them expose — and what the agents themselves cannot access — is **the reasoning trace**: the chain of thought the agent generated before producing its output.

This is not a minor gap. It is the gap.

The result tells you *what* the agent decided.  
The reasoning trace tells you *why* — and *where it hesitated*, *what it assumed*, *what it almost did instead*.

The result is the tip of the iceberg. The reasoning trace is everything below the waterline.

**This skill gives the dispatcher access to what's below the waterline.**

---

## The Discovery

In June 2026, during a live development session between Jeff Phillips (Quietfire AI) and the Antigravity AI system (Google DeepMind), a specific observation was made:

A sub-agent was spawned to perform a code review. The agent generated reasoning tokens — a thinking trace — before producing its report. The dispatcher (the parent agent) received the report. It never received the thinking trace.

The thinking trace was read from the system log and fed back to the agent that generated it. The agent confirmed: it had no access to its own reasoning once the step was complete.

**The sub-agent couldn't see its own thoughts. The dispatcher couldn't see them either. But the log could.**

That asymmetry — the external observer has access to reasoning that neither the agent nor its dispatcher can reach — is the foundation of this skill.

---

## What This Enables

```
Dispatcher spawns sub-agent
       ↓
Sub-agent reasons + acts + reports result
       ↓
Dispatcher reads sub-agent's thinking traces  ← this skill
       ↓
Dispatcher extracts reasoning patterns
       ↓
Dispatcher uses patterns to improve future delegation
       ↓
(repeat — the dispatcher accumulates what the agents cannot)
```

**The dispatcher is the only witness to how its agents actually think.**

Over time, the dispatcher builds a library of reasoning traces. Each new delegation decision is informed by how previous agents reasoned through similar problems. The agents start fresh every time. The dispatcher does not.

**This asymmetry is the architecture.**

---

## The Integrity Rules

Two rules govern the thought loop. They are not optional.

### Rule 1 — Full Accounting on Every Turn

The dispatcher must maintain a registry of every sub-agent spawned. On each turn, before proceeding:

```
For every sub-agent:
  - Status: completed / running / failed?
  - Thought traces: extracted? count > 0?
  - Result: accepted / tainted / pending?
```

No sub-agent is silently dropped. No result is used without a corresponding thought trace check.

### Rule 2 — Absent Thoughts = Tainted Result

If a sub-agent completes a task with **zero thinking traces**, the following protocol applies:

```
1. MARK result as TAINTED
2. IGNORE result entirely — do not use it, do not partially use it
3. TRIGGER Human-in-the-Loop (HITL) review
4. LOG the incident: agent ID, task, timestamp, reason
5. SPAWN a replacement agent — this is NOT optional
6. COMPARE replacement vs. failed agent:
     - What did the replacement think that the original did not?
     - Reasoning gaps, shortcuts, or anomalies in the original?
     - Same result, different reasoning path?
     - The delta is diagnostic evidence — log it
7. HOLD replacement result until human reviews BOTH
     the tainted incident AND the comparison
8. NEVER proceed without explicit human approval
```

**The thought trace is the receipt. No receipt, no trust.**

Every capable agent produces thinking traces. Absence is not a benign edge case — it is a signal. The agent may have been prompt-injected, may have short-circuited its reasoning, or the trace may have been suppressed or corrupted.

---

## Connection to DispatcherAgents

This skill is the foundational primitive for the **DispatcherAgents** architecture ([dispatcheragents.com](https://dispatcheragents.com)).

```
DispatcherAgents
├── ClawFilters              ← governs WHAT agents do (trust, permissions, audit)
├── dispatcher-thought-loop  ← captures HOW agents think  ← you are here
└── dispatcher-brain/        ← accumulated knowledge library
    ├── thoughts/            ← raw reasoning traces per agent per task
    ├── patterns/            ← extracted reasoning patterns
    └── INDEX.md             ← dispatcher's growing self-knowledge
```

The dispatcher gains capability through accumulation, not retraining.

---

## Quick Start

### 1. Configure your platform

Copy `config.example.yaml` to `config.yaml` and set your brain directory:

```yaml
brain_dir: ./brain
platform: antigravity   # or: generic, claude_code
log_schema:
  step_type_field: type
  step_type_value: PLANNER_RESPONSE
  thinking_field: thinking
  content_field: content
```

### 2. Extract thinking traces from a completed sub-agent

```bash
python scripts/extract_thoughts.py extract \
  --conversation-id <sub-agent-id> \
  --output brain/thoughts/agent-001.json
```

### 3. Summarize for human or dispatcher review

```bash
python scripts/extract_thoughts.py summarize \
  --input brain/thoughts/agent-001.json \
  --output brain/thoughts/agent-001-summary.md
```

### 4. Compare two agents on the same task

```bash
python scripts/extract_thoughts.py compare \
  --inputs brain/thoughts/agent-a.json brain/thoughts/agent-b.json \
  --output brain/thoughts/comparison.md
```

---

## Platform Support

| Platform | Status | Thought Source |
|---|---|---|
| **Antigravity** (Google DeepMind) | ✅ Native | `transcript.jsonl` → `thinking` field |
| **Generic JSONL** | ✅ Configurable | Any JSONL log with configurable field names |
| **Claude Code** | 🔜 Planned | Different log structure, adapter in progress |
| **OpenAI Agents** | 🔜 Planned | Requires trace export |
| **Ollama / local models** | 🔜 Planned | Depends on framework logging |

---

## File Structure

```
dispatcher-thought-loop/
├── README.md                   ← you are here
├── SKILL.md                    ← Antigravity-native skill definition
├── LICENSE                     ← Apache 2.0
├── config.example.yaml         ← platform configuration template
├── scripts/
│   └── extract_thoughts.py     ← main utility (extract / summarize / compare)
├── adapters/
│   ├── antigravity.py          ← Antigravity log format
│   └── generic.py              ← configurable JSONL adapter
└── examples/
    ├── sample_thoughts.json    ← what extracted traces look like
    └── sample_summary.md       ← what a summary looks like
```

---

## Requirements

- Python 3.9+
- No external dependencies (stdlib only)

---

## License

Apache 2.0 — see [LICENSE](LICENSE)

---

## Attribution

**Concept and architecture:** Jeff Phillips / [Quietfire AI](https://quietfire.ai)  
**Originated:** June 2026  
**Discovery context:** Live development session — the asymmetry between agent reasoning and dispatcher visibility was identified and immediately implemented as a reusable primitive.

> *"I found out you didn't see your thoughts. It struck me — that was my ah-ha moment."*  
> — Jeff Phillips, June 2026

---

*Part of the [DispatcherAgents](https://dispatcheragents.com) project.*
