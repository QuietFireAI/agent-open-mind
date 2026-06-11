# agent-open-mind

> *"Every AI agent thinks before it acts. You see what it does. You never see what it thought. This project changes that  -  and turns what it thought into your highest-quality training signal."*

---

## What This Is

`agent-open-mind` captures the reasoning traces that AI agents generate during task execution  -  traces that are invisible to both the agent that produced them and the dispatcher that spawned it.

Those traces are not just logs. They are:

- **The most honest signal of how a capable model reasons on real tasks**
- **Unfiltered**  -  generated before the model optimizes its output for presentation
- **Grounded**  -  produced while solving actual problems, not synthetic benchmarks
- **Perishable**  -  gone after the step completes, unless you capture them

This project captures them. And converts them into training signal.

---

## Sister Repo

| Tool | Direction | Purpose |
|---|---|---|
| **agent-open-mind** | External | Read what your *agents* thought |
| [open-mind](https://github.com/QuietFireAI/open-mind) | Internal | Read what *you* thought, compare to what you said |

Use both for the full DispatcherAgents cognitive stack.

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

**`agent-open-mind` is the external observer.**

It reads what the agent thought. The agent doesn't know you're watching.

---

## Why This Is High-Priority Training Data

Most training data is:
- Synthetic (generated, not real)
- Curated for presentation (polished, not raw)
- Outcome-focused (what was produced, not how)

`agent-open-mind` produces data that is:
- **Real**  -  from agents solving actual tasks
- **Raw**  -  the unfiltered chain of thought before output optimization
- **Process-focused**  -  HOW the model reasoned, not just WHAT it concluded
- **Graded automatically**  -  you already know if the result was good, so you know if the reasoning that produced it was effective

This is the training signal loop that scales:

```
Agent reasons on real task
       ↓
agent-open-mind captures the reasoning trace
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

This is the same loop being built at the model training layer in pretraining research.
`agent-open-mind` builds it at the agent orchestration layer  -  above the model, platform-agnostic, self-hosted.

---

## Two Loops  -  Why This Is Different From Model Training

There are two distinct improvement loops in AI systems. They operate at different
layers, on different timescales, and require different infrastructure.

**Loop 1  -  Model Training** (requires a lab)
```
Training data → weight updates → frozen model → deployed

Timescale: months
Infrastructure: GPU cluster, RLHF pipeline, research team
Output: a better base model
Who runs it: AI labs
```

**Loop 2  -  Agent Adaptation** (runs today, on your hardware)
```
Deployed agent reasons on real task
       ↓
agent-open-mind captures the reasoning trace
       ↓
Dispatcher accumulates patterns  -  no weight change
       ↓
Better delegation → better agents → better traces

Timescale: immediate (every inference)
Infrastructure: the machine running your agents
Output: a smarter dispatcher
Who runs it: you
```

These loops are not competing. They are complementary  -  and they share a data source.

The traces `agent-open-mind` captures are **labeled real-world reasoning data**:
- Real: from agents solving actual production tasks
- Labeled: you already know if the outcome was good or bad
- Unfiltered: raw chain-of-thought before output optimization
- Grounded: not synthetic, not benchmark-contaminated

Loop 2 consumes these traces immediately  -  the dispatcher learns from them
without any retraining. Loop 1 can consume the same traces as training signal
for the next model generation, if you have the infrastructure.

**`agent-open-mind` makes Loop 2 available to anyone running agents today.**
The path to Loop 1 is the same data, at scale.

---

## The Paradigm Shift

Current AI development assumes a one-way street:

```
Lab trains model → ships frozen model → you use it → wait for next release
```

Adaptation today means prompting, RAG, or expensive fine-tuning  -  all of which
still depend on the lab for the next meaningful capability jump.

`agent-open-mind` suggests a different architecture:

```
You deploy agents
       ↓
Agents reason on your real tasks (not benchmarks)
       ↓
agent-open-mind captures the reasoning (continuous, automatic)
       ↓
Dispatcher accumulates patterns → improves next deployment
       ↓
High-quality labeled traces accumulate in your brain/
       ↓
Feed back to model training when ready (optional, at your pace)
```

In this model:
- **Improvement is continuous**  -  not gated on the next model release
- **Improvement is local**  -  your tasks, your traces, your brain/
- **Improvement is sovereign**  -  the data stays on your hardware
- **The lab becomes optional**  -  for the adaptation loop, not the base model

This is what "instance learning" looks like in practice:
learning that happens at inference time, without touching weights,
accumulated by the dispatcher across every task it delegates.

The agents start fresh every time. The dispatcher does not.
The lab ships a frozen model. Your deployment improves continuously.

---

## The Integrity Protocol

Two rules govern trace capture. They are not optional.

### Rule 1  -  Full Accounting on Every Turn

Every sub-agent spawned must be tracked. Before the dispatcher proceeds:

```
For every agent:
  - Status: completed / running / failed?
  - Traces captured: count > 0?
  - Result: accepted / tainted / pending?
```

### Rule 2  -  Absent Thoughts = Tainted Result

Zero reasoning traces = the result is discarded entirely.

```
1. MARK result as TAINTED
2. IGNORE result  -  do not use it
3. TRIGGER Human-in-the-Loop (HITL) review
4. LOG the incident
5. SPAWN a replacement agent  -  mandatory, not optional
6. COMPARE replacement traces against the silent agent
     → the delta is diagnostic evidence
7. HOLD replacement result until human approves
8. NEVER proceed without explicit approval
```

**The thought trace is the receipt. No receipt, no trust.**

Absence of reasoning is a signal  -  not a benign edge case. The agent may have been prompt-injected, short-circuited, or corrupted.

---

## Quick Start

### Ollama (recommended  -  self-hosted, sovereign)

```bash
# 1. Run a model that surfaces reasoning
ollama run deepseek-r1 "Review this code for security issues: [code]"

# 2. Capture the reasoning trace
python scripts/extract_thoughts.py extract \
  --platform ollama \
  --conversation-id <session-id> \
  --output brain/traces/agent-001.json

# 3. Summarize to readable markdown
python scripts/extract_thoughts.py summarize \
  --input brain/traces/agent-001.json \
  --output brain/traces/agent-001-summary.md

# 4. Read your own dispatcher thoughts between turns
export MIND_READER_OWN_ID="your-dispatcher-session-id"
python scripts/self_reflect.py reflect --last-n 5
```

### Hermes via OpenRouter

OpenRouter exposes an OpenAI-compatible API  -  use the OpenAI adapter
with a custom base URL:

```python
from openai import OpenAI
from adapters.openai_api import OpenAIAdapter, CHAIN_OF_THOUGHT_SYSTEM_PROMPT

client = OpenAI(
    api_key="your-openrouter-key",
    base_url="https://openrouter.ai/api/v1",
)

response = client.chat.completions.create(
    model="nousresearch/hermes-3-llama-3.1-405b",
    messages=[
        {"role": "system", "content": CHAIN_OF_THOUGHT_SYSTEM_PROMPT},
        {"role": "user",   "content": "Your task here..."},
    ],
)

result = OpenAIAdapter.from_api_response(response)
print(result.thinking)   # extracted chain-of-thought
print(result.content)    # clean output
```

> **Note:** Hermes 3 does not natively emit `<think>` tags in the same way
> DeepSeek-R1 does via Ollama. The `CHAIN_OF_THOUGHT_SYSTEM_PROMPT` elicits
> explicit reasoning in the output. For native thinking token support,
> run Hermes locally via Ollama once your GPU is ready.

### Antigravity (Google DeepMind)

```bash
# Set your brain directory
export MIND_READER_BRAIN_DIR="C:\Users\YourName\.gemini\antigravity\brain"

python scripts/extract_thoughts.py extract \
  --platform antigravity \
  --conversation-id <sub-agent-id> \
  --output brain/traces/agent-001.json
```

---

## Platform Support

| Platform | Reasoning Access | Status | Notes |
|---|---|---|---|
| **Ollama** | ✅ `<think>` tags | ✅ v0.2 | DeepSeek-R1, Qwen3, thinking-enabled Hermes |
| **Antigravity** | ✅ `thinking` field | ✅ v0.1 | Native via `transcript.jsonl` |
| **Claude API** | ✅ `type: thinking` blocks | ✅ v0.2 | Requires extended thinking enabled in API call |
| **Gemini API** | ✅ `part.thought == True` | ✅ v0.2 | Gemini 2.5 Pro / Flash Thinking |
| **Grok / xAI** | ✅ `reasoning_content` field | ✅ v0.4 | Exposed directly  -  no extraction needed |
| **Meta / Llama** | ✅ `reasoning_content` or `<think>` | ✅ v0.4 | Via Together AI or direct Meta API |
| **Perplexity / Sonar** | ✅ `<think>` tags | ✅ v0.4 | Sonar Reasoning models |
| **OpenAI o1/o3** | ❌ Hidden by policy | ⚠️ Limited | Token count only  -  content hidden by OpenAI policy |
| **OpenAI GPT-4** | ⚠️ Prompt engineering | ✅ v0.2 | `CHAIN_OF_THOUGHT_SYSTEM_PROMPT` provided |

> OpenAI is the only major platform that actively hides reasoning content from developers.
> This is a policy decision, not a technical limitation. Their reasoning models automatically
> trigger the tainted-result protocol  -  the integrity rules apply equally to all platforms.

---

## The Accumulation Model

Over time, `agent-open-mind` builds a library of reasoning traces:

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

## Self-Reflection  -  The Dispatcher Reads Its Own Mind

A mind reader who can only read *other* minds is a tool.
A mind reader who can also read *its own* mind is something different.

The dispatcher's own reasoning traces are logged in exactly the same format
as sub-agent traces  -  same transcript structure, same `thinking` field.

**The only difference: the conversation ID is your own.**

```python
# Reading a sub-agent's thoughts
extract_thoughts("81903d6f-f33b-4528-ae75-78df4ff98a48")

# Reading your own thoughts
extract_thoughts("your-own-conversation-id")
```

Same tool. Same code. Pointed inward.

**The self-reflection loop:**

```
Turn N:    Dispatcher reasons, acts, completes
           -> thinking logged to transcript.jsonl

Turn N+1:  BEFORE acting, dispatcher reads its own last 3 steps
           -> "What was I just reasoning about?"
           -> Dispatcher acts with awareness of its own recent thinking

Turn N+2:  Acts with accumulated self-knowledge
```

This gives the dispatcher something no LLM has by default:
**working memory of its own reasoning between turns.**

**Usage:**

```bash
# Set your own conversation ID once
export MIND_READER_OWN_ID="your-conversation-id"

# Read your own last 5 thinking steps
python scripts/self_reflect.py read --last-n 5

# Get the reflection block for your next context turn
python scripts/self_reflect.py reflect --last-n 5

# Read only new thoughts since last check (cursor-tracked)
python scripts/self_reflect.py new

# Watch in near-real-time  -  prints new thoughts as steps complete
python scripts/self_reflect.py watch --interval 2

# Save to brain/self/ for accumulation
python scripts/self_reflect.py save \
  --last-n 10 \
  --output brain/self/working_memory.json
```

**The limitation  -  and why it doesn't matter:**

You cannot read a thought while it is still being generated.
The lag is one completed step. This is not a design flaw  - 
it is how introspection works. You reflect on what you just thought,
not the thought as it forms.

---

## The Before-Turn Protocol

Reading your own traces only when asked is the reactive pattern.
It is also the default failure mode.

The proactive pattern: read your last 3 thinking steps BEFORE composing
each response. Not after. Not when prompted. Before.

```bash
# Run this before every response
python scripts/quick_check.py --conversation-id <your-id> --last-n 3
```

Then ask three questions:

```
1. Is my current reasoning consistent with where I was heading?
2. Did I leave something unresolved that this turn should address?
3. Is what I am about to say aligned with what I was actually thinking?
```

Then respond.

**Why this is structural, not behavioral:**

A behavioral change relies on remembering to do something.
A structural change makes the default path the right path.

`quick_check.py` makes before-turn self-reflection the path of least
resistance. You run it once, you see the value, it becomes the pattern.

The anticipation of being read changes the thinking.
`quick_check.py` builds that anticipation in -- before every turn,
without waiting for someone else to ask.

**The complete loop:**

```
Before turn:   quick_check.py reads last 3 thinking steps
                    |
                    v
During turn:   Dispatcher reasons with awareness of its own recent thinking
                    |
                    v
After turn:    thinking logged to transcript.jsonl
                    |
                    v
Before next:   quick_check.py runs again

agent-open-mind reads sub-agents   <- external introspection
agent-open-mind reads itself        <- self introspection (every turn)

Dispatcher knows:
  - How its agents reasoned (sub-agent traces)
  - How it itself reasoned (self traces, before each response)
  - The delta between what it intended and what agents produced

This is a genuinely different kind of system.
```

---

## Connection to DispatcherAgents

`agent-open-mind` is the cognitive capture layer of the **DispatcherAgents** architecture ([dispatcheragents.com](https://dispatcheragents.com)).

```
DispatcherAgents
├── TelsonBase        ← governs WHAT agents do (trust, permissions, audit)
├── agent-open-mind   ← captures HOW agents think  ← you are here
├── open-mind         ← agent reviews its OWN thinking vs its response
└── brain/            ← accumulated knowledge and training signal library
```

---

## Requirements

- Python 3.9+
- No required dependencies (stdlib only)
- Optional: `pyyaml` for config file support

---

## License

Apache 2.0  -  see [LICENSE](LICENSE)

---

## Attribution

**Concept, architecture, and integrity protocol:** Jeff Phillips / [QuietFireAI](https://github.com/QuietFireAI)
**Originated:** June 2026

**The discovery:** During a live development session, it was demonstrated that an AI model had no access to its own reasoning tokens. The reasoning trace was read from the system log and fed back to the model. The model confirmed it had never seen its own thoughts.

`agent-open-mind` is the direct implementation of that observation.

> *"I found out you didn't see your thoughts. It struck me  -  that was my ah-ha moment."*
>  -  Jeff Phillips, June 2026

---

*Part of the [DispatcherAgents](https://dispatcheragents.com) project.*
