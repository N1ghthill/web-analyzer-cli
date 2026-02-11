import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.url_safety import validate_public_url
from src.webapp import app


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
        self.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("src.webapp.validate_public_url")
    @patch("src.webapp.run_full_audit")
    def test_analyze_full(self, mock_full, mock_validate):
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

        response = self.client.post(
            "/api/analyze",
            json={
                "url": "https://example.com",
                "mode": "full",
                "timeout": 10,
                "use_lighthouse": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"]["overall_score"], 88.5)
        mock_validate.assert_called_once()
        mock_full.assert_called_once()

    @patch("src.webapp.validate_public_url", side_effect=ValueError("blocked"))
    def test_analyze_rejects_bad_url(self, _mock_validate):
        response = self.client.post(
            "/api/analyze",
            json={
                "url": "http://localhost",
                "mode": "full",
                "timeout": 10,
                "use_lighthouse": False,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "blocked")


if __name__ == "__main__":
    unittest.main()
