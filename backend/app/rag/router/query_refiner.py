from typing import Dict, List
from dotenv import load_dotenv
from groq import Groq
import json
import os
import re

load_dotenv()

_llm = Groq()
_MODEL = "llama-3.1-8b-instant"

# --------------------------------------------------
# Deterministic scheme dictionary (authoritative)
# --------------------------------------------------
KNOWN_SCHEMES = {
    "PMKISAN": ["pm kisan", "pm-kisan", "kisan samman", "samman nidhi"],
    "PMKMY": ["pmkmy", "maan dhan"],
    "PMFBY": ["pmfby", "fasal bima", "crop insurance"],
    "KCC": ["kisan credit card", "kcc"],
    "RWBCIS": ["rwbcis", "weather based"],
    "PMKSY": ["pmksy", "krishi sinchai"]
}

INTENT_KEYWORDS = {
    "exclusions": ["not eligible", "who cannot", "excluded", "not allowed"],
    "eligibility": ["eligible", "eligibility", "who can", "can i apply"],
    "benefits": ["benefit", "amount", "pension", "money", "support"],
    "coverage": ["covered", "risk", "insurance covers"],
    "overview": ["what is", "explain", "tell me about"],
    "documents": ["document", "documents", "aadhaar", "bank account", "proof"],
}

SYSTEM_PROMPT = """You are a query understanding assistant.

TASK:
- Analyze the user query.
- DO NOT answer the query.
- DO NOT add any facts.
- ONLY extract structured information.

Return ONLY valid JSON in the following format:
{
  "scheme_code": string | null,
  "intent": one of ["overview", "eligibility", "benefits", "exclusions", "coverage", "general"],
  "normalized_query": string
}

Rules:
- Choose scheme_code ONLY from the provided candidate list.
- If no scheme can be confidently identified, set scheme_code to null.
- Do NOT guess.
- If intent is unclear, use "general".
"""

# --------------------------------------------------
# Deterministic helpers
# --------------------------------------------------
def _detect_schemes(query: str) -> List[str]:
    q = query.lower()
    matches = []

    for code, keywords in KNOWN_SCHEMES.items():
        for kw in keywords:
            if kw in q:
                matches.append(code)
                break

    return matches


def _detect_intent(query: str) -> str:
    q = query.lower()

    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
                return intent

    return "general"


# --------------------------------------------------
# Main refiner
# --------------------------------------------------
def refine_query(query: str) -> Dict:
    """
    Normalize and understand the query.
    This function DOES NOT answer anything.
    """

    # 1️⃣ Deterministic scheme detection
    scheme_candidates = _detect_schemes(query)

    scheme_code = scheme_candidates[0] if len(scheme_candidates) == 1 else None

    # 2️⃣ Deterministic intent detection
    intent = _detect_intent(query)

    # 3️⃣ If both detected confidently → skip LLM
    if scheme_code and intent != "general":
        return {
            "scheme_code": scheme_code,
            "intent": intent,
            "normalized_query": f"{scheme_code} {intent}"
        }

    # 4️⃣ LLM fallback ONLY for unresolved parts
    constrained_prompt = SYSTEM_PROMPT + f"\n\nDetected scheme candidates: {scheme_candidates}"

    response = _llm.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": constrained_prompt},
            {"role": "user", "content": query},
        ],
        temperature=0.0,
    )

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)

        # 5️⃣ HARD SAFETY: block hallucinated scheme
        if parsed.get("scheme_code") not in scheme_candidates:
            parsed["scheme_code"] = scheme_code  # fallback to deterministic or None
        
        # If deterministic scheme exists, NEVER let LLM override intent
        if scheme_code:
            parsed["scheme_code"] = scheme_code

        return parsed

    except json.JSONDecodeError:
        # Absolute safety fallback
        return {
            "scheme_code": scheme_code,
            "intent": intent,
            "normalized_query": query,
        }
