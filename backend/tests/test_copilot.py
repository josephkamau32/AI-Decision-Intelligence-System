"""
Unit tests for AI Copilot Agent with complete mocking (zero external network/API calls).
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.copilot.agent import AICopilotAgent, CopilotAgentProxy, get_copilot_agent


class TestCopilotAgent:

    def test_query_without_api_key_returns_configuration_message(self):
        """When API key is not configured, query returns guidance without attempting network calls."""
        with patch("backend.copilot.agent.settings") as mock_settings:
            mock_settings.google_api_key = ""
            agent = AICopilotAgent()
            response = agent.query("How do I train a model?")
            assert "AI Copilot requires a Google API key to be configured" in response
            assert "GOOGLE_API_KEY" in response

    def test_query_success_with_mocked_llm(self):
        """When API key is set, query correctly prompts the LLM and extracts the response text."""
        with patch("backend.copilot.agent.settings") as mock_settings, patch(
            "google.generativeai.configure"
        ) as mock_configure, patch(
            "google.generativeai.GenerativeModel"
        ) as mock_model_cls:

            mock_settings.google_api_key = "mock-valid-key"

            # Mock the Gemini GenerativeModel instance and its generate_content response
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "This is a simulated AI Copilot answer."
            mock_instance.generate_content.return_value = mock_response
            mock_model_cls.return_value = mock_instance

            agent = AICopilotAgent()
            result = agent.query("Explain random forest")

            assert result == "This is a simulated AI Copilot answer."
            mock_configure.assert_called_with(api_key="mock-valid-key")
            mock_model_cls.assert_called_with("gemini-pro")
            mock_instance.generate_content.assert_called_once()

            call_prompt = mock_instance.generate_content.call_args[0][0]
            assert "User question: Explain random forest" in call_prompt

    def test_query_handles_auth_error_gracefully(self):
        """When the LLM raises an unauthenticated / invalid key error, agent catches it and returns guidance."""
        with patch("backend.copilot.agent.settings") as mock_settings, patch(
            "google.generativeai.configure"
        ), patch("google.generativeai.GenerativeModel") as mock_model_cls:

            mock_settings.google_api_key = "invalid-key"
            mock_instance = MagicMock()

            class UnauthenticatedError(Exception):
                pass

            mock_instance.generate_content.side_effect = UnauthenticatedError(
                "API key not valid. Please pass a valid API key."
            )
            mock_model_cls.return_value = mock_instance

            agent = AICopilotAgent()
            result = agent.query("Hello")

            assert "There was an authentication issue with the AI service" in result

    def test_query_handles_quota_error_gracefully(self):
        """When the LLM raises a quota/resource exhausted error, agent catches it and informs the user."""
        with patch("backend.copilot.agent.settings") as mock_settings, patch(
            "google.generativeai.configure"
        ), patch("google.generativeai.GenerativeModel") as mock_model_cls:

            mock_settings.google_api_key = "test-key"
            mock_instance = MagicMock()

            class ResourceExhausted(Exception):
                pass

            mock_instance.generate_content.side_effect = ResourceExhausted(
                "ResourceExhausted: Quota exceeded"
            )
            mock_model_cls.return_value = mock_instance

            agent = AICopilotAgent()
            result = agent.query("Hello")

            assert "The AI service quota has been exceeded" in result

    def test_query_handles_model_not_found_gracefully(self):
        """When the model is not found, agent returns enabling guidance."""
        with patch("backend.copilot.agent.settings") as mock_settings, patch(
            "google.generativeai.configure"
        ), patch("google.generativeai.GenerativeModel") as mock_model_cls:

            mock_settings.google_api_key = "test-key"
            mock_instance = MagicMock()

            class NotFoundError(Exception):
                pass

            mock_instance.generate_content.side_effect = NotFoundError(
                "Model not found"
            )
            mock_model_cls.return_value = mock_instance

            agent = AICopilotAgent()
            result = agent.query("Hello")

            assert "The Gemini API is not enabled or accessible" in result

    def test_copilot_proxy_and_singleton(self):
        """Verify proxy forwards queries correctly."""
        proxy = CopilotAgentProxy()
        with patch("backend.copilot.agent.settings") as mock_settings:
            mock_settings.google_api_key = ""
            res = proxy.query("Test question")
            assert "AI Copilot requires a Google API key to be configured" in res
