from django.conf import settings
from django.urls import reverse
from playwright.sync_api import sync_playwright

from complete_business_analysis_tool.assessments.models import Assessment


def generate_pdf(assessment_pk: str, token: str) -> bytes:
    """Launch Playwright, render the PDF template, return raw PDF bytes."""

    url = _build_url(assessment_pk, token)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            page.wait_for_selector("svg", timeout=15_000)
            pdf_bytes = page.pdf(
                width="8.5in",
                height="11in",
                print_background=True,
                header_template=_header_template(assessment_pk),
                footer_template=_footer_template(),
                display_header_footer=True,
            )
        finally:
            browser.close()

    return pdf_bytes


def _build_url(assessment_pk: str, token: str) -> str:

    path = reverse("reports:pdf", kwargs={"pk": assessment_pk})
    base = getattr(settings, "PDF_BASE_URL", "http://localhost:8000")
    return f"{base}{path}?token={token}"


def _header_template(assessment_pk: str) -> str:

    try:
        assessment = Assessment.objects.get(pk=assessment_pk)
        name = assessment.name.upper()
        client = assessment.client.business_name
    except Exception:  # noqa: BLE001
        name = ""
        client = ""

    return (
        '<div style="width:100%;background:#0a1628;color:#fff;'
        "font-size:9px;padding:8px 0.75in;box-sizing:border-box;"
        'display:flex;justify-content:space-between;align-items:center;">'
        f"<span>{name}</span><span>{client}</span></div>"
    )


def _footer_template() -> str:
    return (
        '<div style="width:100%;background:#0a1628;color:#fff;'
        "font-size:9px;padding:8px 0.75in;box-sizing:border-box;"
        'display:flex;justify-content:space-between;align-items:center;">'
        '<span class="pageNumber"></span>'
        "<span>COMPLETE BUSINESS REPORT</span></div>"
    )
