import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from src import analyzer
from src.main import build_parser, main_batch, main_full


class FakeResponse:
    def __init__(self, url="https://example.com", status_code=200, text="", headers=None, encoding="utf-8"):
        self.url = url
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self.encoding = encoding
        self.content = text.encode(encoding)


SAMPLE_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="A compact test page used for website quality checks and scoring output." />
    <meta name="robots" content="index,follow" />
    <link rel="canonical" href="https://example.com" />
    <link rel="icon" href="/favicon.ico" />
    <title>Example Quality Test Page</title>
  </head>
  <body>
    <h1>Sample heading</h1>
    <form>
      <label for="email">Email</label>
      <input id="email" type="email" />
      <button aria-label="send">Send</button>
    </form>
    <img src="/hero.jpg" alt="Hero image" />
    <a href="https://example.com/docs" target="_blank" rel="noopener">Docs</a>
  </body>
</html>
"""


class AnalyzerTests(unittest.TestCase):
    def test_calculate_overall_score(self):
        criteria_scores = {
            "performance": 80,
            "security": 90,
            "seo": 70,
            "accessibility": 60,
            "best_practices": 50,
        }
        score = analyzer.calculate_overall_score(criteria_scores)
        self.assertAlmostEqual(score, 75.0)

    @patch("src.analyzer.requests.get")
    def test_run_full_audit_local_only(self, mock_get):
        mock_get.return_value = FakeResponse(
            text=SAMPLE_HTML,
            headers={
                "Strict-Transport-Security": "max-age=31536000",
                "Content-Security-Policy": "default-src 'self'",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": "geolocation=()",
            },
        )

        result = analyzer.run_full_audit("https://example.com")

        self.assertEqual(result["mode"], "full")
        self.assertIsNone(result["error"])
        self.assertEqual(result["status"], 200)
        self.assertIn("overall_score", result)
        self.assertGreaterEqual(result["overall_score"], 0)
        self.assertLessEqual(result["overall_score"], 100)
        self.assertNotIn("lighthouse", result)

        criteria = result["criteria"]
        for key in ["performance", "security", "seo", "accessibility", "best_practices"]:
            self.assertIn(key, criteria)
            self.assertIn("score", criteria[key])
            self.assertGreaterEqual(criteria[key]["score"], 0)
            self.assertLessEqual(criteria[key]["score"], 100)

    @patch("src.analyzer.requests.get", side_effect=Exception("boom"))
    def test_run_basic_analysis_handles_unexpected_error(self, _mock_get):
        result = analyzer.run_basic_analysis("https://example.com")
        self.assertEqual(result["mode"], "basic")
        self.assertEqual(result["url"], "https://example.com")
        self.assertIn("boom", result["error"])


class CliParserTests(unittest.TestCase):
    def test_parser_accepts_full_and_format(self):
        parser = build_parser()
        args = parser.parse_args(["https://example.com", "-F", "-o", "json", "-t", "15"])
        self.assertEqual(args.url, "https://example.com")
        self.assertTrue(args.full)
        self.assertEqual(args.format, "json")
        self.assertEqual(args.timeout, 15)

    def test_parser_accepts_json_shortcut(self):
        parser = build_parser()
        args = parser.parse_args(["https://example.com", "-j"])
        self.assertEqual(args.url, "https://example.com")
        self.assertTrue(args.json)

    def test_parser_accepts_file_mode(self):
        parser = build_parser()
        args = parser.parse_args(["--arquivo", "urls.txt", "--full"])
        self.assertEqual(args.arquivo, "urls.txt")
        self.assertTrue(args.full)

    @patch("src.main.main")
    def test_main_full_wrapper(self, mock_main):
        mock_main.return_value = 0
        rc = main_full(["https://example.com", "-j"])
        self.assertEqual(rc, 0)
        mock_main.assert_called_once_with(["--full", "https://example.com", "-j"])

    @patch("src.main.main")
    def test_main_batch_wrapper(self, mock_main):
        mock_main.return_value = 0
        rc = main_batch(["urls.txt", "-j", "-r", "./reports"])
        self.assertEqual(rc, 0)
        mock_main.assert_called_once_with(
            ["--arquivo", "urls.txt", "--full", "-j", "-r", "./reports"]
        )

    def test_main_batch_wrapper_requires_file(self):
        with redirect_stdout(StringIO()):
            rc = main_batch([])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
