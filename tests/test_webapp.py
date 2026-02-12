import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.url_safety import validate_public_url
from src.webapp import app, reset_runtime_state


class UrlSafetyTests(unittest.TestCase):
    @patch("src.url_safety._resolve_host_ips")
    def test_validate_public_url_accepts_public_host(self, mock_resolve):
        import ipaddress

        mock_resolve.return_value = [ipaddress.ip_address("93.184.216.34")]
        safe = validate_public_url("example.com")
        self.assertEqual(safe, "https://example.com")

    def test_validate_public_url_blocks_localhost(self):
        with self.assertRaises(ValueError):
            validate_public_url("http://localhost:8000")

    def test_validate_public_url_blocks_private_ip(self):
        with self.assertRaises(ValueError):
            validate_public_url("http://192.168.0.10")


class WebApiTests(unittest.TestCase):
    def setUp(self):
        reset_runtime_state()
        self.client = TestClient(app)

    def _headers(self, api_key: str = "test-key"):
        return {"x-api-key": api_key}

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("version", payload)
        self.assertIn("auth_configured", payload)
        self.assertIn("rate_limit", payload)

    def test_analyze_requires_api_key(self):
        with patch.dict(os.environ, {"WEB_ANALYZER_API_KEY": "test-key"}, clear=False):
            response = self.client.post(
                "/api/analyze",
                json={
                    "url": "https://example.com",
                    "mode": "full",
                    "timeout": 10,
                },
            )

        self.assertEqual(response.status_code, 401)
        self.assertIn("Missing x-api-key", response.json()["detail"])

    def test_analyze_rejects_invalid_api_key(self):
        with patch.dict(os.environ, {"WEB_ANALYZER_API_KEY": "test-key"}, clear=False):
            response = self.client.post(
                "/api/analyze",
                headers=self._headers("wrong"),
                json={
                    "url": "https://example.com",
                    "mode": "full",
                    "timeout": 10,
                },
            )

        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid API key", response.json()["detail"])

    @patch("src.webapp.validate_public_url")
    @patch("src.webapp.run_full_audit")
    def test_analyze_full_sync(self, mock_full, mock_validate):
        mock_validate.return_value = "https://example.com"
        mock_full.return_value = {
            "mode": "full",
            "error": None,
            "overall_score": 88.5,
            "criteria": {
                "performance": {"score": 90, "method": "local"},
                "security": {"score": 86, "method": "local"},
                "seo": {"score": 89, "method": "local"},
                "accessibility": {"score": 87, "method": "local"},
                "best_practices": {"score": 91, "method": "local"},
            },
        }

        with patch.dict(
            os.environ,
            {
                "WEB_ANALYZER_API_KEY": "test-key",
                "WEB_ANALYZER_RATE_LIMIT_REQUESTS": "50",
                "WEB_ANALYZER_RATE_LIMIT_WINDOW_SECONDS": "60",
            },
            clear=False,
        ):
            response = self.client.post(
                "/api/analyze",
                headers=self._headers(),
                json={
                    "url": "https://example.com",
                    "mode": "full",
                    "timeout": 10,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"]["overall_score"], 88.5)
        mock_validate.assert_called_once()
        mock_full.assert_called_once_with("https://example.com", timeout=10)

    @patch("src.webapp.validate_public_url", side_effect=ValueError("blocked"))
    def test_analyze_rejects_bad_url(self, _mock_validate):
        with patch.dict(os.environ, {"WEB_ANALYZER_API_KEY": "test-key"}, clear=False):
            response = self.client.post(
                "/api/analyze",
                headers=self._headers(),
                json={
                    "url": "http://localhost",
                    "mode": "full",
                    "timeout": 10,
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "blocked")

    @patch("src.webapp.validate_public_url")
    @patch("src.webapp.run_basic_analysis")
    def test_rate_limit_enforced(self, mock_basic, mock_validate):
        mock_validate.return_value = "https://example.com"
        mock_basic.return_value = {
            "mode": "basic",
            "error": None,
            "status": 200,
            "title": "OK",
        }

        with patch.dict(
            os.environ,
            {
                "WEB_ANALYZER_API_KEY": "test-key",
                "WEB_ANALYZER_RATE_LIMIT_REQUESTS": "1",
                "WEB_ANALYZER_RATE_LIMIT_WINDOW_SECONDS": "60",
            },
            clear=False,
        ):
            first = self.client.post(
                "/api/analyze",
                headers=self._headers(),
                json={
                    "url": "https://example.com",
                    "mode": "basic",
                    "timeout": 10,
                },
            )
            second = self.client.post(
                "/api/analyze",
                headers=self._headers(),
                json={
                    "url": "https://example.com",
                    "mode": "basic",
                    "timeout": 10,
                },
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertIn("Retry-After", second.headers)


if __name__ == "__main__":
    unittest.main()
