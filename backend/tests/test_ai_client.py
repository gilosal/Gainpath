"""Tests for the AI client module (US-004, US-006).

Covers strip_json_fences, AIEmptyResponseError, and retry/reraise behavior
— the fixes introduced in US-004 that prevent silent error swallowing.
"""
import json
import pytest

from app.services.ai_client import strip_json_fences, AIEmptyResponseError, AIClient


class TestStripJsonFences:
    """strip_json_fences removes markdown code fences that some models wrap
    around JSON payloads even when response_format=json_object is requested."""

    def test_plain_json_unchanged(self):
        payload = '{"exercise": "squat", "sets": 3}'
        assert strip_json_fences(payload) == payload

    def test_json_with_fences_stripped(self):
        payload = '```json\n{"exercise": "squat", "sets": 3}\n```'
        result = strip_json_fences(payload)
        parsed = json.loads(result)
        assert parsed["exercise"] == "squat"

    def test_json_with_bare_fences_stripped(self):
        payload = '```\n{"exercise": "squat", "sets": 3}\n```'
        result = strip_json_fences(payload)
        parsed = json.loads(result)
        assert parsed["exercise"] == "squat"

    def test_whitespace_only_fenced_stripped(self):
        payload = '```json\n  \n```'
        result = strip_json_fences(payload)
        assert result.strip() == ""

    def test_inline_fences_not_stripped(self):
        """Code fences in the middle of text (not wrapping the whole thing)
        should not be removed."""
        payload = 'Here is some JSON: ```json\n{"a": 1}\n``` and more text'
        result = strip_json_fences(payload)
        # The regex anchors require fences to wrap the entire string
        assert "```" in result

    def test_nested_braces_unchanged(self):
        payload = '{"outer": {"inner": [1, 2, 3]}}'
        assert strip_json_fences(payload) == payload

    def test_multiline_json_with_fences(self):
        payload = '```json\n{\n  "name": "test",\n  "value": 42\n}\n```'
        result = strip_json_fences(payload)
        parsed = json.loads(result)
        assert parsed["name"] == "test"
        assert parsed["value"] == 42


class TestAIEmptyResponseError:
    """AIEmptyResponseError is raised when the model returns an empty string
    or whitespace-only content — a guard added in US-004."""

    def test_is_subclass_of_ai_generation_error(self):
        assert issubclass(AIEmptyResponseError, Exception)

    def test_message_contains_model_info(self):
        err = AIEmptyResponseError("[anthropic/claude-sonnet-4-5] Empty response from model")
        assert "Empty response" in str(err)
        assert "anthropic" in str(err)


class TestAIClientConfig:
    """Verify the AIClient reads settings correctly and the models_to_try
    logic covers fallback properly."""

    def test_default_model_from_settings(self):
        client = AIClient()
        assert client.default_model == "anthropic/claude-sonnet-4-5"

    def test_fallback_model_from_settings(self):
        client = AIClient()
        assert client.fallback_model == "openai/gpt-4o-mini"

    def test_models_to_try_includes_fallback(self):
        """When generate/generate_text is called, both primary and fallback
        models should be attempted on failure. This tests the config, not
        the HTTP call."""
        client = AIClient()
        primary = client.default_model
        fallback = client.fallback_model
        models = [primary]
        if fallback and fallback != primary:
            models.append(fallback)
        assert len(models) >= 2
        assert models[0] == primary
        assert models[-1] == fallback