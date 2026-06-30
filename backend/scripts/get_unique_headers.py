from collections import defaultdict
from langchain_chroma import Chroma

from backend.app.rag.vectorization.vectorstore import (
    get_embedding_model,
    VECTOR_DB_DIR,
    COLLECTION_NAME,
)


def main():
    vectordb = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedding_model(),
        persist_directory=str(VECTOR_DB_DIR),
    )

    data = vectordb.get(include=["metadatas"])

    unique_headers = set()

    for meta in data["metadatas"]:
        if not meta:
            continue

        # ---- primary_section ----
        ps = meta.get("primary_section")
        if ps:
            unique_headers.add(ps.strip())

        # ---- section_context (stored as string: "A | B | C") ----
        sc = meta.get("section_context")
        if sc:
            for part in sc.split("|"):
                part = part.strip()
                if part:
                    unique_headers.add(part)

        # ---- sections_found (stored as string after normalization) ----
        sf = meta.get("sections_found")
        if sf:
            for part in sf.split("|"):
                part = part.strip()
                if part:
                    unique_headers.add(part)

    print("\n" + "=" * 80)
    print(f"✅ TOTAL UNIQUE HEADERS FOUND: {len(unique_headers)}")
    print("=" * 80 + "\n")

    for header in sorted(unique_headers):
        print(header)


if __name__ == "__main__":
    main()
