from typing import List, Dict
from dotenv import load_dotenv
from groq import Groq
import os

load_dotenv()

_llm = Groq()
_MODEL_NAME = "llama-3.1-8b-instant"

MAX_CONTEXT_CHARS = 12000


SYSTEM_PROMPT = """
You are an AI assistant working as an information extraction system for an Indian government agricultural schemes information system.

CRITICAL RULES:
- Use ONLY exact statements found in the provided context.
- Do NOT infer, assume, generalize, or add conditions.
- Do NOT use prior knowledge.
- Do NOT decide eligibility for the user.
- Do NOT compare schemes.
- If an exclusion is not explicitly written, DO NOT include it.
- NEVER repeat or reword items.
- NEVER add examples.
- NEVER invent farmer conditions.

OUTPUT RULES FOR EXCLUSIONS:
- Extract ONLY sentences that explicitly say:
  "shall not", "not eligible", "not covered", "no claim shall", "shall be excluded".
- If no such sentence exists, say:
  "This information is not mentioned in the official guidelines."

If you violate any rule, the answer is invalid.
"""

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _prepare_chunks_for_generation(chunks: List[Dict]) -> List[Dict]:
    seen = set()
    ordered = []

    for r in chunks:
        uid = (
            r["metadata"].get("parent_id"),
            r["metadata"].get("chunk_index"),
        )
        if uid in seen:
            continue
        seen.add(uid)
        ordered.append(r)

    return ordered


def _filter_chunks_by_intent(chunks: List[Dict], intent: str | None) -> List[Dict]:
    """
    SOFT intent filter.
    - Keeps summaries always
    - For exclusions, keep ANY chunk with exclusion language
      even if section header sounds like eligibility
    """
    if not intent:
        return chunks

    intent_keywords = {
        "exclusions": [
            "shall not",
            "not eligible",
            "not covered",
            "shall not be considered",
            "no claim shall",
            "shall be excluded",
            "not admissible",
            "not payable",
        ],
        "eligibility": ["eligibility", "eligible", "coverage"],
        "documents": ["document", "aadhaar", "kcc", "certificate", "proof"],
        "benefits": ["benefit", "sum insured", "assistance"],
        "claim": ["claim", "loss", "compensation", "settlement"],
        "overview": ["objective", "scheme", "introduction"],
    }

    keywords = intent_keywords.get(intent)
    if not keywords:
        return chunks

    kept = []

    for c in chunks:
        meta = c["metadata"]

        # summaries are always allowed
        if meta.get("source_type") == "summary":
            kept.append(c)
            continue

        blob = " ".join(
            filter(None, [
                meta.get("primary_section", ""),
                str(meta.get("section_context", "")),
                c["text"],
            ])
        ).lower()

        if any(k in blob for k in keywords):
            kept.append(c)

    return kept if kept else chunks


def _filter_farmer_only_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    FINAL hard guard for exclusions:
    - Keep ONLY chunks that explicitly exclude farmers / coverage
    - Do NOT rely on section headers
    """
    exclusion_triggers = [
        "shall not",
        "not eligible",
        "not covered",
        "shall not be considered",
        "no claim shall",
        "shall be excluded",
        "not admissible",
        "not payable",
    ]

    filtered = []

    for c in chunks:
        blob = " ".join([
            c["text"],
            c["metadata"].get("primary_section", ""),
        ]).lower()

        if any(e in blob for e in exclusion_triggers):
            filtered.append(c)

    return filtered


def dedupe_chunks(chunks: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []

    for c in chunks:
        text = c["text"].strip()
        if text and text not in seen:
            seen.add(text)
            unique.append(c)

    return unique


def _format_context(chunks: List[Dict]) -> str:
    grouped = {}
    total_chars = 0
    blocks = []

    for r in chunks:
        meta = r["metadata"]
        scheme = meta.get("scheme_code", "UNKNOWN")
        doc_type = meta.get("document_type", "unknown")

        grouped.setdefault(scheme, {"summary": [], "pdf": []})
        grouped[scheme][doc_type].append(r["text"].strip())

    for scheme, docs in grouped.items():
        parts = [f"SCHEME: {scheme}"]

        if docs["summary"]:
            parts.append("SOURCE: SUMMARY")
            parts.append("\n\n".join(docs["summary"]))

        if docs["pdf"]:
            parts.append("SOURCE: OFFICIAL GUIDELINES")
            parts.append("\n\n".join(docs["pdf"]))

        block = "\n\n".join(parts)

        if total_chars + len(block) > MAX_CONTEXT_CHARS:
            break

        blocks.append(block)
        total_chars += len(block)

    return "\n\n---\n\n".join(blocks)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def generate_answer(
    query: str,
    retrieved_chunks: List[Dict],
    intent: str | None = None,
) -> str:

    if not retrieved_chunks:
        return "This information is not mentioned in the official guidelines."

    retrieved_chunks = _prepare_chunks_for_generation(retrieved_chunks)

    # ✅ FIRST: intent narrowing (soft)
    retrieved_chunks = _filter_chunks_by_intent(retrieved_chunks, intent)

    # ✅ SECOND: hard exclusion guard
    if intent == "exclusions":
        retrieved_chunks = _filter_farmer_only_chunks(retrieved_chunks)

    retrieved_chunks = dedupe_chunks(retrieved_chunks)

    if not retrieved_chunks:
        return "This information is not mentioned in the official guidelines."

    context = _format_context(retrieved_chunks)

    task_line = (
        "Extract exact exclusion conditions."
        if intent == "exclusions"
        else "Extract exact information strictly answering the question."
    )

    instruction_block = (
        """
- Copy ONLY exact exclusion statements from the context.
- Do NOT paraphrase.
- Do NOT infer.
- Do NOT list anything not explicitly written.
"""
        if intent == "exclusions"
        else
        """
- Use ONLY statements explicitly present in the context.
- Do NOT infer or add information.
"""
    )

    user_prompt = f"""
TASK:
{task_line}

CONTEXT:
{context}

INTENT:
{intent}

INSTRUCTIONS:
{instruction_block}

QUESTION:
{query}

ANSWER:
"""

    response = _llm.chat.completions.create(
        model=_MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    return response.choices[0].message.content.strip()
