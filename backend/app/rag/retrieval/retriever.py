from typing import List, Dict, Optional, Set
import re
from langchain_chroma import Chroma
from backend.app.rag.vectorization.vectorstore import (
    get_embedding_model,
    VECTOR_DB_DIR,
    COLLECTION_NAME,
)


DEFAULT_TOP_K = 8


# -------------------------------
# Section keyword map
# -------------------------------
SECTION_KEYWORDS = {

    # -------------------------------------------------
    # ELIGIBILITY / COVERAGE / EXCLUSIONS
    # -------------------------------------------------
    "eligibility": [
        "eligibility",
        "coverage of farmers",
        "coverage",
        "who can apply",
        "who can receive",
        "a farmer family is eligible",
        "definition of farmer",
        "definitions",
        "compulsory component",
        "voluntary component",
        "insured farmer",
        "farmer family",
        "coverage of crops",
    ],

    "exclusion": [
        "exclusion",
        "exclusions",
        "not eligible",
        "who cannot join",
        "cannot join",
        "opt out",
        "opt-out",
        "risk not covered",
        "coverage of risks and exclusions",
        "exclusions (not eligible)",
    ],

    # -------------------------------------------------
    # DOCUMENTS / APPLICATION / ENROLLMENT
    # -------------------------------------------------
    "documents": [
        "documents required",
        "documents",
        "documentary evidence",
        "list of documents",
        "proofs",
        "application",
        "application / enrollment process",
        "application / enrollment",
        "enrollment",
        "proposal",
        "declaration",
        "aadhaar",
        "bank account",
        "kcc",
        "validity of the list of beneficiaries",
    ],

    # -------------------------------------------------
    # PREMIUM / SUBSIDY / CONTRIBUTION
    # -------------------------------------------------
    "premium": [
        "premium",
        "premium rates",
        "premium rates and premium subsidy",
        "premium subsidy",
        "farmer contribution",
        "government contribution",
        "financial contribution",
        "sum insured",
        "scale of finance",
    ],

    # -------------------------------------------------
    # BENEFITS / ENTITLEMENTS / CALCULATION
    # -------------------------------------------------
    "benefits": [
        "benefits",
        "benefits / what farmers receive",
        "what farmers receive",
        "activities covered",
        "components of the scheme",
        "method of calculating benefits",
        "methodology for calculation of benefit",
        "sum insured",
        "coverage amount",
    ],

    # -------------------------------------------------
    # RISKS / WEATHER / SEASONALITY
    # -------------------------------------------------
    "risks": [
        "risks covered",
        "weather risks",
        "weather perils",
        "weather perils to be covered",
        "period of risk",
        "seasonality discipline",
        "post-harvest losses",
        "localized calamity",
        "preventive sowing",
        "failed sowing",
    ],

    # -------------------------------------------------
    # CLAIM / LOSS / ASSESSMENT
    # -------------------------------------------------
    "claim": [
        "claim",
        "claim settlement",
        "claim settlement / payment process",
        "assessment of claims",
        "assessment of loss",
        "loss assessment",
        "shortfall in yield",
        "yield estimation",
        "documentary evidence required for claim assessment",
        "time frame for loss assessment",
        "procedure for settlement of claims",
    ],

    # -------------------------------------------------
    # PAYMENT / DISBURSEMENT
    # -------------------------------------------------
    "payment": [
        "payment",
        "payment process",
        "payment / disbursement process",
        "electronic remittance",
        "fund transfer",
        "modalities for transfer of benefit",
        "claim / pension payment process",
    ],

    # -------------------------------------------------
    # GRIEVANCE / DISPUTE / REDRESSAL
    # -------------------------------------------------
    "grievance": [
        "grievance",
        "grievance redressal",
        "grievance redressal mechanism",
        "complaint",
        "dispute resolution",
        "review monitoring and grievance redressal",
    ],

    # -------------------------------------------------
    # ADMIN / IMPLEMENTATION / GOVERNANCE
    # -------------------------------------------------
    "administration": [
        "role and responsibilities",
        "role and responsibilities of various agencies",
        "district level implementation committee",
        "inter departmental working group",
        "tendering and notification",
        "empanelment and selection of insurance companies",
        "monitoring and review of the scheme",
        "coordination among various participating agencies",
    ],

    # -------------------------------------------------
    # OVERVIEW / GENERAL
    # -------------------------------------------------
    "overview": [
        "scheme overview",
        "overview",
        "introduction",
        "objective of the scheme",
        "purpose",
        "key features of the scheme",
        "general guidelines",
        "scheme",
    ],
}


