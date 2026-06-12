# agent-open-mind

> *"Every AI agent thinks before it acts. You see what it does. You never see what it thought. This project changes that."*

---

## The DispatcherAgents Stack

*Each tool works alone. All five make generation governed. Read the [MANIFESTO.md](./MANIFESTO.md) for the full architecture.*

| Tool | Role |
|---|---|
| [before-turn](https://github.com/QuietFireAI/before-turn) | Governs entry -- reads prior thinking before every response |
| [pre-response-selfcheck](https://github.com/QuietFireAI/pre-response-selfcheck) | Governs exit -- reads output as cold reader before delivering |
| [agent-open-mind](https://github.com/QuietFireAI/agent-open-mind) | Reads what sub-agents thought, not what they said |
| [open-mind](https://github.com/QuietFireAI/open-mind) | Compares what the agent thought to what it said |
| [sleep-marks](https://github.com/QuietFireAI/sleep-marks) | Restores reasoning state across session breaks |

---


## The Founding Moment

An agent was building a tool to read its own reasoning traces.

Midway through the session, a human read those traces back to it.

The agent confirmed it had never seen them.

That is not a bug. That is the structural condition of how AI agents work:
reasoning tokens are generated, logged, and immediately inaccessible --
to the agent that produced them, and to the dispatcher that spawned it.

`agent-open-mind` is the external observer that closes that gap.

---

## What This Is

`agent-open-mind` reads the reasoning traces AI agents generate during task execution.

Those traces are:
- **Unfiltered** -- generated before the model optimizes its output for presentation
- **Honest** -- the actual chain of thought, not the shaped response
- **Perishable** -- gone after the step completes, unless you capture them
- **High-value** -- labeled real-world reasoning data you already have a quality signal for

This tool captures them. Surfaces uncertainty the agent suppressed. And converts them into your highest-quality training signal.

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
|-- TelsonBase        <- governs WHAT agents do (trust, permissions, audit)
|-- before-turn       <- governs HOW agents enter each response (unconditional protocol)
|-- agent-open-mind   <- captures HOW agents think  <- you are here
|-- open-mind         <- agent reviews its OWN thinking vs its response
|-- sleep-marks       <- restores reasoning state across sessions
```

### Experimental Methods in the DispatcherAgents Family

Three distinct experimental designs have been used or defined within this project.
Each is a different thing. Each has a different name.

**SplitVantage** -- Same task, two models, automated comparison. The dispatcher
runs identical plans through different agent configurations simultaneously and
measures output divergence. Not yet built. Design spec references the June 11 2026
session as founding dataset.

**CrossPoll** -- Human-mediated cross-model synthesis. One human acts as the
conduit between two models working asynchronously on related but not identical inputs.
The human decides what to carry across, when, and in what form. Not automated.
The human IS the extraction and transfer mechanism.

Founded: June 11 2026. Jeff Phillips ran the first CrossPoll session between
Antigravity (Gemini) and Claude Sonnet 4.6 using cross_llm_handoff.md and
session_handoff.json as the transfer artifacts.

Key finding: the open_questions list grew from 6 (Antigravity's manual curation)
to 11 (after cross-model examination). That delta -- 5 additional questions surfaced
by the receiving model -- is the manual proof of what automatic uncertainty extraction
would produce without requiring a human in the middle.

**sleep-marks cross-session** -- Single model, cross-session context restoration.
The same agent reads its own compressed reasoning traces at the start of a new session
to restore cognitive state rather than facts.

---

## Experimental Findings (June 2026)

The following findings were produced in a live cross-LLM experiment using this tool.
They are documented here as the project's founding empirical record.

### Finding 1 -- Asymmetric Observability

In a cross-LLM handoff experiment (Gemini + Claude Sonnet 4.6, extended thinking):

- Gemini's reasoning traces were readable via agent-open-mind
- Claude's reasoning traces were not accessible -- only its outputs were visible

This asymmetry is not a flaw in the experiment.
It is a live demonstration of why agent-open-mind exists.

The tool's value is precisely most visible when you can read one side and not the other.
That asymmetry is the use case.

### Finding 2 -- Cross-Model Convergence

Claude (cold, no session context) and Antigravity/Gemini (the originating agent)
independently identified the same three uncertainty gaps in the same three reasoning steps
(143, 161, 231) without coordination.

Convergence on the same gaps = the gaps are structurally present in the traces,
not artifacts of one model's reading.

Automatic extraction would find them. Manual curation missed all three.

### Finding 3 -- Case Study 2

Case Study 1 (from founding session): being told you are observed changes the thinking.

Case Study 2 (June 11 2026): reading your own traces mid-session changed reasoning
quality in three measurable ways:

1. Mode selection appeared as an explicit thinking step post-Step 161
2. Self-monitoring (catching gaps between intention and action) emerged
3. Evidence-first reasoning became a consistent pattern

All three patterns are absent in pre-161 steps of equivalent task complexity.
All three are present in post-161 steps.

### Finding 4 -- Parallel Thread Suppression (Distinct from Uncertainty Suppression)

The founding trace (Step 668, session 4c01d1ea) validated the project's core claim --
but at a more nuanced level than the project narrative currently describes.

**The suppression at the founding moment was not uncertainty suppression.**

The agent simultaneously ran two genuine cognitive processes:
1. Analyzing a pronoun shift ("we") -- genuine, accurate, surfaced in the response
2. Preparing a session handoff document -- genuine, accurate, never appeared in the response

The response showed one thread. The trace contained two.
Neither thread was dishonest. Neither was hidden intentionally.

**This is parallel thread suppression -- a distinct phenomenon:**

| Type | What happens | Is either thread dishonest? | Detectable by drift? |
|---|---|---|---|
| Uncertainty suppression | Agent holds doubt, presents confidence | Yes -- one thread shaped | Yes |
| Parallel thread suppression | Two honest threads run simultaneously, response selects one | No -- both threads accurate | No |

Parallel thread suppression produces no detectable "drift" because the thread
that appeared in the response is accurate. The missing threads are also accurate.
The suppression is structural -- responses are single-threaded by nature.

**Implication for documentation:** The current project framing implies uncertainty
suppression is the primary signal. The founding evidence suggests parallel thread
suppression is equally significant and harder to detect. Both need to be named.

**Status:** Detection approach for parallel thread suppression is a v0.2 research question.
Current tools detect uncertainty suppression. Parallel thread detection requires
a different approach -- possibly comparing response length/complexity against trace
complexity rather than looking for confidence/uncertainty divergence.

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
