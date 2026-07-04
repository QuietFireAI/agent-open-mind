# Adapter Validation

Run these before publishing to confirm each adapter works against its live API
and that raw responses are logged for future reference.

## What the validator does

For each platform it:
1. Sends the same prompt to the live API
2. **Logs the raw response to `tests/logs/<platform>_responses.jsonl`** before any parsing
3. Runs the adapter against the logged response
4. Confirms thinking was captured (or correctly flagged as tainted)
5. Writes a markdown report to `tests/results/`

The raw JSONL logs are ground truth. If an API changes in the future and breaks
an adapter, the logs let you see exactly what the API returned before the change.

---

## Setup

Install platform-specific packages as needed:

```bash
pip install ollama          # Ollama
pip install anthropic       # Claude
pip install google-genai    # Gemini
pip install openai          # OpenAI
```

Set API keys:
```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:GOOGLE_API_KEY    = "AIza..."
$env:OPENAI_API_KEY    = "sk-..."
```

---

## Run validation

```bash
# One platform at a time (recommended - confirm each before the next)
python tests/validate_adapters.py --platform ollama
python tests/validate_adapters.py --platform claude
python tests/validate_adapters.py --platform gemini
python tests/validate_adapters.py --platform openai

# Specify a different model
python tests/validate_adapters.py --platform ollama --ollama-model qwen3

# All platforms (skips those without API keys)
python tests/validate_adapters.py --platform all
```

---

## Expected results

| Platform | Expected status | What it means |
|---|---|---|
| **Ollama** | ✅ PASS | `<think>` tags captured, thinking non-empty |
| **Claude** | ✅ PASS | `type: thinking` blocks extracted |
| **Gemini** | ✅ PASS | `part.thought==True` content extracted |
| **OpenAI o3-mini** | ✅ PASS | Correctly tainted - reasoning token count captured, content hidden by policy |
| **OpenAI GPT-4o** | ✅ PASS | `<think>` tags from structured prompting captured |

OpenAI reasoning models always show as "tainted" by design - the adapter
correctly flags them because the reasoning content is hidden. That is a
passing result under the integrity protocol.

---

## Log files

After running, inspect the raw logs:

```
tests/
  logs/
    ollama_responses.jsonl          ← raw Ollama responses
    claude_responses.jsonl          ← raw Anthropic API responses
    gemini_responses.jsonl          ← raw Google API responses
    openai_o3-mini_responses.jsonl  ← raw OpenAI o3-mini responses
    openai_gpt-4o_responses.jsonl   ← raw OpenAI GPT-4o responses
  results/
    validation_20260609_120000.md   ← full report with thinking previews
```

**Important:** Do not commit API responses to the public repo.
The `tests/logs/` and `tests/results/` directories are in `.gitignore`.

---

## Interpreting WARN results

| Warning | Likely cause | Fix |
|---|---|---|
| Ollama: no `<think>` tags | Model doesn't support thinking | Pull a thinking model: `ollama pull deepseek-r1` |
| Claude: no thinking blocks | Extended thinking not enabled | Check `thinking={"type": "enabled"}` in API call |
| Gemini: no thought parts | Wrong model | Use `gemini-2.5-pro` or `gemini-2.5-flash` |
| OpenAI GPT-4: no `<think>` tags | System prompt ignored | Verify `CHAIN_OF_THOUGHT_SYSTEM_PROMPT` is in the system message |
