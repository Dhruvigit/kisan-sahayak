from typing import Dict

from backend.app.rag.router.mode_detector import detect_mode
from backend.app.rag.router.query_refiner import refine_query
from backend.app.rag.retrieval.retriever import retrieve_chunks
from backend.app.rag.generation.generator import generate_answer


def handle_information_query(query: str) -> Dict:
    """
    End-to-end handler for INFORMATION MODE only.
    """

    # 1️⃣ Detect mode (future-proof)
    mode = detect_mode(query)

    if mode != "information":
        return {
            "status": "unsupported",
            "message": "Advisory mode is not enabled yet."
        }

    # 2️⃣ Refine query (intent + scheme)
    refined = refine_query(query)

    scheme_code = refined.get("scheme_code")
    normalized_query = refined.get("normalized_query") or query

    # 3️⃣ Retrieve
    retrieved_chunks = retrieve_chunks(
        query=normalized_query,
        scheme_code=scheme_code,
    )

    # 4️⃣ Generate answer
    answer = generate_answer(
        query=normalized_query,
        retrieved_chunks=retrieved_chunks,
        intent=refined.get("intent"),
    )

    return {
        "status": "success",
        "mode": "information",
        "scheme_code": scheme_code,
        "intent": refined.get("intent"),
        "answer": answer,
    }
