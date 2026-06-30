from pathlib import Path

from backend.app.rag.ingestion.ingest import ingest_documents
from backend.app.rag.vectorization.vectorstore import build_vectorstore


def main():
    # Resolve paths relative to the project root
    # d:\Kisan_f\backend\app\rag\vectorization\build_vectorstore.py -> parents[4] = root
    BASE_DIR = Path(__file__).resolve().parents[4]
    
    chunk_records = ingest_documents(
        pdf_dir=BASE_DIR / "data" / "pdfs",
        docx_dir=BASE_DIR / "data" / "summaries",
    )

    print(f"✅ Chunks received for vectorization: {len(chunk_records)}")

    build_vectorstore(chunk_records)

    print("✅ Vectorstore build complete")


if __name__ == "__main__":
    main()
