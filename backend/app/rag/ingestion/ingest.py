from pathlib import Path
from typing import List, Dict

from backend.app.rag.ingestion.extractors import ingest_pdf, ingest_docx
from backend.app.rag.ingestion.chunking import chunk_text
from backend.app.rag.ingestion.headers import extract_sections_from_chunk
from backend.app.rag.ingestion.metadata import build_chunk_metadata
from backend.app.rag.scheme_metadata import SCHEME_METADATA


PDF_CHUNK_SIZE = 800
PDF_CHUNK_OVERLAP = 150

DOCX_CHUNK_SIZE = 500
DOCX_CHUNK_OVERLAP = 80


# ---------- helpers ----------

def is_index_chunk(chunk: str) -> bool:
    """Skip PMFBY INDEX table chunks"""
    text = chunk.upper()
    return "INDEX" in text and "|" in text


def is_boilerplate_chunk(chunk: str, current_section: str | None) -> bool:
    """Drop signatures / addresses / slogans"""
    if current_section is not None:
        return False
    return len(chunk.strip()) < 300


def is_footer_section(section: str) -> bool:
    """Prevent footers / references from becoming sections"""
    bad_keywords = [
        "MASTER CIRCULAR",
        "CIRCULAR",
        "DIRECTION",
        "NORMS",
        "DBR",
    ]
    s = section.upper()
    return any(k in s for k in bad_keywords) or len(section) > 120


# ---------- main ----------

def ingest_documents(pdf_dir: Path, docx_dir: Path) -> List[Dict]:
    chunk_records: List[Dict] = []

    def process(chunks, scheme, doc_type, source):
        records = []
        current_section = None

        for idx, chunk in enumerate(chunks):
            # ---- skip junk chunks early ----
            if is_index_chunk(chunk):
                continue

            if is_boilerplate_chunk(chunk, current_section):
                continue

            # ---- extract headers inside chunk ----
            sections = extract_sections_from_chunk(chunk, source_type=doc_type)
            sections = [s for s in sections if not is_footer_section(s)]

            previous_section = current_section  # 👈 snapshot BEFORE update

            # ---- update sticky section ----
            if sections:
                current_section = sections[-1]

            primary_section = sections[0] if sections else current_section

            section_context = list(
                dict.fromkeys(
                    ([previous_section] if previous_section else []) + sections
                )
            )

            records.append({
                "text": chunk,
                "metadata": build_chunk_metadata(
                    scheme_id=scheme["scheme_id"],
                    scheme_code=scheme["scheme_code"],
                    scheme_name=scheme["scheme_name"],
                    document_type=doc_type,
                    content_level="official" if doc_type == "pdf" else "derived",
                    source_document=source,
                ) | {
                    "source_type": doc_type,
                    "chunk_index": idx,
                    "parent_id": f"{scheme['scheme_code']}::{source}",
                    "primary_section": primary_section,
                    "previous_section": previous_section,
                    "sections_found": sections,
                    "section_context": section_context,
                }
            })

        return records

    # ---------- PDFs ----------
    for pdf in pdf_dir.glob("*.pdf"):
        scheme = SCHEME_METADATA[pdf.name]
        text = ingest_pdf(pdf)

        chunks = chunk_text(
            text,
            chunk_size=PDF_CHUNK_SIZE,
            chunk_overlap=PDF_CHUNK_OVERLAP,
            consolidate=True,
        )

        chunk_records.extend(process(chunks, scheme, "pdf", pdf.name))

    # ---------- DOCX summaries ----------
    for docx in docx_dir.glob("*.docx"):
        scheme = SCHEME_METADATA[docx.name]
        text = ingest_docx(docx)

        chunks = chunk_text(
            text,
            chunk_size=DOCX_CHUNK_SIZE,
            chunk_overlap=DOCX_CHUNK_OVERLAP,
            consolidate=False,
        )

        chunk_records.extend(process(chunks, scheme, "summary", docx.name))

    return chunk_records
