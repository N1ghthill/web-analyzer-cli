"""Utility functions for the Web Analyzer CLI."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .analyzer import normalize_url, verificar_url


def _slugify_url(url: str) -> str:
    normalized = normalize_url(url)
    cleaned = re.sub(r"^https?://", "", normalized, flags=re.IGNORECASE)
    cleaned = cleaned.strip().lower().replace("/", "-")
    cleaned = re.sub(r"[^a-z0-9._-]", "-", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "report"


def _resolve_report_path(
    report: Optional[str],
    url: str,
    output_format: str,
    single_mode: bool,
) -> Optional[str]:
    if not report:
        return None

    ext = "json" if output_format == "json" else "txt"
    base = Path(report)

    if single_mode and (base.suffix or not base.exists()):
        if not base.suffix:
            base = base.with_suffix(f".{ext}")
        return str(base)

    base.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"{_slugify_url(url)}-{timestamp}.{ext}"
    return str(base / filename)


def modo_interativo(
    full: bool = False,
    timeout: int = 10,
    use_lighthouse: bool = True,
    output_format: str = "text",
    report: Optional[str] = None,
):
    """Interactive mode to test multiple URLs."""
    print(
        "\n"
        "WEB ANALYZER CLI\n"
        "----------------\n"
        "Type one URL per line and press Enter.\n"
        "Type 'sair' to exit.\n"
    )

    while True:
        url = input("URL: ").strip()

        if url.lower() in ["sair", "exit", "quit"]:
            print("\nBye!")
            break

        if not url:
            continue

        report_file = _resolve_report_path(report, url, output_format, single_mode=False)
        verificar_url(
            url,
            full=full,
            timeout=timeout,
            use_lighthouse=use_lighthouse,
            output_format=output_format,
            report_file=report_file,
        )


def modo_arquivo(
    arquivo: str,
    full: bool = False,
    timeout: int = 10,
    use_lighthouse: bool = True,
    output_format: str = "text",
    report: Optional[str] = None,
):
    """Read URLs from a file and execute checks."""
    try:
        with open(arquivo, "r", encoding="utf-8") as file_handle:
            urls = [line.strip() for line in file_handle if line.strip()]

        print(f"Loaded {len(urls)} URLs from {arquivo}")

        for url in urls:
            report_file = _resolve_report_path(report, url, output_format, single_mode=False)
            verificar_url(
                url,
                full=full,
                timeout=timeout,
                use_lighthouse=use_lighthouse,
                output_format=output_format,
                report_file=report_file,
            )

    except FileNotFoundError:
        print(f"Error: file '{arquivo}' not found")
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}")


def mostrar_ajuda():
    """Print help text with examples."""
    print(
        "\n"
        "WEB ANALYZER CLI - usage\n"
        "\n"
        "Basic check:\n"
        "  web-analyzer <url>\n"
        "\n"
        "Full audit (scores for performance/security/seo/accessibility/best-practices):\n"
        "  web-analyzer <url> --full\n"
        "\n"
        "Read URLs from file:\n"
        "  web-analyzer --arquivo urls.txt [--full]\n"
        "\n"
        "Output format and report file/directory:\n"
        "  web-analyzer <url> --full --format json --report report.json\n"
        "  web-analyzer --arquivo urls.txt --full --report ./reports\n"
        "\n"
        "Flags:\n"
        "  --timeout <seconds>      request timeout (default: 10)\n"
        "  --no-lighthouse          skip optional lighthouse integration\n"
        "  --format text|json       output format (default: text)\n"
        "\n"
        "Tip: install lighthouse for stronger browser-level metrics:\n"
        "  npm install -g lighthouse\n"
    )


def resolve_report_for_single_url(report: Optional[str], url: str, output_format: str) -> Optional[str]:
    """Helper used by CLI for single URL mode."""
    return _resolve_report_path(report, url, output_format, single_mode=True)
