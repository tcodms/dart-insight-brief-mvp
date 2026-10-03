import pytest

from merge_builder import MergeValidationError, merge_extract_results


def sample(batch_id: str, category: str, statement: str, page: int) -> dict:
    return {
        "company_name": "테스트기업",
        "report_type": "사업보고서",
        "report_period": "2025-01-01 ~ 2025-12-31",
        "filing_date": "2026-03-18",
        "source_batch": batch_id,
        "source_document": "test.pdf",
        category: [f"[E001] {statement}"],
        "evidence_refs": [
            f"E001 | original_page={page} | section=테스트 | quote={statement}"
        ],
        "limitations": [],
    }


def test_merge_reassigns_global_ids():
    merged = merge_extract_results(
        [
            ("B01", "01_business_strategy", sample("01_business_strategy", "products_services", "서비스 A", 10)),
            ("B02", "02_finance_management", sample("02_finance_management", "financial_highlights", "당기순이익 10억원", 20)),
            ("B03", "03_workforce_esg", sample("03_workforce_esg", "employee_count_trend", "임직원 100명", 30)),
        ]
    )
    assert [fact["id"] for fact in merged["facts"]] == ["B01-E001", "B02-E001", "B03-E001"]
    assert merged["fact_count"] == 3
    assert merged["evidence_refs"][0].startswith("B01-E001 |")


def test_merge_rejects_fact_without_evidence():
    broken = sample("01_business_strategy", "products_services", "서비스 A", 10)
    broken["evidence_refs"] = []
    with pytest.raises(MergeValidationError):
        merge_extract_results(
            [
                ("B01", "01_business_strategy", broken),
                ("B02", "02_finance_management", sample("02_finance_management", "financial_highlights", "이익", 20)),
                ("B03", "03_workforce_esg", sample("03_workforce_esg", "employee_count_trend", "인원", 30)),
            ]
        )


def test_merge_normalizes_jo_eok_value_to_eok():
    merged = merge_extract_results(
        [
            ("B01", "01_business_strategy", sample("01_business_strategy", "products_services", "서비스 A", 10)),
            (
                "B02",
                "02_finance_management",
                sample(
                    "02_finance_management",
                    "industry_specific_metrics",
                    "metric_name=대손충당금 전입액 | value=1조 5,588 | unit=억원 | period=2025년",
                    20,
                ),
            ),
            ("B03", "03_workforce_esg", sample("03_workforce_esg", "employee_count_trend", "임직원 100명", 30)),
        ]
    )

    assert merged["facts"][1]["statement"] == (
        "metric_name=대손충당금 전입액 | value=15,588 | unit=억원 | period=2025년"
    )
