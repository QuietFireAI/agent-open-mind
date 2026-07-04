---
name: agent-open-mind
description: >
  Run when an orchestrator/dispatcher receives results from sub-agents. Read what
  the sub-agents actually THOUGHT - their reasoning traces - not just the cleaned
  results they returned, before acting on them. Treat a missing trace as tainted,
  never as a silent pass. This is the DISPATCH layer of the DispatcherAgents stack.
---

# agent-open-mind

## What it is
In standard agent loops a sub-agent's reasoning is generated, logged, and never
fed back to the dispatcher that spawned it - the dispatcher decides on shaped
outputs alone. agent-open-mind is the external observer that reads those traces
and returns them, closing the visibility asymmetry.

## When to trigger
Whenever a coordinating agent is about to act on a sub-agent's output: before
merging, accepting, or escalating sub-agent results.

## The protocol
1. Pull each sub-agent's reasoning trace, not just its final answer.
2. **Absent Thoughts = Tainted Result.** If a sub-agent returns output with no
   trace, treat it as low-trust and flag it for review - never silent-admit.
3. Feed the recovered reasoning back to the dispatcher so its decision accounts
   for the uncertainty and alternatives the sub-agent suppressed.

## Invoke the engine
```bash
pip install -r requirements.txt    # clone-and-run; zero required deps for tests
```
```bash
python scripts/extract_thoughts.py extract --last-n 5    # pull sub-agent traces
python scripts/extract_thoughts.py summarize --last-n 5
python scripts/self_reflect.py    reflect --last-n 5
```
```python
from adapters.openai_api import OpenAIAdapter, CHAIN_OF_THOUGHT_SYSTEM_PROMPT
result = OpenAIAdapter.from_api_response(response)   # normalizes trace + answer
```

## Works with
- **open-mind** scores drift on a single agent's trace-vs-response; agent-open-mind
  extends that visibility from one agent to its sub-agents.
- **sleep-marks** carries recovered reasoning across sessions; **before-turn** uses
  it at the start of the next turn.

## Honest scope
Depends on a provider that exposes reasoning traces. When only summaries are
available it degrades to summarized traces at reduced resolution and says so - 
it never treats a summary as a raw trace. The hard guarantee is that the observer
is *external* to the sub-agent, not the sub-agent reporting on itself.

## Output convention
End a triggering turn with one line, e.g.:
`agent-open-mind: read 4 sub-agent traces; 1 flagged (absent trace → tainted).`
