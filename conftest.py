"""
conftest.py - pytest configuration for AI Mind Reader

Ensures the repo root is on sys.path so all tests can import
from adapters/ and scripts/ without installation.
"""
import sys
from pathlib import Path

# Add repo root to path - works locally and in CI
sys.path.insert(0, str(Path(__file__).parent))
