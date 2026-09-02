"""
Citation extraction and formatting.

Maps inline citation markers [1], [2] from the LLM response back to
actual source chunks, producing structured Citation objects.
"""

import re

from app.models import Citation


def build_citation_map(
    context_chunks: list[tuple[str, str, str, str | None]],
    # [(chunk_id, text, doc_title, source_path)]
) -> dict[int, Citation]:
    """
    Build a mapping from citation number to Citation object.

    The numbers correspond to the [1], [2], etc. markers in the prompt.

    Args:
        context_chunks: Ordered list of (chunk_id, text, doc_title, source_path).

    Returns:
        Dict mapping citation number to Citation object.
    """
    citation_map = {}
    for i, (chunk_id, text, doc_title, source_path) in enumerate(context_chunks, 1):
        # Snippet: first 200 chars of the chunk text
        snippet = text[:200].strip()
        if len(text) > 200:
            snippet += "..."

        citation_map[i] = Citation(
            chunk_id=chunk_id,
            doc_title=doc_title,
            snippet=snippet,
            source_path=source_path,
        )
    return citation_map


def extract_cited_numbers(answer: str) -> list[int]:
    """
    Extract citation numbers referenced in the LLM answer.

    Looks for patterns like [1], [2], [3,4], [1-3], etc.
    """
    # Match [N] patterns
    single_refs = re.findall(r"\[(\d+)\]", answer)

    # Match [N,M] patterns
    multi_refs = re.findall(r"\[(\d+(?:,\s*\d+)+)\]", answer)

    numbers = set()

    for ref in single_refs:
        numbers.add(int(ref))

    for ref in multi_refs:
        for num in re.findall(r"\d+", ref):
            numbers.add(int(num))

    return sorted(numbers)


def get_citations_for_answer(
    answer: str,
    citation_map: dict[int, Citation],
) -> list[Citation]:
    """
    Get the Citation objects referenced in an LLM answer.

    Args:
        answer: The LLM-generated answer text.
        citation_map: The full citation map from build_citation_map().

    Returns:
        List of Citation objects that were actually referenced in the answer.
        If none were referenced, returns all citations (the model may have
        used the context without explicit markers).
    """
    referenced_numbers = extract_cited_numbers(answer)

    if referenced_numbers:
        citations = [
            citation_map[n]
            for n in referenced_numbers
            if n in citation_map
        ]
    else:
        # If no explicit citations, return all context citations
        citations = list(citation_map.values())

    return citations
