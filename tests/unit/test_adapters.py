"""
Unit tests for AI Mind Reader adapters.
No API keys required — tests parse known inputs only.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


# ─── Ollama ───────────────────────────────────────────────────────────────────

class TestOllamaAdapter:
    def setup_method(self):
        from adapters.ollama import OllamaAdapter
        self.adapter = OllamaAdapter

    def test_parse_response_with_thinking(self):
        raw = "<think>\nLet me reason about this carefully.\nThe function has a bug.\n</think>\n\nHere is my answer."
        thinking, content = self.adapter.parse_response(raw)
        assert "Let me reason" in thinking
        assert "The function has a bug" in thinking
        assert "Here is my answer" in content
        assert "<think>" not in content
        assert "</think>" not in content

    def test_parse_response_no_thinking(self):
        raw = "Here is my answer with no reasoning tags."
        thinking, content = self.adapter.parse_response(raw)
        assert thinking == ""
        assert content == raw

    def test_parse_response_multiple_think_blocks(self):
        raw = "<think>First thought.</think>Middle text.<think>Second thought.</think>Final answer."
        thinking, content = self.adapter.parse_response(raw)
        assert "First thought" in thinking
        assert "Second thought" in thinking
        assert "Middle text" in content
        assert "Final answer" in content

    def test_has_thinking_true(self):
        raw = "<think>Some reasoning.</think>Output."
        assert self.adapter.has_thinking(raw) is True

    def test_has_thinking_false(self):
        raw = "Output with no thinking."
        assert self.adapter.has_thinking(raw) is False

    def test_case_insensitive_tags(self):
        raw = "<THINK>Some reasoning.</THINK>Output."
        thinking, content = self.adapter.parse_response(raw)
        assert "Some reasoning" in thinking

    def test_multiline_thinking(self):
        raw = "<think>\nLine 1\nLine 2\nLine 3\n</think>\nAnswer here."
        thinking, content = self.adapter.parse_response(raw)
        assert "Line 1" in thinking
        assert "Line 2" in thinking
        assert "Answer here" in content


# ─── Claude ───────────────────────────────────────────────────────────────────

class TestClaudeAdapter:
    def setup_method(self):
        from adapters.claude_api import ClaudeAdapter
        self.adapter = ClaudeAdapter

    def test_parse_dict_blocks(self):
        blocks = [
            {"type": "thinking", "thinking": "Let me think through this..."},
            {"type": "text", "text": "Here is my analysis."},
        ]
        thinking, content = self.adapter.parse_content_blocks(blocks)
        assert "Let me think through this" in thinking
        assert "Here is my analysis" in content

    def test_parse_no_thinking_blocks(self):
        blocks = [{"type": "text", "text": "Direct answer."}]
        thinking, content = self.adapter.parse_content_blocks(blocks)
        assert thinking == ""
        assert "Direct answer" in content

    def test_parse_multiple_thinking_blocks(self):
        blocks = [
            {"type": "thinking", "thinking": "First reasoning step."},
            {"type": "text", "text": "Intermediate output."},
            {"type": "thinking", "thinking": "Second reasoning step."},
            {"type": "text", "text": "Final answer."},
        ]
        thinking, content = self.adapter.parse_content_blocks(blocks)
        assert "First reasoning step" in thinking
        assert "Second reasoning step" in thinking
        assert "Intermediate output" in content
        assert "Final answer" in content

    def test_empty_blocks(self):
        thinking, content = self.adapter.parse_content_blocks([])
        assert thinking == ""
        assert content == ""

    def test_parse_dict_response(self):
        response = {
            "content": [
                {"type": "thinking", "thinking": "My reasoning..."},
                {"type": "text", "text": "My answer..."},
            ]
        }
        thinking, content = self.adapter.from_api_response(response)
        assert "My reasoning" in thinking
        assert "My answer" in content


# ─── Gemini ───────────────────────────────────────────────────────────────────

class TestGeminiAdapter:
    def setup_method(self):
        from adapters.gemini_api import GeminiAdapter
        self.adapter = GeminiAdapter

    def test_parse_parts_with_thought(self):
        parts = [
            {"thought": True, "text": "Let me think..."},
            {"thought": False, "text": "Here is my answer."},
        ]
        thinking, content = self.adapter.parse_parts(parts)
        assert "Let me think" in thinking
        assert "Here is my answer" in content

    def test_parse_parts_no_thought(self):
        parts = [{"thought": False, "text": "Direct answer."}]
        thinking, content = self.adapter.parse_parts(parts)
        assert thinking == ""
        assert "Direct answer" in content

    def test_parse_is_thought_field(self):
        # Some SDK versions use is_thought instead of thought
        parts = [
            {"is_thought": True, "text": "Reasoning here."},
            {"is_thought": False, "text": "Answer here."},
        ]
        thinking, content = self.adapter.parse_parts(parts)
        assert "Reasoning here" in thinking
        assert "Answer here" in content

    def test_parse_empty_parts(self):
        thinking, content = self.adapter.parse_parts([])
        assert thinking == ""
        assert content == ""

    def test_parse_dict_response(self):
        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"thought": True, "text": "My reasoning..."},
                            {"thought": False, "text": "My answer..."},
                        ]
                    }
                }
            ]
        }
        thinking, content = self.adapter.from_api_response(response)
        assert "My reasoning" in thinking
        assert "My answer" in content


# ─── OpenAI ───────────────────────────────────────────────────────────────────

class TestOpenAIAdapter:
    def setup_method(self):
        from adapters.openai_api import OpenAIAdapter, CHAIN_OF_THOUGHT_SYSTEM_PROMPT
        self.adapter = OpenAIAdapter
        self.cot_prompt = CHAIN_OF_THOUGHT_SYSTEM_PROMPT

    def test_chain_of_thought_prompt_exists(self):
        assert self.cot_prompt
        assert "<think>" in self.cot_prompt

    def test_parse_gpt4_response_with_think_tags(self):
        response = {
            "model": "gpt-4o",
            "choices": [
                {"message": {"content": "<think>My reasoning.</think>My answer."}}
            ],
            "usage": {},
        }
        result = self.adapter.from_api_response(response)
        assert "My reasoning" in result.thinking
        assert "My answer" in result.content
        assert result.tainted is False

    def test_parse_gpt4_response_no_think_tags(self):
        response = {
            "model": "gpt-4o",
            "choices": [
                {"message": {"content": "Direct answer without reasoning."}}
            ],
            "usage": {},
        }
        result = self.adapter.from_api_response(response)
        assert result.thinking == ""
        assert result.tainted is True

    def test_reasoning_model_flagged_tainted(self):
        response = {
            "model": "o3-mini",
            "choices": [
                {"message": {"content": "Answer from reasoning model."}}
            ],
            "usage": {
                "completion_tokens_details": {"reasoning_tokens": 500}
            },
        }
        result = self.adapter.from_api_response(response)
        assert result.tainted is True
        assert result.reasoning_tokens == 500
        assert result.thinking == ""  # hidden by OpenAI policy


# ─── SelfAdapter ──────────────────────────────────────────────────────────────

class TestSelfAdapter:
    def setup_method(self):
        from adapters.self_adapter import SelfAdapter
        self.SelfAdapter = SelfAdapter

    def test_format_for_injection_empty(self):
        # When no steps, returns empty string
        import os
        os.environ["MIND_READER_OWN_ID"] = "test-conv-id"
        adapter = self.SelfAdapter(
            conversation_id="test-conv-id",
            brain_dir="./brain_test",
        )
        result = adapter.format_for_injection([])
        assert result == ""

    def test_format_for_injection_with_steps(self):
        import os
        os.environ["MIND_READER_OWN_ID"] = "test-conv-id"
        adapter = self.SelfAdapter(
            conversation_id="test-conv-id",
            brain_dir="./brain_test",
        )
        steps = [
            {
                "step_index": 5,
                "created_at": "2026-06-09T10:00:00Z",
                "thinking": "I need to review the auth module carefully.",
                "content": "Let me look at the code.",
                "tool_calls": ["view_file"],
            }
        ]
        result = adapter.format_for_injection(steps)
        assert "Step 5" in result
        assert "auth module" in result
        assert "view_file" in result
        assert "self-reflection" in result.lower()

    def test_format_truncates_long_thinking(self):
        import os
        adapter = self.SelfAdapter(
            conversation_id="test-conv-id",
            brain_dir="./brain_test",
        )
        long_thinking = "A" * 500
        steps = [{
            "step_index": 1,
            "created_at": None,
            "thinking": long_thinking,
            "content": "",
            "tool_calls": [],
        }]
        result = adapter.format_for_injection(steps, max_chars_per_thought=100)
        assert "..." in result
        assert len([line for line in result.split("\n") if "A" * 500 in line]) == 0
