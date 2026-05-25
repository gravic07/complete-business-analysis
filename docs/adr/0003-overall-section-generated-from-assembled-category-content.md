# Overall section is generated from assembled category section content

The Overall ReportSection is generated after all category sections are written, using the full assembled current state of the Report as its primary input — not the raw Q&A answers. It reads the latest ReportSection per category across all Analysis runs (the same DISTINCT ON query used by `_assemble_report()`), synthesizing what the category sections actually concluded rather than re-deriving conclusions from the same raw data independently.

This decision resolves the coherence problem: when the Overall is generated from raw Q&A (same inputs as category sections), the LLM may reach different conclusions, producing contradictions between the Overall and the category sections. By reading the category section text directly, the Overall is structurally incapable of contradicting what the categories said — it can only synthesize it.

The Overall section has a distinct mandate from category sections: (1) briefly acknowledge the overall picture, (2) identify execution sequencing (which category plans can run simultaneously, which depend on others), (3) call out low-hanging fruit (high-impact, easy-to-implement actions), (4) name the most urgent items to address. Category scores are passed as silent context to inform urgency ranking but the prompt instructs the model never to cite raw numeric scores in output.

The Overall section regenerates any time any category section changes — not only when `overall_feedback` is present. When targeted feedback triggers regeneration of a single category, the Overall is re-run against the full assembled Report so its synthesis reflects the updated state.

## Considered Options

- **Overall generated from raw Q&A (prior approach)** — rejected: same inputs as category sections, LLM may reach different conclusions, producing contradictions with no structural guarantee of consistency
- **Separate coherence review pass that patches all sections** — rejected: expensive, risks silently regressing sections that were already correct, and cross-category contradictions (Sales vs. People) are rare in practice; category-to-Overall contradictions are the real problem
- **Sequential chained generation (PHP approach)** — rejected: natural coherence via shared conversation context, but prevents individual section regeneration; the feedback cycle depends on being able to regenerate a single category without touching others
