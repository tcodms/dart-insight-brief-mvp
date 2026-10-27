"""CLI entry point for standalone CV and JD Studio Agent analysis."""

from __future__ import annotations

import argparse

from candidate_document_service import run_candidate_document_analysis


def main() -> None:
    parser = argparse.ArgumentParser(description="CV/JD PDF를 Upstage Studio Agent로 분석")
    parser.add_argument("--cv", help="CV PDF 경로")
    parser.add_argument("--jd", help="직무기술서(JD) PDF 경로")
    args = parser.parse_args()
    if not args.cv and not args.jd:
        parser.error("--cv 또는 --jd를 하나 이상 지정하세요.")

    result = run_candidate_document_analysis(args.cv, args.jd, progress=print)
    for name, path in result["paths"].items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
