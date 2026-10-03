from brief_renderer import render_company_brief


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
    assert "## 주요 제품·서비스" in markdown
    assert "[KP01] 서비스 A" in markdown
