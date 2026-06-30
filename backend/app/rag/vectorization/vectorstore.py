from pathlib import Path
from typing import List, Dict

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Resolve paths relative to the project root
# d:\Kisan_f\backend\app\rag\vectorization\vectorstore.py -> parents[4] = root
BASE_DIR = Path(__file__).resolve().parents[4]
VECTOR_DB_DIR = BASE_DIR / "data" / "vectordb"
COLLECTION_NAME = "subsidy_chunks"


def get_embedding_model():
    """
    Central place to define embedding model.
    """
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

def normalize_metadata(metadata: dict) -> dict:
    clean = {}

    for k, v in metadata.items():
        if v is None:
            # ChromaDB doesn't support None, convert to empty string
            clean[k] = ""
        elif isinstance(v, list):
            # convert list → string
            clean[k] = " | ".join(str(x) for x in v)
        elif isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            # fallback: stringify anything else
            clean[k] = str(v)

    return clean

def build_vectorstore(chunk_records: List[Dict]):
    """
    Create / update Chroma vector store from chunk records.

    chunk_records format:
    [
        {
            "text": str,
            "metadata": dict
        }
    ]
    """
    texts = [rec["text"] for rec in chunk_records]
    metadatas = [normalize_metadata(rec["metadata"]) for rec in chunk_records]

    embedding = get_embedding_model()

    vectordb = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding,
        persist_directory=str(VECTOR_DB_DIR),
    )

    vectordb.add_texts(
        texts=texts,
        metadatas=metadatas,
    )

    return vectordb
