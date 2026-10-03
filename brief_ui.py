"""Streamlit components for the reader-friendly company brief."""

from __future__ import annotations

from html import escape

import streamlit as st

from brief_presenter import build_brief_view_model


def render_item_list(items: list[dict[str, str]]) -> None:
    if not items:
        st.caption("확인된 정보가 없습니다.")
        return
    for item in items:
        st.markdown(f"- {item['text']}")


def render_brief_dashboard(brief: dict) -> None:
    view = build_brief_view_model(brief)

    st.markdown(
        """
        <style>
        .brief-summary {
            padding: 1.2rem 1.35rem;
            border: 1px solid rgba(49, 51, 63, 0.14);
            border-radius: 0.8rem;
            background: rgba(79, 70, 229, 0.04);
            margin-bottom: 1rem;
        }
        .brief-card {
            padding: 1rem 1.05rem;
            border: 1px solid rgba(49, 51, 63, 0.12);
            border-radius: 0.8rem;
            box-sizing: border-box;
            height: 16rem;
            overflow-y: auto;
            background: rgba(250, 250, 252, 0.72);
        }
        .brief-card h4 { margin: 0 0 0.7rem 0; }
        .brief-card ul { padding-left: 1.15rem; }
        .brief-card li { margin-bottom: 0.55rem; }
        .brief-label {
            color: #4f46e5;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }
        button[data-baseweb="tab"] {
            color: #3f3f46 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #4f46e5 !important;
            font-weight: 700 !important;
        }
        div[data-baseweb="tab-highlight"] {
            background-color: #4f46e5 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.subheader(f"{view['company_name']} 취업용 기업분석 브리프")
    if view["data_recency"]:
        st.caption(view["data_recency"])
    st.markdown(
        f"<div class='brief-summary'><span class='brief-label'>기업 한눈에 보기</span>"
        f"<div style='margin-top:0.55rem; line-height:1.7'>{escape(view['one_sentence'])}</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("### 3분 핵심 요약")
    columns = st.columns(3)
    for column, highlight in zip(columns, view["highlights"]):
        with column:
            items_html = "".join(
                f"<li>{escape(item['text'])}</li>" for item in highlight["items"]
            ) or "<li>확인된 정보가 없습니다.</li>"
            st.markdown(
                f"<div class='brief-card'><h4>{escape(highlight['title'])}</h4>"
                f"<ul>{items_html}</ul></div>",
                unsafe_allow_html=True,
            )

    st.markdown("### 취업 준비 핵심 포인트")
    if not view["evidence_cards"]:
        st.info("취업 준비에 활용할 근거 카드가 생성되지 않았습니다.")
    for card in view["evidence_cards"]:
        with st.expander(card["title"]):
            st.markdown(f"**기업 사실**  \n{card['company_fact']}")
            if card["why_it_matters"]:
                st.markdown(f"**왜 중요한가**  \n{card['why_it_matters']}")
            if card["usable_question"]:
                st.markdown(f"**면접·지원서에서 생각해볼 질문**  \n{card['usable_question']}")
            source_parts = []
            if card["original_pages"]:
                source_parts.append("원본 " + ", ".join(card["original_pages"]) + "쪽")
            if card["evidence_ids"]:
                source_parts.append("근거 " + ", ".join(card["evidence_ids"]))
            if source_parts:
                st.caption(" · ".join(source_parts))

    st.markdown("### 상세 분석")
    tabs = st.tabs([group["title"] for group in view["detail_groups"]])
    for tab, group in zip(tabs, view["detail_groups"]):
        with tab:
            for section in group["sections"]:
                st.markdown(f"#### {section['title']}")
                render_item_list(section["items"])

    with st.expander("공식 표현과 해석 시 유의사항"):
        if view["official_terms"]:
            st.markdown("**회사가 공식적으로 사용한 표현**")
            st.write(" · ".join(item["text"] for item in view["official_terms"]))
        st.markdown("**해석 시 유의사항**")
        if view["limitations"]:
            for limitation in view["limitations"]:
                st.markdown(f"- {limitation}")
        else:
            st.caption("특이사항 없음")
