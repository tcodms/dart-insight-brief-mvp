"""Streamlit UI for the first DART Insight Brief MVP."""

from __future__ import annotations

import json
import os
import tempfile
from html import escape
from pathlib import Path

import streamlit as st

from brief_presenter import build_brief_view_model
from config import missing_config
from service import run_company_brief_pipeline


st.set_page_config(
    page_title="DART Insight 취업용 기업분석 브리프",
    page_icon="📊",
    layout="wide",
)


def read_bytes(path: str) -> bytes:
    return Path(path).read_bytes()


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
            border-left: 5px solid #4f46e5;
            border-radius: 0.8rem;
            background: rgba(79, 70, 229, 0.04);
            margin-bottom: 1rem;
        }
        .brief-card {
            padding: 1rem 1.05rem;
            border: 1px solid rgba(49, 51, 63, 0.12);
            border-radius: 0.8rem;
            min-height: 13rem;
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


with st.sidebar:
    st.title("DART Insight")
    st.markdown(
        "장문 사업보고서를 사업·전략, 재무·경영진단, 인력·조직·ESG로 나누어 "
        "분석하고 원문 근거가 연결된 취업용 기업분석 브리프를 만듭니다."
    )
    missing = missing_config()
    if missing:
        st.warning(".env 설정 필요\n\n" + "\n".join(f"- {name}" for name in missing))
    else:
        st.success("네 Agent 환경변수 설정 완료")

st.title("📊 DART Insight 취업용 기업분석 브리프")
st.caption("1차 MVP: 사업보고서 1개 → Extract Agent 3개 → Python 병합 → Agent 4 브리프")

report_file = st.file_uploader("DART 사업보고서 PDF", type=["pdf"])

run_button = st.button(
    "기업분석 브리프 생성",
    type="primary",
    use_container_width=True,
    disabled=bool(missing_config()),
)

if run_button:
    if report_file is None:
        st.error("사업보고서 PDF를 업로드하세요.")
        st.stop()

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(report_file.getvalue())
            temp_path = temp_file.name

        status = st.status("분석을 시작합니다.", expanded=True)

        def show_progress(message: str) -> None:
            status.write(message)

        result = run_company_brief_pipeline(
            temp_path,
            source_document_name=Path(report_file.name).name,
            progress=show_progress,
        )
        status.update(label="기업분석 브리프 생성 완료", state="complete", expanded=False)
        st.session_state["analysis_result"] = result
    except Exception as exc:
        st.error("분석에 실패했습니다.")
        st.exception(exc)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

result = st.session_state.get("analysis_result")
if result:
    st.divider()
    render_brief_dashboard(result["company_brief"])

    paths = result["paths"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "브리프 Markdown 다운로드",
            data=read_bytes(paths["brief_markdown"]),
            file_name="company_brief.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "브리프 JSON 다운로드",
            data=read_bytes(paths["brief_json"]),
            file_name="company_brief_result.json",
            mime="application/json",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "병합 JSON 다운로드",
            data=read_bytes(paths["merged"]),
            file_name="merged_company_data.json",
            mime="application/json",
            use_container_width=True,
        )

    with st.expander("검증용 중간 산출물"):
        for index in range(1, 4):
            key = f"extract_{index}"
            st.download_button(
                f"Agent {index} 결과 JSON",
                data=read_bytes(paths[key]),
                file_name=Path(paths[key]).name,
                mime="application/json",
                key=f"download_{key}",
            )
        st.download_button(
            "전처리 manifest",
            data=read_bytes(paths["manifest"]),
            file_name="preprocess_manifest.json",
            mime="application/json",
        )

    with st.expander("Agent 4 원본 JSON"):
        st.json(result["company_brief"])

    with st.expander("병합 데이터 요약"):
        merged = result["merged_company_data"]
        st.write(f"총 근거 사실: {merged.get('fact_count', 0)}개")
        if merged.get("merge_warnings"):
            st.warning("\n".join(merged["merge_warnings"]))
        st.json(
            {
                "company_name": merged.get("company_name"),
                "report_period": merged.get("report_period"),
                "filing_date": merged.get("filing_date"),
                "batches": merged.get("batches"),
            }
        )

    with st.expander("자동 전처리 판정 근거"):
        detection = result["manifest"].get("detection", {})
        st.write(f"탐지 방식: {detection.get('method', '정보 없음')}")
        for batch_id, pages in detection.get("batches", {}).items():
            st.write(f"**{batch_id}**: {len(pages)}쪽")
            for reason in detection.get("selection_reasons", {}).get(batch_id, []):
                st.caption(reason)
