"""
app.py  —  IMPROVED VERSION (FIXED)
------------------------------------
Legal Document Intelligence System — FastAPI Backend

Fixed issues:
  ✅ Delete endpoint returns proper status fields
  ✅ Upload response includes index_name
  ✅ LLM endpoints match frontend expectations
  ✅ Consistent error handling across all endpoints

Run:
    uvicorn app:app --reload --port 8000

Swagger:
    http://localhost:8000/docs
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()

from utils.parser import extract_text
from utils.chunking import split_into_chunks
from utils.retrieval import (
    build_vectorstore,
    load_vectorstore,
    retrieve_clauses,
    list_available_indexes,
)
from utils.analysis import (
    extract_important_clauses,
    analyze_risk,
    compliance_check_from_text,
    summarize_via_retrieval,
    structured_output_from_clauses,
)
from utils.llm import (
    call_llm,
    llm_summarize_text,
    llm_analyze_risk,
    llm_structured_extraction,
)

# ── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config from .env ──────────────────────────────────────────────────
UPLOAD_DIR      = Path(os.getenv("UPLOAD_DIR", "uploads"))
VECTORSTORE_DIR = Path(os.getenv("VECTORSTORE_DIR", "vectorstore"))
CHUNK_SIZE      = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP   = int(os.getenv("CHUNK_OVERLAP", 200))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", 5))
MAX_FILE_MB     = int(os.getenv("MAX_FILE_MB", 10))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# ── FastAPI app ───────────────────────────────────────────────────────
app = FastAPI(
    title="Legal Document Intelligence System",
    description=(
        "Upload legal PDFs/DOCX → Extract text → Chunk → Embed → "
        "Store in FAISS → Retrieve relevant clauses via semantic search (RAG).\n\n"
        "**Owner:** Thupakula Pavithra | **Version:** 2.1.0"
    ),
    version="2.1.0",
    contact={"name": "Thupakula Pavithra"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8501",      # Streamlit dev
        "http://127.0.0.1:8501",      # Streamlit dev
        "http://localhost:8000",      # Alternative ports
        "http://127.0.0.1:8000",
        os.getenv("FRONTEND_URL", ""),  # Production frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs every incoming request with method, path, status code, and response time."""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} "
        f"→ {response.status_code} ({duration_ms}ms)"
    )
    return response


# ══════════════════════════════════════════════════════════════════════
# Pydantic Models — typed API contracts
# ══════════════════════════════════════════════════════════════════════

class UploadResponse(BaseModel):
    status: str = "success"  # ← ADD THIS
    message: str
    filename: str
    index_name: str  # ← ADD THIS
    file_type: str
    total_chunks: int
    total_characters: int
    chunk_size: int
    chunk_overlap: int
    first_chunk_preview: str
    processed_at: str


class ClauseResult(BaseModel):
    chunk_index: int
    source: str
    file_type: str
    content: str
    relevance_score: float
    word_count: int
    has_monetary_amounts: bool
    has_dates: bool


class RetrievalStats(BaseModel):
    max_score: float
    min_score: float
    avg_score: float
    threshold_used: float


class RetrievalResponse(BaseModel):
    query: str
    document: str
    total_results: int
    stats: RetrievalStats | None
    results: list[ClauseResult]


class HealthResponse(BaseModel):
    status: str
    version: str
    vectorstore_exists: bool
    total_documents_indexed: int
    timestamp: str


class DocumentInfo(BaseModel):
    index_name: str
    use_in_retrieve: str  # ← Keep this for frontend compatibility


