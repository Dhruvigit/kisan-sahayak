from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---- Consolidation defaults (PDF) ----
PDF_MIN_CHARS = 900
PDF_MAX_CHARS = 3000


def _consolidate_chunks(
    chunks: list[str],
    min_chars: int,
    max_chars: int,
) -> list[str]:
    """
    Merge small chunks with neighbors until minimum size is reached,
    while preventing overly large chunks.
    """
    consolidated = []
    buffer = ""

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if len(buffer) + len(chunk) < min_chars:
            buffer += "\n\n" + chunk
        else:
            if buffer.strip():
                consolidated.append(buffer.strip())
            buffer = chunk

        # prevent runaway large chunks
        if len(buffer) > max_chars:
            consolidated.append(buffer.strip())
            buffer = ""

    if buffer.strip():
        consolidated.append(buffer.strip())

    return consolidated


def chunk_text(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    *,
    consolidate: bool = False,
) -> list[str]:
    """
    Split text into chunks.
    Optionally consolidates small chunks (used for PDFs).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    raw_chunks = splitter.split_text(text)

    if not consolidate:
        return raw_chunks

    return _consolidate_chunks(
        raw_chunks,
        min_chars=PDF_MIN_CHARS,
        max_chars=PDF_MAX_CHARS,
    )