from pathlib import Path

from reportlab.pdfgen import canvas

from evidence_validator import reconcile_evidence_pages


def make_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path))
    for page in range(1, 6):
        text = "ordinary page"
        if page == 4:
            text = "Revenue 2025 123 million won"
        pdf.drawString(72, 720, text)
        pdf.showPage()
    pdf.save()


def test_reconcile_evidence_corrects_high_confidence_page(tmp_path):
    source = tmp_path / "source.pdf"
    make_pdf(source)
    result = {
        "evidence_refs": [
            "E001 | original_page=2 | section=Finance | "
            "quote=Revenue 2025 123 million won"
        ],
        "limitations": ["ORIGINAL_PDF_PAGE 2에서 확인"],
    }
    revised, corrections = reconcile_evidence_pages(
        result, source, [1, 2, 3, 4, 5]
    )
    assert "original_page=4" in revised["evidence_refs"][0]
    assert "ORIGINAL_PDF_PAGE 4" in revised["limitations"][0]
    assert corrections[0]["to_page"] == 4
