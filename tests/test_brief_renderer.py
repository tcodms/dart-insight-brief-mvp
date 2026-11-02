from brief_renderer import render_company_brief
from brief_presenter import (
    build_brief_view_model,
    emphasize_markdown,
    find_highlight_terms,
    parse_evidence_card,
    split_tag,
    truncate_text,
)


def test_split_tag_hides_internal_identifier():
    assert split_tag("[KP01] 서비스 A") == ("KP01", "서비스 A")
    assert split_tag("태그 없음") == ("", "태그 없음")


def test_truncate_text_preserves_short_text_and_shortens_long_text():
    assert truncate_text("짧은 문장", 20) == "짧은 문장"
    assert truncate_text("가" * 30, 10) == "가" * 9 + "…"


def test_highlight_terms_use_official_names_found_in_analysis():
    result = {
        "key_products_services": ["[KP01] IBK GenAI를 운영한다."],
        "official_terms": ["[T01] IBK GenAI.", "[T02] 사용되지 않은 표현."],
    }
    assert find_highlight_terms(result) == ["IBK GenAI"]
    assert emphasize_markdown("IBK GenAI를 운영한다.", ["IBK GenAI"]) == (
        "**IBK GenAI**를 운영한다."
    )


def test_parse_evidence_card():
    card = parse_evidence_card(
        "[J01] company_fact=AI 플랫폼을 구축했다 | why_it_matters=전략 방향을 보여준다 "
        "| usable_question=왜 AI를 확대하는가 | official_term=AI 플랫폼 "
        "| evidence_ids=B01-E001,B02-E003 | original_pages=31,737"
    )
    assert card["id"] == "J01"
    assert card["title"] == "AI 플랫폼"
    assert card["evidence_ids"] == ["B01-E001", "B02-E003"]
    assert card["original_pages"] == ["31", "737"]


def test_build_view_model_prioritizes_three_items():
    long_text = "긴 문장 " + "가" * 140
    view = build_brief_view_model(
        {
            "company_name": "테스트기업",
            "company_in_one_sentence": "[SUM01] 한눈에 보는 기업",
            "business_and_revenue_model": [
                f"[BR0{i}] {long_text if i == 1 else f'사업 {i}'}"
                for i in range(1, 5)
            ],
        }
    )
    assert view["one_sentence"] == "한눈에 보는 기업"
    assert len(view["highlights"][0]["items"]) == 3
    assert view["highlights"][0]["items"][0]["text"] == long_text
    assert not view["highlights"][0]["items"][0]["text"].endswith("…")


def test_render_company_brief():
    markdown = render_company_brief(
        {
            "company_name": "테스트기업",
            "company_in_one_sentence": "[SUM01] 테스트 기업이다.",
            "key_products_services": ["[KP01] 서비스 A"],
            "data_recency": "2025년 사업보고서 기준",
            "limitations": [],
        }
    )
    assert "# 테스트기업 취업용 기업분석 브리프" in markdown
    assert "## 3분 핵심 요약" in markdown
    assert "## 취업 준비 핵심 포인트" in markdown
    assert "#### 주요 제품·서비스" in markdown
    assert "서비스 A" in markdown
    assert "[KP01]" not in markdown


def test_render_company_brief_links_summary_and_detail_to_fact_ids():
    markdown = render_company_brief({
        "company_name": "다른 기업",
        "company_in_one_sentence": "[SUM01] 수익은 제품 A에서 발생한다.",
        "key_products_services": ["[KP01] 제품 A를 판매한다."],
        "evidence_ids": [
            "SUM01 | source_ids=B02-E003 | basis=매출 구조",
            "KP01 | source_ids=B01-E001,B01-E002 | basis=제품 설명",
        ],
    })
    assert "[수익은 제품 A에서 발생한다.](#evidence-id-B02-E003)" in markdown
    assert "[제품 A를 판매한다.](#evidence-id-B01-E001)" in markdown
    assert "[근거 2](#evidence-id-B01-E002)" in markdown
