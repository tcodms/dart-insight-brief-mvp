from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from preprocessor import preprocess_report
from section_detector import detect_report_sections


def make_pdf(path: Path, pages: int = 60) -> None:
    raw_path = path.with_name("raw.pdf")
    pdf = canvas.Canvas(str(raw_path))
    for page in range(1, pages + 1):
        text = f"Test source page {page}"
        if page == 50:
            text += " ESG sustainability"
        pdf.drawString(72, 720, text)
        pdf.showPage()
    pdf.save()

    reader = PdfReader(str(raw_path))
    writer = PdfWriter()
    for source_page in reader.pages:
        writer.add_page(source_page)
    for title, page in [
        ("I. Company overview", 4),
        ("II. Business", 8),
        ("III. Finance", 15),
        ("IV. Management discussion", 30),
        ("V. Audit", 35),
        ("VI. Governance", 38),
        ("VII. Shareholders", 39),
        ("VIII. Employees", 40),
        ("IX. Affiliates", 45),
        ("X. Transactions", 47),
        ("XI. Other", 48),
        ("XII. Tables", 55),
    ]:
        writer.add_outline_item(title, page - 1)
    with path.open("wb") as output:
        writer.write(output)
    raw_path.unlink()


def test_preprocess_creates_three_pdfs_with_cover(tmp_path):
    source = tmp_path / "source.pdf"
    make_pdf(source)
    manifest = preprocess_report(source, tmp_path / "batches")
    assert manifest["detection"]["method"] == "pdf_outline"
    for batch_id in (
        "01_business_strategy",
        "02_finance_management",
        "03_workforce_esg",
    ):
        output = Path(manifest["batches"][batch_id]["output_pdf"])
        assert output.is_file()
        expected = len(manifest["detection"]["batches"][batch_id]) + 1
        assert len(PdfReader(str(output)).pages) == expected
        assert manifest["batches"][batch_id]["prepared_page_count"] == expected


def test_preprocess_preserves_uploaded_source_name(tmp_path):
    source = tmp_path / "temporary-upload.pdf"
    make_pdf(source)
    manifest = preprocess_report(
        source,
        tmp_path / "batches",
        source_document_name="original-business-report.pdf",
    )
    assert manifest["source_document"] == "original-business-report.pdf"


def test_detector_uses_sections_not_company_page_constants(tmp_path):
    source = tmp_path / "source.pdf"
    make_pdf(source)
    detected = detect_report_sections(str(source))
    assert detected["batches"]["01_business_strategy"] == list(range(4, 15))
    assert detected["batches"]["02_finance_management"] == list(range(15, 38))
    assert set(range(40, 45)).issubset(detected["batches"]["03_workforce_esg"])
