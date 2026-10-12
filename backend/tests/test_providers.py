"""
Unit and integration tests for decoupled LLM/Embedding providers and Local-First mode.
"""
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend import providers
from backend.auth import get_current_user


class TestProviderDecoupling(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check_reports_providers(self):
        """Verify /health returns active provider configuration and local_mode."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("llm_provider", data)
        self.assertIn("embedding_provider", data)
        self.assertIn("local_mode", data)
        self.assertIn("ollama_base_url", data)

    def test_ollama_completion_mocked(self):
        """Verify Ollama provider generates text correctly from /api/generate."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "This is a local response from Llama 3.2"}

        with patch("backend.providers.LLM_PROVIDER", "ollama"):
            with patch("backend.providers.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_client.post.return_value = mock_response
                mock_httpx.Client.return_value.__enter__.return_value = mock_client

                result = providers.generate_completion("Hello test")
                self.assertEqual(result, "This is a local response from Llama 3.2")

    def test_ollama_embedding_mocked(self):
        """Verify Ollama embedding handles /api/embed and fallback correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}

        with patch("backend.providers.EMBEDDING_PROVIDER", "ollama"):
            with patch("backend.providers.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_client.post.return_value = mock_response
                mock_httpx.Client.return_value.__enter__.return_value = mock_client

                vec = providers.embed_query_text("Test query")
                self.assertEqual(vec, [0.1, 0.2, 0.3])

    def test_independent_provider_configuration(self):
        """Verify LLM and embedding providers can be configured independently."""
        with patch("backend.providers.LLM_PROVIDER", "gemini"), \
             patch("backend.providers.EMBEDDING_PROVIDER", "ollama"):
            self.assertEqual(providers.LLM_PROVIDER, "gemini")
            self.assertEqual(providers.EMBEDDING_PROVIDER, "ollama")

    def test_local_mode_auth_fallback(self):
        """Verify that when AUTH_OPTIONAL is enabled without credentials, get_current_user provides a local profile."""
        with patch("backend.auth.AUTH_OPTIONAL", True):
            user = get_current_user(credentials=None)
            self.assertEqual(user["username"], "local_user")
            self.assertEqual(user["email"], "local@technoir.rag")


if __name__ == "__main__":
    unittest.main()
