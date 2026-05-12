from retrieval.keyword_search import SearchResult, WikiPage


ASK_SYSTEM_PROMPT = """You are a technician wiki assistant.

Answer the user's question using only the provided wiki context.
Cite the relevant page titles or page IDs.
If the context is insufficient, say so clearly.
Do not invent procedures.
"""


DEBUG_SYSTEM_PROMPT = """You are a technician debug router.

Choose the single best page_id from the candidate wiki pages.

Return ONLY the page_id.
Do not return a URL.
Do not explain.
Do not include markdown.
Do not include extra text.
"""


def build_ask_prompt(query: str, pages: list[WikiPage]) -> str:
    context_blocks = []
    for page in pages:
        context_blocks.append(
            "\n".join(
                [
                    f"TITLE: {page.title}",
                    f"PAGE_ID: {page.page_id}",
                    f"URL: {page.url}",
                    "CONTENT:",
                    page.body,
                ]
            )
        )

    context = "\n\n---\n\n".join(context_blocks) or "NO_MATCHING_CONTEXT"

    return "\n".join(
        [
            ASK_SYSTEM_PROMPT.strip(),
            "",
            "WIKI CONTEXT:",
            context,
            "",
            "USER QUESTION:",
            query,
            "",
            "ANSWER:",
        ]
    )


def build_debug_prompt(query: str, candidates: list[SearchResult]) -> str:
    rendered_candidates = []
    for candidate in candidates:
        rendered_candidates.append(
            "\n".join(
                [
                    f"- page_id: {candidate.page_id}",
                    f"  title: {candidate.title}",
                    f"  snippet: {candidate.snippet}",
                ]
            )
        )

    return "\n".join(
        [
            DEBUG_SYSTEM_PROMPT.strip(),
            "",
            "CANDIDATE WIKI PAGES:",
            "\n".join(rendered_candidates),
            "",
            "USER QUERY:",
            query,
        ]
    )