# ══════════════════════════════════════════════════════════════════════
# ROUTE 1 — Health Check
# GET /health
# ══════════════════════════════════════════════════════════════════════
@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Health check — confirms server is running."""
    indexes = list_available_indexes(str(VECTORSTORE_DIR))
    return HealthResponse(
        status="ok",
        version="2.1.0",
        vectorstore_exists=len(indexes) > 0,
        total_documents_indexed=len(indexes),
        timestamp=datetime.now().isoformat(),
    )


# ══════════════════════════════════════════════════════════════════════
# ROUTE 2 — Upload & Process (Full RAG Pipeline)
# POST /upload
# ══════════════════════════════════════════════════════════════════════
@app.post("/upload", response_model=UploadResponse, tags=["Pipeline"])
async def upload_and_process(file: UploadFile = File(...)):
    """
    **Full RAG Pipeline — single endpoint**

    Accepts: PDF or DOCX (max 10MB)

    Steps:
    1. Validate file type and size
    2. Sanitize filename (security)
    3. Save to uploads/
    4. Extract text
    5. Split into chunks
    6. Generate embeddings + store in FAISS
    """

    # ── File type validation ──────────────────────────────────────────
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Only .pdf and .docx are accepted.",
        )

    # ── Read file content + size validation ──────────────────────────
    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(contents) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_MB}MB.",
        )

    # ── Filename sanitization (security) ──────────────────────────────
    safe_filename = Path(file.filename).name
    save_path = UPLOAD_DIR / safe_filename

    # ── Save file ─────────────────────────────────────────────────────
    try:
        with open(save_path, "wb") as f:
            f.write(contents)
        logger.info(f"File saved: {save_path} ({len(contents)} bytes)")
    except Exception as exc:
        logger.error(f"File save failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Could not save file: {exc}")

    # ── Extract text ──────────────────────────────────────────────────
    try:
        extraction_result = extract_text(str(save_path))
        text      = extraction_result["text"]
        file_type = extraction_result["file_type"]
        logger.info(f"Extracted {len(text)} characters from {file_type.upper()}")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # ── Chunk text ────────────────────────────────────────────────────
    try:
        chunks = split_into_chunks(
            text=text,
            source_filename=safe_filename,
            file_type=file_type,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        logger.info(f"Created {len(chunks)} chunks")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # ── Embed + Store in FAISS ────────────────────────────────────────
    # Use filename stem as index name → multi-doc support
    index_name = Path(safe_filename).stem.replace(" ", "_").lower()

    try:
        build_vectorstore(
            documents=chunks,
            store_dir=str(VECTORSTORE_DIR),
            index_name=index_name,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # First chunk preview for response
    first_preview = chunks[0].page_content[:150].replace("\n", " ") if chunks else ""

    return UploadResponse(
        status="success",  # ← ADD THIS
        message="Document processed successfully. Use GET /retrieve to search.",
        filename=safe_filename,
        index_name=index_name,  # ← ADD THIS
        file_type=file_type,
        total_chunks=len(chunks),
        total_characters=len(text),
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        first_chunk_preview=first_preview,
        processed_at=datetime.now().isoformat(),
    )


# ══════════════════════════════════════════════════════════════════════
# ROUTE 3 — Semantic Retrieval
# GET /retrieve?query=...&document=...&top_k=5
# ══════════════════════════════════════════════════════════════════════
@app.get("/retrieve", response_model=RetrievalResponse, tags=["Pipeline"])
def retrieve(
    query: str = Query(
        ..., min_length=3,
        description="Natural language query"
    ),
    document: str = Query(
        ...,
        description="Document name to search (filename without extension)"
    ),
    top_k: int = Query(
        default=5, ge=1, le=20,
        description="Number of results to return (1–20)"
    ),
):
    """
    **Semantic Clause Retrieval**

    Converts your query to a vector and finds the most semantically
    similar chunks from the specified document's FAISS index.

    Example queries:
    - `termination clause`
    - `penalty for leaving early`
    - `confidentiality obligations`
    """

    # Load document-specific FAISS index
    index_name = document.replace(" ", "_").lower()

    try:
        vectorstore = load_vectorstore(
            store_dir=str(VECTORSTORE_DIR),
            index_name=index_name,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No index found for document '{document}'. "
                "Use GET /documents to see available documents, "
                "or upload this document first via POST /upload."
            ),
        )

    # Retrieve clauses
    try:
        result = retrieve_clauses(
            query=query,
            vectorstore=vectorstore,
            top_k=top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    clauses = result["clauses"]
    stats   = result["stats"]

    if not clauses:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No relevant clauses found for query '{query}'. "
                "Try a different query or lower the confidence threshold."
            ),
        )

    return RetrievalResponse(
        query=query,
        document=document,
        total_results=len(clauses),
        stats=RetrievalStats(**stats) if stats else None,
        results=[ClauseResult(**c) for c in clauses],
    )


# ══════════════════════════════════════════════════════════════════════
# ROUTE 4 — List all indexed documents
# GET /documents
# ══════════════════════════════════════════════════════════════════════
@app.get("/documents", tags=["System"])
def list_documents():
    """
    List all documents that have been uploaded and indexed in FAISS.
    Use the returned names as the `document` parameter in GET /retrieve.
    """
    indexes = list_available_indexes(str(VECTORSTORE_DIR))
    return {
        "status": "success",
        "total": len(indexes),
        "documents": [
            {"index_name": name, "use_in_retrieve": name}
            for name in indexes
        ],
    }


# ══════════════════════════════════════════════════════════════════════
# ANALYSIS ROUTES
# ══════════════════════════════════════════════════════════════════════

@app.get("/analysis/clauses", tags=["Analysis"])
def api_extract_clauses(document: str, per_query_k: int = 5):
    """Extract important clauses from a document's index."""
    try:
        vs = load_vectorstore(store_dir=str(VECTORSTORE_DIR), index_name=document)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No index found for '{document}'")

    clauses = extract_important_clauses(vectorstore=vs, per_query_k=per_query_k)
    return {"status": "success", "total": len(clauses), "clauses": clauses}


