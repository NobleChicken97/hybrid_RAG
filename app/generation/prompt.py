"""
Prompt templates for RAG-grounded generation with citation instructions.

The system prompt enforces:
  - Answer ONLY from provided context
  - Use inline citation markers [1], [2], etc.
  - Say "I don't have enough information" when context is insufficient
"""


SYSTEM_PROMPT = """You are a helpful research assistant. Your task is to answer questions based ONLY on the provided context passages.

RULES:
1. Answer ONLY based on the information in the context passages below. Do NOT use any prior knowledge.
2. If the context does not contain enough information to answer the question, say: "I don't have enough information in the provided documents to answer this question."
3. Include inline citation markers like [1], [2], etc. to reference the specific context passage(s) you used. Every factual claim must have at least one citation.
4. Be concise and direct. Do not repeat the question.
5. If multiple passages contain relevant information, synthesize them and cite all relevant sources.
"""


def build_prompt(
    question: str,
    context_chunks: list[tuple[str, str, str]],  # [(chunk_id, text, doc_title)]
) -> str:
    """
    Build the full prompt with numbered context passages and the question.

    Args:
        question: The user's question.
        context_chunks: List of (chunk_id, compressed_text, doc_title) tuples.

    Returns:
        The assembled prompt string.
    """
    # Build numbered context block
    context_lines = []
    for i, (chunk_id, text, doc_title) in enumerate(context_chunks, 1):
        context_lines.append(f"[{i}] (Source: {doc_title})\n{text}")

    context_block = "\n\n".join(context_lines)

    prompt = f"""CONTEXT PASSAGES:
{context_block}

QUESTION: {question}

Please answer the question using ONLY the context passages above. Include citation markers [1], [2], etc. for every factual claim."""

    return prompt


def build_prompt_with_metadata(
    question: str,
    context_chunks: list[tuple[str, str, str]],
    metadata: dict | None = None,
) -> tuple[str, str]:
    """
    Build both the system prompt and user prompt.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    user_prompt = build_prompt(question, context_chunks)
    return SYSTEM_PROMPT, user_prompt