def detect_target_sections(query: str) -> List[str]:
    q = query.lower()
    targets: List[str] = []

    for keywords in SECTION_KEYWORDS.values():
        for kw in keywords:
            if kw in q:
                targets.extend(keywords)
                break

    return list(set(targets))


def get_vectorstore():
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedding_model(),
        persist_directory=str(VECTOR_DB_DIR),
    )


def normalize(text: str) -> str:
    return re.sub(r"[^a-z ]", " ", text.lower())


def retrieve_chunks(
    query: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    scheme_code: Optional[str] = None,
    intent: Optional[str] = None,
    use_mmr: bool = False,
) -> List[Dict]:

    vectordb = get_vectorstore()

    # -------------------------------
    # Build SAFE filters
    # -------------------------------
    if scheme_code:
        summary_filter = {
            "$and": [
                {"source_type": "summary"},
                {"scheme_code": scheme_code},
            ]
        }
        pdf_filter = {
            "$and": [
                {"source_type": "pdf"},
                {"scheme_code": scheme_code},
            ]
        }
    else:
        summary_filter = {"source_type": "summary"}
        pdf_filter = {"source_type": "pdf"}
    
    # -------------------------------
    # Always retrieve BOTH sources
    # -------------------------------
    summary_docs = vectordb.similarity_search_with_score(
        query,
        k=top_k * 3,
        filter=summary_filter,
    )

    pdf_docs = vectordb.similarity_search_with_score(
        query,
        k=top_k * 3,
        filter=pdf_filter,
    )

    docs_with_scores = summary_docs + pdf_docs

    results: List[Dict] = []
    seen_ids: Set[str] = set()

    target_sections = detect_target_sections(query)

    for doc, score in docs_with_scores:
        meta = doc.metadata

        uid = f"{meta.get('parent_id')}::{meta.get('chunk_index')}"
        if uid in seen_ids:
            continue
        seen_ids.add(uid)

        final_score = score

        # -------------------------------
        # Section-aware boost
        # -------------------------------
        primary_section = normalize(meta.get("primary_section") or "")
        for ts in target_sections:
            if ts in primary_section:
                final_score -= 0.35
                break

        # -------------------------------
        # Source-type bias
        # -------------------------------
        if meta.get("source_type") == "summary":
            final_score -= 0.25   # STRONG preference
        else:
            final_score += 0.05   # factual backup

        results.append({
            "text": doc.page_content,
            "metadata": meta,
            "score": final_score,
        })

        # -------------------------------
        # Neighbor expansion (controlled)
        # -------------------------------
        parent_id = meta.get("parent_id")
        chunk_index = meta.get("chunk_index")

        if parent_id is None or chunk_index is None:
            continue

        for neighbor_idx in (chunk_index - 1, chunk_index + 1):
            if neighbor_idx < 0:
                continue

            neighbor = vectordb.similarity_search(
                query="context",
                k=1,
                filter={
                    "$and": [
                        {"parent_id": parent_id},
                        {"chunk_index": neighbor_idx},
                    ]
                },
            )

            if not neighbor:
                continue

            n_doc = neighbor[0]
            n_meta = n_doc.metadata
            n_uid = f"{n_meta.get('parent_id')}::{n_meta.get('chunk_index')}"

            if n_uid in seen_ids:
                continue

            seen_ids.add(n_uid)

            results.append({
                "text": n_doc.page_content,
                "metadata": n_meta,
                "score": None,
            })

    # -------------------------------
    # Final ranking
    # -------------------------------
    results.sort(
        key=lambda x: x["score"] if x["score"] is not None else 999
    )

    return results[:top_k]
