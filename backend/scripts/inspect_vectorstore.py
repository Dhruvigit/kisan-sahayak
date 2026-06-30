from langchain_chroma import Chroma
from backend.app.rag.vectorization.vectorstore import get_embedding_model, COLLECTION_NAME
from pathlib import Path


# Resolve paths relative to the project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
VECTOR_DB_DIR = BASE_DIR / "data" / "vectordb"


def inspect_vectorstore(limit=5):
    embedding = get_embedding_model()

    vectordb = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding,
        persist_directory=str(VECTOR_DB_DIR),
    )

    collection = vectordb._collection

    print("\n" + "=" * 80)
    print("📦 VECTORSTORE INSPECTION")
    print("=" * 80)

    total = collection.count()
    print(f"Total vectors stored: {total}")

    if total == 0:
        print("⚠️ Vectorstore is empty.")
        return

    # ✅ deterministic sample (important for debugging)
    results = collection.get(
        limit=min(limit, total),
        include=["documents", "metadatas"],
    )

    for i in range(len(results["documents"])):
        print("\n" + "-" * 60)
        print(f"Vector {i + 1}")
        print("-" * 60)

        print("🧾 Text preview:")
        print(results["documents"][i][:800])

        meta = results["metadatas"][i]

        print("\n🏷 Metadata:")
        print(f"  scheme_code  : {meta.get('scheme_code')}")
        print(f"  scheme_name  : {meta.get('scheme_name')}")
        print(f"  document     : {meta.get('source_document')}")
        print(f"  document_type: {meta.get('document_type')}")
        print(f"  content_level: {meta.get('content_level')}")
        print(f"  parent_id    : {meta.get('parent_id')}")
        print(f"  chunk_index  : {meta.get('chunk_index')}")


if __name__ == "__main__":
    inspect_vectorstore(limit=10)
