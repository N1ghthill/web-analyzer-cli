#!/usr/bin/env python3
"""Package entry point for Web Analyzer CLI."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .analyzer import verificar_url
from .utils import (
    modo_arquivo,
    modo_interativo,
    mostrar_ajuda,
    resolve_report_for_single_url,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("url", nargs="?", help="URL to analyze")
    parser.add_argument("-f", "--arquivo", dest="arquivo", help="Path to file containing URLs")
    parser.add_argument("-F", "--full", action="store_true", help="Run complete quality audit")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="HTTP timeout in seconds")
    parser.add_argument(
        "-o",
        "--format",
        default="text",
        choices=["text", "json"],
        help="Output format",
    )
    parser.add_argument("-j", "--json", action="store_true", help="Shortcut for --format json")
    parser.add_argument(
        "-r",
        "--report",
        help=(
            "Output file for single URL mode, or directory for batch/interative modes"
        ),
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.help:
        mostrar_ajuda()
        return 0

    if args.timeout <= 0:
        print("Error: --timeout must be greater than zero")
        return 1

    output_format = "json" if args.json else args.format

    if args.arquivo:
        modo_arquivo(
            args.arquivo,
            full=args.full,
            timeout=args.timeout,
            output_format=output_format,
            report=args.report,
        )
        return 0

    if args.url:
        report_file = resolve_report_for_single_url(args.report, args.url, output_format)
        verificar_url(
            args.url,
            full=args.full,
            timeout=args.timeout,
            output_format=output_format,
            report_file=report_file,
        )
        return 0

    modo_interativo(
        full=args.full,
        timeout=args.timeout,
        output_format=output_format,
        report=args.report,
    )
    return 0


def main_full(argv: Optional[List[str]] = None) -> int:
    """Shortcut entry point for full audit mode."""
    args = list(sys.argv[1:] if argv is None else argv)
    return main(["--full", *args])


def main_batch(argv: Optional[List[str]] = None) -> int:
    """Shortcut entry point for batch mode from file.

    Usage:
      wab urls.txt
      wab urls.txt --json -r ./reports
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: wab <arquivo_urls> [opcoes]")
        return 1
    return main(["--arquivo", args[0], "--full", *args[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
