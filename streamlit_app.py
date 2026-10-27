"""Streamlit UI for company briefs and personal contribution reports."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st

from brief_ui import render_brief_dashboard
from config import missing_config
from contribution_service import run_contribution_pipeline
from service import run_company_brief_pipeline, sanitize_progress_message


st.set_page_config(
    page_title="DART Insight 취업용 기업분석 브리프",
    page_icon="📊",
    layout="wide",
)


def read_bytes(path: str) -> bytes:
    return Path(path).read_bytes()


def company_fact_label(data: dict) -> str:
    company = str(data.get("company_name") or "회사명 미기재").strip()
    period = str(data.get("report_period") or "").strip()
    year = period[:4] if period[:4].isdigit() else "연도 미기재"
    report_type = str(data.get("report_type") or "보고서").strip()
    return f"{company} {year}년 {report_type}"


def clear_company_result() -> None:
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("contribution_result", None)


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

report_file = st.file_uploader(
    "DART 사업보고서 PDF", type=["pdf"], on_change=clear_company_result
)

run_button = st.button(
    "기업분석 브리프 생성",
    type="primary",
    use_container_width=True,
    disabled=bool(missing_config()),
)

if run_button:
    st.session_state.pop("contribution_result", None)
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

st.divider()
st.header("개인 경험 연결")
st.caption("CV·직무기술서와 기업 fact를 연결해 자기소개서·면접용 보고서를 만듭니다.")

if result:
    fact_path = Path(result["paths"]["merged"])
    st.caption(f"사용할 기업 fact: {company_fact_label(result['merged_company_data'])}")
else:
    fact_path = None
    st.info("먼저 사업보고서로 기업 브리프를 생성하세요.")

cv_file = st.file_uploader(
    "CV PDF", type=["pdf"], key="cv_pdf",
    on_change=lambda: st.session_state.pop("contribution_result", None),
)
jd_file = st.file_uploader(
    "직무기술서(JD) PDF", type=["pdf"], key="jd_pdf",
    on_change=lambda: st.session_state.pop("contribution_result", None),
)
contribution_button = st.button(
    "개인 경험 연결",
    use_container_width=True,
    disabled=cv_file is None or jd_file is None or fact_path is None,
)

if contribution_button:
    st.session_state.pop("contribution_result", None)
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            cv_path = Path(temp_dir) / "cv.pdf"
            jd_path = Path(temp_dir) / "jd.pdf"
            cv_path.write_bytes(cv_file.getvalue())
            jd_path.write_bytes(jd_file.getvalue())

            status = st.status("개인 경험 연결을 시작합니다.", expanded=True)
            contribution_result = run_contribution_pipeline(
                cv_path,
                jd_path,
                fact_path,
                progress=status.write,
            )
            status.update(label="개인 경험 연결 완료", state="complete", expanded=False)
            st.session_state["contribution_result"] = contribution_result
    except Exception as exc:
        st.error("개인 경험 연결에 실패했습니다.")
        st.exception(exc)

contribution_result = st.session_state.get("contribution_result")
if contribution_result:
    st.subheader("개인 경험 연결 보고서")
    st.markdown(contribution_result["report"])
    st.download_button(
        "보고서 Markdown 다운로드",
        data=read_bytes(contribution_result["paths"]["report_markdown"]),
        file_name="contribution_report.md",
        mime="text/markdown",
    )
