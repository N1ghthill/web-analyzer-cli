#!/usr/bin/env python3
"""Package entry point for Web Analyzer CLI."""

from __future__ import annotations

import argparse
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
    parser.add_argument("--full", action="store_true", help="Run complete quality audit")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP timeout in seconds")
    parser.add_argument(
        "--no-lighthouse",
        action="store_true",
        help="Disable optional lighthouse integration",
    )
    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "json"],
        help="Output format",
    )
    parser.add_argument(
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

    use_lighthouse = not args.no_lighthouse

    if args.arquivo:
        modo_arquivo(
            args.arquivo,
            full=args.full,
            timeout=args.timeout,
            use_lighthouse=use_lighthouse,
            output_format=args.format,
            report=args.report,
        )
        return 0

    if args.url:
        report_file = resolve_report_for_single_url(args.report, args.url, args.format)
        verificar_url(
            args.url,
            full=args.full,
            timeout=args.timeout,
            use_lighthouse=use_lighthouse,
            output_format=args.format,
            report_file=report_file,
        )
        return 0

    modo_interativo(
        full=args.full,
        timeout=args.timeout,
        use_lighthouse=use_lighthouse,
        output_format=args.format,
        report=args.report,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
