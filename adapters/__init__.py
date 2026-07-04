"""
AI Mind Reader - Adapter package
Each adapter handles one platform's reasoning trace format.

Supported platforms:
  ollama - Local models via Ollama (<think> tags)
  claude - Anthropic Claude (thinking content blocks)
  gemini - Google Gemini (part.thought field)
  openai - OpenAI o1/o3 (tainted - reasoning hidden by policy)
  grok - xAI Grok (reasoning_content field, exposed)
  meta - Meta Llama (reasoning_content or <think> tags)
  perplexity - Perplexity Sonar Reasoning (<think> tags)
  self - Dispatcher self-reflection (transcript.jsonl)
"""

from .ollama import OllamaAdapter
from .claude_api import ClaudeAdapter
from .gemini_api import GeminiAdapter
from .openai_api import OpenAIAdapter
from .grok import GrokAdapter
from .meta import MetaAdapter
from .perplexity import PerplexityAdapter
from .self_adapter import SelfAdapter

ADAPTERS = {
    # Local
    "ollama":        OllamaAdapter,
    # Anthropic
    "claude":        ClaudeAdapter,
    "claude_api":    ClaudeAdapter,
    # Google
    "gemini":        GeminiAdapter,
    "gemini_api":    GeminiAdapter,
    # OpenAI
    "openai":        OpenAIAdapter,
    "openai_api":    OpenAIAdapter,
    # xAI
    "grok":          GrokAdapter,
    "xai":           GrokAdapter,
    # Meta
    "meta":          MetaAdapter,
    "llama":         MetaAdapter,
    "together":      MetaAdapter,
    # Perplexity
    "perplexity":    PerplexityAdapter,
    "sonar":         PerplexityAdapter,
    # Self
    "self":          SelfAdapter,
    "antigravity":   SelfAdapter,
}


def get_adapter(platform: str):
    """Return the adapter class for a given platform name."""
    key = platform.lower().strip()
    if key not in ADAPTERS:
        raise ValueError(
            f"Unknown platform '{platform}'. "
            f"Available: {', '.join(ADAPTERS.keys())}"
        )
    return ADAPTERS[key]


__all__ = [
    "OllamaAdapter",
    "ClaudeAdapter",
    "GeminiAdapter",
    "OpenAIAdapter",
    "SelfAdapter",
    "get_adapter",
]
