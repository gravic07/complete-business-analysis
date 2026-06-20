def calculate_toc_page_numbers(categories: list[str], name: str) -> dict[str, int]:
    n = len(categories)
    pages: dict[str, int] = {}

    pages["CBA Score"] = 3
    pages["Visualizations"] = 4
    pages[f"Analysis for {name}"] = 5

    for i, cat in enumerate(categories):
        pages[f"analysis:{cat}"] = 6 + i

    pages["Recommendations"] = 6 + n

    for i, cat in enumerate(categories):
        pages[f"recommendations:{cat}"] = 7 + n + i

    pages["12-Month Roadmap"] = 7 + 2 * n

    for month in range(1, 13):
        pages[f"Month {month}"] = 7 + 2 * n + month

    pages["Potential Challenges"] = 20 + 2 * n
    pages["Post-Implementation Outcomes"] = 21 + 2 * n
    pages["Closing Reflections"] = 22 + 2 * n

    return pages