@app.get("/analysis/risk", tags=["Analysis"])
def api_risk_analysis(document: str):
    try:
        vs = load_vectorstore(store_dir=str(VECTORSTORE_DIR), index_name=document)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No index found for '{document}'")

    clauses = extract_important_clauses(vectorstore=vs, per_query_k=6)
    result = analyze_risk(clauses)
    return {
        "status": "success",
        "risks": result.get("per_clause", []),
        "avg_score": result.get("avg_score"),
        "severity": result.get("severity"),
    }

@app.get("/analysis/compliance", tags=["Analysis"])
def api_compliance_check(
    document: str = Query(..., description="Document index name"),
    rules: str = Query(default="[]", description="Compliance rules as JSON"),
):
    """
    Run compliance checks on an indexed document.
    """
    import json

    # ── STEP 1: Parse rules safely ───────────────────────────────────
    try:
        if isinstance(rules, str):
            rules = rules.strip()

            if not rules:
                rules_list = []
            else:
                rules_list = json.loads(rules)

        elif isinstance(rules, list):
            rules_list = rules

        else:
            rules_list = []

        if not isinstance(rules_list, list):
            raise ValueError("rules must be a JSON array")

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rules format: {str(e)}"
        )

    # ── STEP 2: Load vectorstore ─────────────────────────────────────
    try:
        vs = load_vectorstore(
            store_dir=str(VECTORSTORE_DIR),
            index_name=document
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"No index found for '{document}'"
        )

    # ── STEP 3: Retrieve full document text ──────────────────────────
    try:
        docs = vs.similarity_search(
            "document",
            k=1000
        )

        if not docs:
            raise ValueError(
                "No content found in document index."
            )

        combined_text = "\n\n".join(
            doc.page_content
            for doc in docs
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting document text: {str(e)}"
        )

    # ── STEP 4: Default rules fallback ───────────────────────────────
    if not rules_list:
        rules_list = [
            {
                "name": "Termination Clause",
                "description": "Document must contain termination clause",
                "pattern": "termination",
                "required": True
            }
        ]

    # ── STEP 5: Run compliance engine ────────────────────────────────
    try:
        result = compliance_check_from_text(
            text=combined_text,
            rules=rules_list
        )

        compliance_results = result.get(
            "compliance_results",
            []
        )

        passed_checks = sum(
            1
            for r in compliance_results
            if r.get("passed")
        )

        return {
            "status": "success",
            "document": document,
            "compliance_results": compliance_results,
            "total_checks": len(rules_list),
            "passed_checks": passed_checks,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Compliance check error: {str(e)}"
        )
@app.get("/analysis/summary", tags=["Analysis"])
def api_summarize(document: str, top_k: int = 5):
    try:
        vs = load_vectorstore(store_dir=str(VECTORSTORE_DIR), index_name=document)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No index found for '{document}'")

    summary = summarize_via_retrieval(vectorstore=vs, top_k=top_k)
    return {"status": "success", "summary": summary}


@app.get("/analysis/structured", tags=["Analysis"])
def api_structured_output(document: str, per_query_k: int = 6):
    try:
        vs = load_vectorstore(store_dir=str(VECTORSTORE_DIR), index_name=document)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No index found for '{document}'")

    clauses = extract_important_clauses(vectorstore=vs, per_query_k=per_query_k)
    structured = structured_output_from_clauses(clauses)
    return {"status": "success", "total": len(structured), "structured": structured}


