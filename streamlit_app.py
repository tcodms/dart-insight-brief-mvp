"""Streamlit UI for the first DART Insight Brief MVP."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st

from brief_ui import render_brief_dashboard
from config import missing_config
from service import run_company_brief_pipeline, sanitize_progress_message


st.set_page_config(
    page_title="DART Insight 취업용 기업분석 브리프",
    page_icon="📊",
    layout="wide",
)


def read_bytes(path: str) -> bytes:
    return Path(path).read_bytes()


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
            status.write(sanitize_progress_message(message))

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
