"""Split one long DART report into three purpose-specific PDFs."""

from __future__ import annotations

import copy
import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from config import FONT_NAME, FONT_PATH
from file_manager import save_json
from section_detector import compact_ranges, detect_report_sections


BATCHES = {
    "01_business_strategy": {
        "title": "Business & Strategy Extract Input",
        "description": "Business structure, products, market, R&D, investment and strategy",
    },
    "02_finance_management": {
        "title": "Finance & Management Extract Input",
        "description": "Financial trends, change drivers, risks and management discussion",
    },
    "03_workforce_esg": {
        "title": "Workforce, Organization & ESG Extract Input",
        "description": "Employees, work systems, organization, governance and ESG",
    },
}


def _register_font() -> str:
    if FONT_PATH.is_file():
        try:
            pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_PATH)))
            return FONT_NAME
        except Exception:
            pass
    return "Helvetica"


def _cover_page(batch_id: str, metadata: dict, width: float, height: float):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(width, height))
    font = _register_font()
    pdf.setFont(font, 18)
    pdf.drawString(48, height - 72, metadata["title"])
    pdf.setFont(font, 10)
    lines = [
        f"SOURCE_BATCH: {batch_id}",
        f"SOURCE_DOCUMENT: {metadata['source_document']}",
        f"SELECTED_ORIGINAL_PAGES: {metadata['selected_ranges']}",
        f"PURPOSE: {metadata['description']}",
        "PAGE_NUMBER_RULE: Use ORIGINAL_PDF_PAGE, not prepared PDF page number.",
    ]
    y = height - 110
    for line in lines:
        pdf.drawString(48, y, line)
        y -= 22
    pdf.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def _page_overlay(batch_id: str, original_page: int, width: float, height: float):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(width, height))
    pdf.setFillColorRGB(0.10, 0.22, 0.62)
    pdf.rect(0, height - 18, width, 18, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    # Use the project's embedded font instead of a built-in PDF font. Some
    # DART pages already define Helvetica resources with incompatible
    # encodings, which can corrupt only part of the merged header visually.
    pdf.setFont(_register_font(), 8)
    pdf.drawString(
        12,
        height - 13,
        f"ORIGINAL_PDF_PAGE: {original_page} | SOURCE_BATCH: {batch_id}",
    )
    pdf.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def preprocess_report(
    source_pdf: str | Path,
    output_dir: str | Path,
    source_document_name: str | None = None,
) -> dict:
    source_path = Path(source_pdf)
    if not source_path.is_file():
        raise FileNotFoundError(f"사업보고서 PDF가 없습니다: {source_path}")

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(source_path))
    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("페이지가 없는 PDF입니다.")
    display_source_name = source_document_name or source_path.name

    first_page = reader.pages[0]
    width = float(first_page.mediabox.width)
    height = float(first_page.mediabox.height)

    detection = detect_report_sections(str(source_path))
    manifest = {
        "preprocessor": "dart_outline_auto_detector_v1",
        "source_pdf": str(source_path.resolve()),
        "source_document": display_source_name,
        "source_page_count": total_pages,
        "detection": detection,
        "batches": {},
    }

    for batch_id, batch_info in BATCHES.items():
        selected_pages = detection["batches"][batch_id]
        spec = compact_ranges(selected_pages)
        output_pdf = target_dir / f"{batch_id}.pdf"
        writer = PdfWriter()

        cover_metadata = {
            **batch_info,
            "source_document": display_source_name,
            "selected_ranges": spec,
        }
        writer.add_page(_cover_page(batch_id, cover_metadata, width, height))

        mapping = [{"prepared_page": 1, "original_page": 0}]
        for prepared_index, original_page in enumerate(selected_pages, start=2):
            page = writer.add_page(copy.deepcopy(reader.pages[original_page - 1]))
            overlay = _page_overlay(
                batch_id,
                original_page,
                float(page.mediabox.width),
                float(page.mediabox.height),
            )
            page.merge_page(overlay)
            mapping.append(
                {"prepared_page": prepared_index, "original_page": original_page}
            )

        with output_pdf.open("wb") as output_file:
            writer.write(output_file)

        manifest["batches"][batch_id] = {
            "output_pdf": str(output_pdf.resolve()),
            "description": batch_info["description"],
            "selected_pages": selected_pages,
            "selected_ranges": spec,
            "prepared_page_count": len(selected_pages) + 1,
            "page_mapping": mapping,
            "selection_reasons": detection["selection_reasons"][batch_id],
        }

    save_json(manifest, target_dir / "preprocess_manifest.json")
    return manifest
