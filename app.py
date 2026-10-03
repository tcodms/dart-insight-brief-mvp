"""Command-line entry point for the DART Insight Brief MVP."""

from __future__ import annotations

import argparse

from config import print_config
from service import run_company_brief_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DART 취업용 기업분석 브리프 생성")
    parser.add_argument("report", help="분석할 사업보고서 PDF 경로")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print_config()
    result = run_company_brief_pipeline(
        args.report,
    )
    print(f"완료: {result['paths']['brief_markdown']}")


if __name__ == "__main__":
    main()
