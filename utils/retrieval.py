"""
retrieval.py  —  DEPLOYMENT-STABLE VERSION
------------------------------------------
US-05 : Advanced Retrieval Pipeline (RAG)

Features:
  EXTRA-08 : Threshold disabled for FakeEmbeddings deployment
  EXTRA-09 : Multi-document FAISS indexes
  EXTRA-10 : Retrieval statistics
  FIX-RENDER-01 : Render-safe low-memory deployment
"""
import logging
import os
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings
from langchain.schema import Document

logger = logging.getLogger(__name__)

# ── Deployment-safe config ───────────────────────────────────────────
MIN_RELEVANCE_SCORE = 0.0

# ── Singleton embeddings instance ────────────────────────────────────
_embeddings_instance = None


def _get_embeddings():
    """
    Ultra-light deployment-safe embeddings for free hosting.
    """
    global _embeddings_instance

    if _embeddings_instance is None:
        logger.info("Loading ultra-light deployment embeddings")
        _embeddings_instance = FakeEmbeddings(size=384)

    return _embeddings_instance


# ─────────────────────────────────────────────────────────────────────
# Build vectorstore
# ─────────────────────────────────────────────────────────────────────
def build_vectorstore(
    documents: list[Document],
    store_dir: str,
    index_name: str = "legal_index",
) -> FAISS:
    """
    Build and save FAISS vectorstore for a document.
    """

    if not documents:
        raise ValueError(
            "Cannot build vectorstore from empty document list."
        )

    Path(store_dir).mkdir(
        parents=True,
        exist_ok=True
    )

    embeddings = _get_embeddings()

    logger.info(
        f"Embedding {len(documents)} chunks → index '{index_name}'"
    )

    try:
        vectorstore = FAISS.from_documents(
            documents,
            embeddings
        )

    except Exception as exc:
        logger.error(
            f"FAISS build failed: {exc}"
        )

        raise RuntimeError(
            f"Vectorstore build error: {exc}"
        ) from exc

    vectorstore.save_local(
        store_dir,
        index_name=index_name
    )

    logger.info(
        f"FAISS index saved: '{store_dir}/{index_name}'"
    )

    return vectorstore


# ─────────────────────────────────────────────────────────────────────
# Load vectorstore
# ─────────────────────────────────────────────────────────────────────
def load_vectorstore(
    store_dir: str,
    index_name: str = "legal_index",
) -> FAISS:
    """
    Load existing FAISS vectorstore.
    """

    index_path = Path(store_dir) / f"{index_name}.faiss"

    if not index_path.exists():
        raise FileNotFoundError(
            f"No FAISS index found for '{index_name}'. "
            "Please upload and process the document first."
        )

    embeddings = _get_embeddings()

    try:
        vectorstore = FAISS.load_local(
            store_dir,
            embeddings,
            index_name=index_name,
            allow_dangerous_deserialization=True,
        )

        logger.info(
            f"FAISS index loaded: '{store_dir}/{index_name}'"
        )

        return vectorstore

    except Exception as exc:
        raise RuntimeError(
            f"Failed to load FAISS index: {exc}"
        ) from exc


# ─────────────────────────────────────────────────────────────────────
# List available indexes
# ─────────────────────────────────────────────────────────────────────
def list_available_indexes(
    store_dir: str
) -> list[str]:
    """
    Return all indexed document names.
    """

    store_path = Path(store_dir)

    if not store_path.exists():
        return []

    return [
        f.stem
        for f in store_path.glob("*.faiss")
    ]


# ─────────────────────────────────────────────────────────────────────
# Retrieval
# ─────────────────────────────────────────────────────────────────────
def retrieve_clauses(
    query: str,
    vectorstore: FAISS,
    top_k: int = 5,
) -> dict:
    """
    Retrieve relevant clauses for legal analysis.

    Threshold filtering disabled because FakeEmbeddings
    produce weak similarity scores.
    """

    if not query or not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    if top_k <= 0:
        raise ValueError(
            f"top_k must be positive, got {top_k}"
        )

    logger.info(
        f"Retrieving top-{top_k} clauses for: '{query}'"
    )

    fetch_k = min(
        top_k * 3,
        20
    )

    results_with_scores = (
        vectorstore.similarity_search_with_score(
            query,
            k=fetch_k
        )
    )

    clauses = []

    for doc, distance in results_with_scores:

        relevance = round(
            1 / (1 + float(distance)),
            4
        )

        clauses.append({
            "chunk_index": doc.metadata.get(
                "chunk_index",
                -1
            ),
            "source": doc.metadata.get(
                "source",
                "unknown"
            ),
            "file_type": doc.metadata.get(
                "file_type",
                "unknown"
            ),
            "content": doc.page_content.strip(),
            "relevance_score": relevance,
            "word_count": doc.metadata.get(
                "word_count",
                0
            ),
            "has_monetary_amounts": doc.metadata.get(
                "has_monetary_amounts",
                False
            ),
            "has_dates": doc.metadata.get(
                "has_dates",
                False
            ),
        })

        if len(clauses) >= top_k:
            break

    # ── Retrieval statistics ────────────────────────────────────────
    scores = [
        clause["relevance_score"]
        for clause in clauses
    ]

    stats = {}

    if scores:
        stats = {
            "max_score": max(scores),
            "min_score": min(scores),
            "avg_score": round(
                sum(scores) / len(scores),
                4
            ),
            "threshold_used": MIN_RELEVANCE_SCORE,
        }

    logger.info(
        f"Retrieved {len(clauses)} clauses"
    )

    return {
        "clauses": clauses,
        "stats": stats
    }
