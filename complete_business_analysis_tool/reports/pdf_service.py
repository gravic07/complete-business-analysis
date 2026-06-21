from io import BytesIO

from django.conf import settings
from django.urls import reverse
from django.utils.html import escape
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

# Shared inline style for the header and footer dark bands.
# width:100% spans the full paper width inside Playwright's template area.
# padding matches the body side margins so text aligns with page content.
_BAND_STYLE = (
    "width:100%;height:0.3in;"
    "background-color:#0a1628;color:#ffffff;"
    "font-size:10px;font-family:Arial,sans-serif;letter-spacing:0.04em;"
    "display:flex;justify-content:space-between;align-items:center;"
    "padding:0 0.75in;box-sizing:border-box;margin:0;"
    "-webkit-print-color-adjust:exact;print-color-adjust:exact;"
)


def generate_pdf(
    assessment_pk: str,
    token: str,
    header_left: str = "",
    header_right: str = "",
) -> bytes:
    """Launch Playwright, render the PDF template, return raw PDF bytes."""

    url = _build_url(assessment_pk, token)

    header_template = (
        f'<div style="{_BAND_STYLE}">'
        f"<span>{escape(header_left)}</span>"
        f"<span>{escape(header_right)}</span>"
        f"</div>"
    )
    footer_template = (
        f'<div style="{_BAND_STYLE}">'
        f'<span>PAGE <span class="pageNumber"></span></span>'
        f"<span>COMPLETE BUSINESS REPORT</span>"
        f"</div>"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            page.wait_for_selector("svg", timeout=15_000)

            # Pass 1: full document with header/footer on every page.
            # Page numbers will be correct throughout (1, 2, 3 …) and we
            # discard page 1 of this PDF in the merge step below.
            full_pdf_bytes = page.pdf(
                width="8.5in",
                height="11in",
                print_background=True,
                display_header_footer=True,
                header_template=header_template,
                footer_template=footer_template,
                margin={
                    "top": "0.75in",
                    "bottom": "0.75in",
                    "left": "0.75in",
                    "right": "0.75in",
                },
            )

            # Pass 2: cover page only, full-bleed, no header/footer.
            # Hide every non-cover section so only one page renders.
            page.evaluate(
                "document.querySelectorAll('.page-break').forEach(el => "
                "el.style.display = 'none')",
            )
            cover_pdf_bytes = page.pdf(
                width="8.5in",
                height="11in",
                print_background=True,
                display_header_footer=False,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
        finally:
            browser.close()

    # Merge: cover (full-bleed, no header/footer) + pages 2+ from full PDF.
    full_reader = PdfReader(BytesIO(full_pdf_bytes))
    cover_reader = PdfReader(BytesIO(cover_pdf_bytes))
    writer = PdfWriter()
    writer.add_page(cover_reader.pages[0])
    for i in range(1, len(full_reader.pages)):
        writer.add_page(full_reader.pages[i])
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def _build_url(assessment_pk: str, token: str) -> str:
    path = reverse("reports:pdf", kwargs={"pk": assessment_pk})
    base = getattr(settings, "PDF_BASE_URL", "http://localhost:8000")
    return f"{base}{path}?token={token}"
