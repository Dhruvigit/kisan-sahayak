import re
from typing import List, Dict

# ---------- STRICT TOP-LEVEL HEADER REGEX ----------

TOP_LEVEL_HEADER_REGEX = re.compile(
    r"""
    ^\s*
    (
        (\d+(\.0)?)
        |
        \d+(\.\d+)*
        |
        ([A-Z])
        |
        ([IVXLCDM]+)
    )
    [\.\)\:]?
    \s+
    .+
    [A-Za-z].*
    $
    """,
    re.VERBOSE
)

SUBSECTION_REGEX = re.compile(
    r"""
    \d+\.\d+          |   # 3.1
    \d+\.\d+\.\d+     |   # 3.1.1
    [A-Z]\.\d+            # A.1
    """,
    re.VERBOSE)

SUBSECTION_REGEX = re.compile(r"\d+\.\d+")

PDF_STOPWORDS = {
    "that", "which", "while", "where", "therefore", "thereof",
    "including", "such", "shall", "being", "advised"
}

def looks_like_sentence(line: str) -> bool:
    words = line.lower().split()
    return any(w in PDF_STOPWORDS for w in words)

PDF_VERBS = {
    "provide", "collection", "procedure", "assessment", "payment",
    "transfer", "implementation", "monitoring", "review",
    "settlement", "dispute", "evaluation", "appointment"
}

PDF_BAD_SECOND_WORDS = {"of", "for", "to", "regarding"}


# ---------- CORE LOGIC ----------

def is_top_level_header(
    line: str,
    *,
    source_type: str,
    raw_line: str
) -> bool:
    """
    source_type: 'pdf' or 'summary'
    raw_line   : original line BEFORE cleaning ** markers
    """
    line = line.strip()

    if not line:
        return False
    
    # Reject numbered sentences (end with full stop AND long)
    if line.endswith(".") and len(line.split()) > 6:
        return False

    # Reject tables
    if line.startswith("|") and line.endswith("|"):
        return False

    # Reject subsections like 3.1, 4.2.1
    if SUBSECTION_REGEX.search(line):
        return False

    # Must match top-level numbering
    if not TOP_LEVEL_HEADER_REGEX.match(line):
        return False
    
    # reject sentence-like headers
    if line.endswith(":") is False and line.count(" ") > 7:
        return False

    # Word length guard
    if len(line.split()) > 10:
        return False
    
     # ---------- SOURCE-SPECIFIC RULES ----------

    if source_type == "pdf":
        # STRICT: must be bold in original PDF text
        if "**" not in raw_line:
            return False
        
        words = line.lower().split()

        # Hard length cap for PDF headers
        if len(words) > 10:
            return False

        # Reject sentence-like constructions
        if looks_like_sentence(line):
            return False
        
        # Reject verb-like headers
        if any(w in PDF_VERBS for w in words):
            return False

        # Reject "X of Y" / "X for Y" patterns
        if len(words) > 1 and words[1] in PDF_BAD_SECOND_WORDS:
            return False

    # summary: numbering alone is enough
    return True

def is_pdf_header(line: str) -> bool:
    # PDF: MUST be numbered AND bold in original text
    if "**" not in line:
        return False
    return is_top_level_header(line.replace("**", ""))


def is_summary_header(line: str) -> bool:
    # Summary: numbering start is enough, bold not required
    return is_top_level_header(line)

def extract_sections_from_chunk(
    chunk: str,
    *,
    source_type: str
) -> List[str]:
    """
    Extract valid top-level headers from a chunk.
    """
    sections = []

    for raw_line in chunk.splitlines():
        clean = raw_line.replace("**", "").strip()

        if is_top_level_header(
            clean,
            source_type=source_type,
            raw_line=raw_line
        ):
            sections.append(clean)

    return sections
