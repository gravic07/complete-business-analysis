def resolve_scope(
    overall_text: str | None,
    category_feedback_ids: set[str],
    all_category_ids: set[str],
) -> set[str]:
    """Return the set of category IDs to reprocess for a re-analysis run.

    Rule: if overall_text is present → all categories; otherwise → only the
    categories that received specific feedback.
    """
    if overall_text:
        return set(all_category_ids)
    return set(category_feedback_ids)
