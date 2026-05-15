"""
retrieval.py  —  IMPROVED VERSION
------------------------------------
User Stories covered:
  US-05 : Advanced Retrieval Pipeline (RAG)

Additional features added (add to Excel as extras):
  EXTRA-08 : Confidence threshold filtering (ignores low-quality results)
  EXTRA-09 : Multi-document support (each doc gets its own FAISS index)
  EXTRA-10 : Retrieval stats in response (min/max/avg relevance scores)

DEPLOYMENT FIX:
  FIX-RENDER-01 : Lightweight embedding model for Render free deployment
"""
import logging
import os
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document

logger = logging.getLogger(__name__)

# ── Embedding model ───────────────────────────────────────────────────
# Smaller model to prevent Render memory crashes
_EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    ""sentence-transformers/paraphrase-albert-small-v2""
)

# ── Confidence threshold (EXTRA-08) ──────────────────────────────────
MIN_RELEVANCE_SCORE = float(
    os.getenv("MIN_RELEVANCE_SCORE", "0.15")
)

# ─────────────────────────────────────────────────────────────────────
# Embedding model loader (singleton pattern)
# FIXED for low-memory deployment
# ─────────────────────────────────────────────────────────────────────
_embeddings_instance = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    """
    Load lightweight embedding model only once.

    Improvements:
    - Smaller model
    - CPU only
    - Lower memory footprint
    - Prevent repeated loading crashes
    """
    global _embeddings_instance

    if _embeddings_instance is None:
        logger.info(
            f"Loading lightweight embedding model: {_EMBEDDING_MODEL_NAME}"
        )

        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=_EMBEDDING_MODEL_NAME,
            model_kwargs={
                "device": "cpu"
            },
            encode_kwargs={
                "normalize_embeddings": True,
                "batch_size": 8
            },
            cache_folder="./models"
        )

        logger.info(
            "Lightweight embedding model loaded successfully."
        )

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
    Embed all chunks and save a FAISS index to disk.
    """

    if not documents:
        raise ValueError(
            "Cannot build vectorstore from empty document list."
        )

    Path(store_dir).mkdir(
        parents=True,
        exist_ok=True
    )

    Path("./models").mkdir(
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
    Load saved FAISS index from disk.
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
    Return all available FAISS indexes.
    """

    store_path = Path(store_dir)

    if not store_path.exists():
        return []

    return [
        f.stem
        for f in store_path.glob("*.faiss")
    ]


# ─────────────────────────────────────────────────────────────────────
# Semantic retrieval
# ─────────────────────────────────────────────────────────────────────
def retrieve_clauses(
    query: str,
    vectorstore: FAISS,
    top_k: int = 5,
) -> dict:
    """
    Retrieve semantically relevant legal clauses.
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

        if relevance < MIN_RELEVANCE_SCORE:
            logger.debug(
                f"Filtered chunk "
                f"{doc.metadata.get('chunk_index')} "
                f"— score {relevance}"
            )
            continue

        clauses.append({
            "chunk_index": doc.metadata.get(
                "chunk_index", -1
            ),
            "source": doc.metadata.get(
                "source", "unknown"
            ),
            "file_type": doc.metadata.get(
                "file_type", "unknown"
            ),
            "content": doc.page_content.strip(),
            "relevance_score": relevance,
            "word_count": doc.metadata.get(
                "word_count", 0
            ),
            "has_monetary_amounts": doc.metadata.get(
                "has_monetary_amounts", False
            ),
            "has_dates": doc.metadata.get(
                "has_dates", False
            ),
        })

        if len(clauses) >= top_k:
            break

    # ── Retrieval stats ────────────────────────────────────────────
    scores = [
        c["relevance_score"]
        for c in clauses
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
        f"Retrieved {len(clauses)} clauses "
        f"(after threshold filtering)"
    )

    return {
        "clauses": clauses,
        "stats": stats
    }
