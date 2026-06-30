def build_chunk_metadata(
    scheme_id: str,
    scheme_code: str,
    scheme_name: str,
    document_type: str,
    content_level: str,
    source_document: str,
    section: str = "other",
    subsection: str | None = None,
    page_range: str | None = None,
):
    return {
        "scheme_id": scheme_id,
        "scheme_code": scheme_code,
        "scheme_name": scheme_name,
        "document_type": document_type,     # pdf | summary
        "content_level": content_level,     # official | derived
        "source_document": source_document,
        "section": section,
        "subsection": subsection,
        "page_range": page_range,
    }
