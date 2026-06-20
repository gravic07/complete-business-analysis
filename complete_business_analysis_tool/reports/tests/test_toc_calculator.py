# ruff: noqa: PLR2004

from complete_business_analysis_tool.reports.utils.toc_calculator import (
    calculate_toc_page_numbers,
)


def test_cba_score_is_page_3():
    pages = calculate_toc_page_numbers(["Ops"], "Acme")
    assert pages["CBA Score"] == 3


def test_n1_all_keys_present():
    pages = calculate_toc_page_numbers(["Ops"], "Acme")
    expected_keys = {
        "CBA Score",
        "Visualizations",
        "Analysis for Acme",
        "analysis:Ops",
        "Recommendations",
        "recommendations:Ops",
        "12-Month Roadmap",
        *(f"Month {m}" for m in range(1, 13)),
        "Potential Challenges",
        "Post-Implementation Outcomes",
        "Closing Reflections",
    }
    assert set(pages.keys()) == expected_keys


def test_n1_all_page_numbers_correct():
    pages = calculate_toc_page_numbers(["Ops"], "Acme")
    # N equals 1
    assert pages["CBA Score"] == 3
    assert pages["Visualizations"] == 4
    assert pages["Analysis for Acme"] == 5
    assert pages["analysis:Ops"] == 6
    assert pages["Recommendations"] == 7  # 6+N = 6+1
    assert pages["recommendations:Ops"] == 8  # 7+N = 7+1
    assert pages["12-Month Roadmap"] == 9  # 7+2N = 7+2
    assert pages["Month 1"] == 10  # 8+2N
    assert pages["Month 12"] == 21  # 19+2N
    assert pages["Potential Challenges"] == 22  # 20+2N
    assert pages["Post-Implementation Outcomes"] == 23
    assert pages["Closing Reflections"] == 24  # 22+2N


CATEGORIES_7 = [
    "Strategic Planning",
    "Performance",
    "People",
    "Processes",
    "Sales and Marketing",
    "Personal Development",
    "Technology and Software",
]


def test_n7_all_keys_present():
    pages = calculate_toc_page_numbers(CATEGORIES_7, "Testing 2")
    expected_keys = {
        "CBA Score",
        "Visualizations",
        "Analysis for Testing 2",
        *(f"analysis:{cat}" for cat in CATEGORIES_7),
        "Recommendations",
        *(f"recommendations:{cat}" for cat in CATEGORIES_7),
        "12-Month Roadmap",
        *(f"Month {m}" for m in range(1, 13)),
        "Potential Challenges",
        "Post-Implementation Outcomes",
        "Closing Reflections",
    }
    assert set(pages.keys()) == expected_keys


def test_n7_page_numbers_correct():
    pages = calculate_toc_page_numbers(CATEGORIES_7, "Testing 2")
    # N equals 7
    assert pages["CBA Score"] == 3
    assert pages["Visualizations"] == 4
    assert pages["Analysis for Testing 2"] == 5
    assert pages["analysis:Strategic Planning"] == 6
    assert pages["analysis:Technology and Software"] == 12  # 5+N
    assert pages["Recommendations"] == 13  # 6+N
    assert pages["recommendations:Strategic Planning"] == 14  # 7+N
    assert pages["recommendations:Technology and Software"] == 20  # 6+2N
    assert pages["12-Month Roadmap"] == 21  # 7+2N
    assert pages["Month 1"] == 22  # 8+2N
    assert pages["Month 12"] == 33  # 19+2N
    assert pages["Potential Challenges"] == 34  # 20+2N
    assert pages["Post-Implementation Outcomes"] == 35
    assert pages["Closing Reflections"] == 36  # 22+2N


def test_n5_spot_check():
    cats = ["A", "B", "C", "D", "E"]
    pages = calculate_toc_page_numbers(cats, "Corp")
    # N equals 5
    assert pages["analysis:E"] == 10  # 5+N = 10
    assert pages["Recommendations"] == 11  # 6+N
    assert pages["recommendations:A"] == 12  # 7+N
    assert pages["recommendations:E"] == 16  # 6+2N
    assert pages["12-Month Roadmap"] == 17  # 7+2N
    assert pages["Month 1"] == 18  # 8+2N
    assert pages["Month 12"] == 29  # 19+2N
    assert pages["Potential Challenges"] == 30  # 20+2N
    assert pages["Closing Reflections"] == 32  # 22+2N
