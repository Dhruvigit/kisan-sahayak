from pathlib import Path
from docx import Document
from pymupdf4llm import to_markdown


def ingest_docx(docx_path: Path) -> str:
    """
    Extract clean text from DOCX summary files.
    """
    doc = Document(docx_path)
    paragraphs = []

    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text.strip())

    if not paragraphs:
        raise ValueError(f"DOCX extraction failed: {docx_path.name}")

    return "\n\n".join(paragraphs)


def ingest_pdf(pdf_path: Path) -> str:
    """
    Extract text from born-digital government PDFs.
    - Preserves headings
    - Linearizes tables as text
    - Ignores images & diagrams
    """
    text = to_markdown(
        pdf_path,
        page_chunks=False,
        write_images=False
    )

    if not text or len(text.strip()) < 300:
        raise ValueError(f"PDF text extraction failed: {pdf_path.name}")

    return text.strip()
