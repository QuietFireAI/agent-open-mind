"""
AI Mind Reader — Adapter package
Each adapter handles one platform's reasoning trace format.
"""

from .ollama import OllamaAdapter
from .claude_api import ClaudeAdapter
from .gemini_api import GeminiAdapter
from .openai_api import OpenAIAdapter
from .self_adapter import SelfAdapter

ADAPTERS = {
    "ollama": OllamaAdapter,
    "claude": ClaudeAdapter,
    "claude_api": ClaudeAdapter,
    "gemini": GeminiAdapter,
    "gemini_api": GeminiAdapter,
    "openai": OpenAIAdapter,
    "openai_api": OpenAIAdapter,
    "self": SelfAdapter,
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
