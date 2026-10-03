"""Development-only preview that renders a saved Agent 4 result without API calls."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from brief_ui import render_brief_dashboard


st.set_page_config(page_title="브리프 양식 미리보기", page_icon="👀", layout="wide")
st.title("👀 브리프 양식 미리보기")
st.caption("저장된 Agent 4 JSON을 화면에 표시합니다. Agent API를 호출하지 않습니다.")

uploaded = st.file_uploader("company_brief_result.json", type=["json"])

if uploaded is not None:
    brief = json.loads(uploaded.getvalue().decode("utf-8-sig"))
    render_brief_dashboard(brief)
else:
    candidates = sorted(
        Path("output/runs").glob("*/company_brief_result.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        latest = candidates[0]
        st.info(f"최근 저장 결과 사용: {latest}")
        render_brief_dashboard(json.loads(latest.read_text(encoding="utf-8")))
    else:
        st.info("저장 결과가 없습니다. company_brief_result.json을 업로드하세요.")