# ══════════════════════════════════════════════════════════════════════
# LLM-POWERED ANALYSIS ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

# FIXED: Changed from /analysis/llm/... to /llm/... to match frontend expectations
@app.get("/llm/summary/{document}", tags=["Analysis - LLM"])
def api_llm_summary(document: str, top_k: int = 5):
    """🤖 LLM-powered document summarization using Groq."""
    try:
        vs = load_vectorstore(store_dir=str(VECTORSTORE_DIR), index_name=document)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No index found for '{document}'")

    try:
        clauses = extract_important_clauses(vectorstore=vs, per_query_k=top_k)
        combined_text = "\n\n".join(
            f"Clause {c.get('chunk_index')}: {c.get('content', '')}"
            for c in clauses
        )
        summary = llm_summarize_text(combined_text, top_k=top_k)

        return {
            "status": "success",
            "document": document,
            "summary": summary,
            "clauses_analyzed": len(clauses),
            "provider": "Groq (or OpenAI/HuggingFace fallback)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM summarization error: {str(e)}")


@app.get("/llm/risk/{document}", tags=["Analysis - LLM"])
def api_llm_risk(document: str, top_k: int = 6):
    """🤖 LLM-powered risk analysis using Groq."""
    try:
        vs = load_vectorstore(store_dir=str(VECTORSTORE_DIR), index_name=document)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No index found for '{document}'")

    try:
        clauses = extract_important_clauses(vectorstore=vs, per_query_k=top_k)
        risk_analysis = llm_analyze_risk(clauses)

        return {
            "status": "success",
            "document": document,
            "risk_analysis": risk_analysis,
            "clauses_analyzed": len(clauses),
            "provider": "Groq (or OpenAI/HuggingFace fallback)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM risk analysis error: {str(e)}")


@app.get("/llm/structured/{document}", tags=["Analysis - LLM"])
def api_llm_structured(document: str, per_query_k: int = 6):
    """🤖 LLM-powered structured data extraction using Groq."""
    try:
        vs = load_vectorstore(store_dir=str(VECTORSTORE_DIR), index_name=document)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No index found for '{document}'")

    try:
        clauses = extract_important_clauses(vectorstore=vs, per_query_k=per_query_k)
        structured = llm_structured_extraction(clauses)

        return {
            "status": "success",
            "document": document,
            "structured": structured,
            "clauses_analyzed": len(clauses),
            "provider": "Groq (or OpenAI/HuggingFace fallback)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM structured extraction error: {str(e)}")


# ══════════════════════════════════════════════════════════════════════
# ROUTE 5 — List uploaded files
# GET /files
# ══════════════════════════════════════════════════════════════════════
@app.get("/files", tags=["System"])
def list_uploaded_files():
    """List all uploaded files (PDF and DOCX) in the uploads directory."""
    files = [
        {
            "filename": f.name,
            "file_type": f.suffix.lower().replace(".", ""),
            "size_kb": round(f.stat().st_size / 1024, 2),
        }
        for f in UPLOAD_DIR.iterdir()
        if f.suffix.lower() in ALLOWED_EXTENSIONS
    ]
    return {"status": "success", "total": len(files), "files": files}


# ══════════════════════════════════════════════════════════════════════
# ROUTE 6 — Delete a specific document index
# DELETE /index/{document_name}
# ══════════════════════════════════════════════════════════════════════
@app.delete("/index/{document_name}", tags=["System"])
def delete_index(document_name: str):
    """
    Delete the FAISS index for a specific document.
    The uploaded file in uploads/ is NOT deleted — only the vector index.
    """
    index_name = document_name.replace(" ", "_").lower()
    deleted = []

    for ext in [".faiss", ".pkl"]:
        idx_file = VECTORSTORE_DIR / f"{index_name}{ext}"
        if idx_file.exists():
            try:
                idx_file.unlink()
                deleted.append(str(idx_file))
                logger.info(f"Deleted: {idx_file}")
            except Exception as e:
                logger.error(f"Failed to delete {idx_file}: {e}")

    if deleted:
        return {
            "status": "success",
            "message": f"Index '{index_name}' deleted successfully.",
            "deleted_files": deleted,
        }

    return JSONResponse(
        status_code=404,
        content={
            "status": "not_found",
            "message": f"No index found for '{document_name}'.",
        },
    )
