## What this PR does

<!-- One-line summary -->

## Type of change

- [ ] New platform adapter
- [ ] Bug fix in existing adapter
- [ ] Documentation improvement
- [ ] Other (describe below)

## Platform / model tested against

<!-- If this is an adapter PR: platform name, model name, SDK version -->

## Checklist

- [ ] Unit tests added in `tests/unit/` (no API keys required to run)
- [ ] Live validation run: `python tests/validate_adapters.py --platform <name>`
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] Adapter registered in `adapters/__init__.py`
- [ ] No required dependencies added (optional only, imported lazily)
- [ ] Platform limitations documented honestly (if reasoning is hidden, say so)

## Integrity protocol

- [ ] Absent reasoning traces surface as tainted, not silently ignored
- [ ] `has_thinking()` returns False when no reasoning is present
- [ ] No code path bypasses the taint flag

## Sample output

<!-- Paste a redacted example showing thinking and content extracted correctly -->

```
Thinking: Let me consider the authentication flow first...
Content:  I found two issues in the authentication module...
```

## Additional notes

<!-- Anything the reviewer should know -->
