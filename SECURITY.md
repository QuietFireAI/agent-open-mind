# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| v0.3.x (current) | ✅ |
| v0.2.x | ✅ security fixes only |
| v0.1.x | ❌ |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report security issues privately to: **jeff@quietfire.ai**

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

You will receive a response within 72 hours. If the vulnerability is confirmed,
a fix will be prioritized and a patched release published. You will be credited
in the release notes unless you prefer to remain anonymous.

## Scope

Security issues relevant to this project include:

- **Prompt injection via reasoning traces** - malicious content in a captured
  thinking trace that could cause the dispatcher to act against user intent
- **Path traversal in log file reading** - adapter `read_log()` paths that
  could access files outside the intended directory
- **Credential exposure** - API keys or secrets appearing in logged responses
  that are then written to non-gitignored files
- **Integrity protocol bypass** - conditions where a tainted result could be
  silently promoted past the HITL gate

## Out of Scope

- Vulnerabilities in the underlying AI platforms (report those to the platform)
- API key management (your responsibility - the `.gitignore` protects logs)
- Model behavior (we capture reasoning, we don't control it)
