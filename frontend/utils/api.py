import requests
import logging
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote
import os

load_dotenv()

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 180))

def health_check():
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=API_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return None

def get_documents():
    try:
        resp = requests.get(f"{BACKEND_URL}/documents", timeout=API_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        return {"documents": [], "total": 0}

def get_files():
    try:
        resp = requests.get(f"{BACKEND_URL}/files", timeout=API_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Get files error: {e}")
        return {"files": [], "total": 0}

def upload_document(file_bytes, filename, file_type):
    try:
        files = {"file": (filename, file_bytes, file_type)}
        resp = requests.post(f"{BACKEND_URL}/upload", files=files, timeout=API_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        # Handle both response formats from backend
        # Format 1: {"status": "success", ...} - explicit status
        # Format 2: {"message": "Document processed successfully..."} - no explicit status
        if "status" not in data and "message" in data:
            # Infer success from message content if status field missing
            if "successfully" in data.get("message", "").lower():
                data["status"] = "success"
            else:
                data["status"] = "error"
        
        return data
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return {"status": "error", "message": str(e)}

def retrieve_clauses(index_name, query, top_k=5):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/retrieve",
            params={"document": index_name, "query": query, "top_k": top_k},
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Retrieve error: {e}")
        return {"clauses": [], "error": str(e)}

def get_clauses(index_name, top_k=5):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/analysis/clauses",
            params={"document": index_name, "per_query_k": top_k},
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Get clauses error: {e}")
        return {"clauses": [], "error": str(e)}

def get_risk(index_name, top_k=5):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/analysis/risk",
            params={"document": index_name},
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Get risk error: {e}")
        return {"risks": [], "error": str(e)}

def get_compliance(index_name, top_k=5):
    try:
        # Compliance check requires file upload - this is a placeholder
        # In the Analysis page, we should handle compliance separately
        return {"compliance": [], "message": "Compliance check requires document upload"}
    except Exception as e:
        logger.error(f"Get compliance error: {e}")
        return {"compliance": [], "error": str(e)}

def get_summary(index_name, top_k=5):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/analysis/summary",
            params={"document": index_name, "top_k": top_k},
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Get summary error: {e}")
        return {"summary": "", "error": str(e)}

def get_structured(index_name, top_k=5):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/analysis/structured",
            params={"document": index_name, "per_query_k": top_k},
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Get structured error: {e}")
        return {"structured": {}, "error": str(e)}

def get_llm_summary(index_name):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/llm/summary/{index_name}",
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Get LLM summary error: {e}")
        return {"summary": "", "error": str(e)}

def get_llm_risk(index_name):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/llm/risk/{index_name}",
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Get LLM risk error: {e}")
        return {"risk_analysis": "", "error": str(e)}

def get_llm_structured(index_name):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/llm/structured/{index_name}",
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Get LLM structured error: {e}")
        return {"structured": {}, "error": str(e)}

def delete_index(index_name):
    """Delete an index by name"""
    try:
        # CHANGED: /delete/ → /index/
        resp = requests.delete(
            f"{BACKEND_URL}/index/{index_name}",  # ← Changed this
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Delete index error: {e}")
        return {"status": "error", "message": str(e)}