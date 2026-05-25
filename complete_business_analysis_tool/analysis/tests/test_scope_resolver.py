from complete_business_analysis_tool.analysis.scope import resolve_scope


def test_overall_text_only_returns_all_categories():
    all_ids = {"cat1", "cat2", "cat3"}
    result = resolve_scope(
        overall_text="Needs improvement overall",
        category_feedback_ids=set(),
        all_category_ids=all_ids,
    )
    assert result == all_ids


def test_category_feedback_only_returns_those_categories():
    all_ids = {"cat1", "cat2", "cat3"}
    result = resolve_scope(
        overall_text=None,
        category_feedback_ids={"cat1", "cat3"},
        all_category_ids=all_ids,
    )
    assert result == {"cat1", "cat3"}


def test_both_overall_and_category_returns_all_categories():
    all_ids = {"cat1", "cat2", "cat3"}
    result = resolve_scope(
        overall_text="Overall concern",
        category_feedback_ids={"cat2"},
        all_category_ids=all_ids,
    )
    assert result == all_ids
