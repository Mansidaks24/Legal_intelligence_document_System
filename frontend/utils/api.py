import requests
import logging
from pathlib import Path
from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()

logger = logging.getLogger(__name__)

# ── Backend URL Configuration ────────────────────────────────────────
try:
    BACKEND_URL = st.secrets["BACKEND_URL"]
except Exception:
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

API_TIMEOUT = int(os.getenv("API_TIMEOUT", 300))


# ═════════════════════════════════════════════════════════════════════
# SYSTEM HEALTH
# ═════════════════════════════════════════════════════════════════════
def health_check():
    try:
        resp = requests.get(
            f"{BACKEND_URL}/health",
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return None


# ═════════════════════════════════════════════════════════════════════
# DOCUMENT LISTING
# ═════════════════════════════════════════════════════════════════════
def get_documents():
    try:
        resp = requests.get(
            f"{BACKEND_URL}/documents",
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()

        data = resp.json()

        return {
            "documents": data.get("documents", []),
            "total": data.get("total", 0),
            "status": data.get("status", "success")
        }

    except Exception as e:
        logger.error(f"Get documents error: {e}")
        return {
            "documents": [],
            "total": 0,
            "status": "error",
            "error": str(e)
        }


def get_files():
    try:
        resp = requests.get(
            f"{BACKEND_URL}/files",
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()

        data = resp.json()

        return {
            "files": data.get("files", []),
            "total": data.get("total", 0),
            "status": data.get("status", "success")
        }

    except Exception as e:
        logger.error(f"Get files error: {e}")
        return {
            "files": [],
            "total": 0,
            "status": "error",
            "error": str(e)
        }


# ═════════════════════════════════════════════════════════════════════
# UPLOAD DOCUMENT
# ═════════════════════════════════════════════════════════════════════
def upload_document(file_bytes, filename, file_type):
    try:
        files = {
            "file": (
                filename,
                file_bytes,
                file_type
            )
        }

        resp = requests.post(
            f"{BACKEND_URL}/upload",
            files=files,
            timeout=API_TIMEOUT
        )

        resp.raise_for_status()

        data = resp.json()

        if "status" not in data:
            if "successfully" in data.get("message", "").lower():
                data["status"] = "success"
            else:
                data["status"] = "error"

        return data

    except Exception as e:
        logger.error(f"Upload error: {e}")

        return {
            "status": "error",
            "message": str(e)
        }


# ═════════════════════════════════════════════════════════════════════
# SEARCH / RETRIEVAL
# ═════════════════════════════════════════════════════════════════════
def retrieve_clauses(index_name, query, top_k=5):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/retrieve",
            params={
                "document": index_name,
                "query": query,
                "top_k": top_k
            },
            timeout=API_TIMEOUT
        )

        resp.raise_for_status()

        data = resp.json()

        clauses = data.get(
            "clauses",
            data.get("results", [])
        )

        return {
            "clauses": clauses,
            "stats": data.get("stats", {}),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Retrieve error: {e}")

        return {
            "clauses": [],
            "stats": {},
            "status": "error",
            "error": str(e)
        }


# ═════════════════════════════════════════════════════════════════════
# CLAUSE ANALYSIS
# ═════════════════════════════════════════════════════════════════════
def get_clauses(index_name, top_k=5):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/analysis/clauses",
            params={
                "document": index_name,
                "per_query_k": top_k
            },
            timeout=API_TIMEOUT
        )

        resp.raise_for_status()

        data = resp.json()

        return {
            "clauses": data.get("clauses", []),
            "status": data.get("status", "success")
        }

    except Exception as e:
        logger.error(f"Get clauses error: {e}")

        return {
            "clauses": [],
            "status": "error",
            "error": str(e)
        }


# ═════════════════════════════════════════════════════════════════════
# RISK ANALYSIS
# ═════════════════════════════════════════════════════════════════════
def get_risk(index_name, top_k=5):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/analysis/risk",
            params={
                "document": index_name,
                "top_k": top_k
            },
            timeout=API_TIMEOUT
        )

        resp.raise_for_status()

        data = resp.json()

        return {
            "risks": data.get("risks", []),
            "avg_score": data.get("avg_score", 0),
            "severity": data.get("severity", "none"),
            "status": data.get("status", "success")
        }

    except Exception as e:
        logger.error(
            f"Get risk error: {e}"
        )

        return {
            "risks": [],
            "avg_score": 0,
            "severity": "none",
            "status": "error",
            "error": str(e)
        }
# ═════════════════════════════════════════════════════════════════════
# COMPLIANCE
# ═════════════════════════════════════════════════════════════════════
def get_compliance(index_name, rules_json):
    """
    Run compliance checks on an indexed document.

    Args:
        index_name: The document index name
        rules_json: Compliance rules (list/dict/JSON string)

    Returns:
        dict with compliance results
    """
    try:
        import json

        # ── Ensure proper JSON serialization ────────────────────────
        if isinstance(rules_json, (list, dict)):
            rules_payload = json.dumps(rules_json)

        elif isinstance(rules_json, str):
            rules_payload = rules_json

        else:
            rules_payload = "[]"

        resp = requests.get(
            f"{BACKEND_URL}/analysis/compliance",
            params={
                "document": index_name,
                "rules": rules_payload
            },
            timeout=API_TIMEOUT
        )

        resp.raise_for_status()

        return resp.json()

    except Exception as e:
        logger.error(
            f"Get compliance error: {e}"
        )

        return {
            "status": "error",
            "error": str(e)
        }

# ═════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════
def get_summary(index_name, top_k=5):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/analysis/summary",
            params={
                "document": index_name,
                "top_k": top_k
            },
            timeout=API_TIMEOUT
        )

        resp.raise_for_status()

        data = resp.json()

        return {
            "summary": data.get("summary", ""),
            "status": data.get("status", "success")
        }

    except Exception as e:
        logger.error(f"Get summary error: {e}")

        return {
            "summary": "",
            "status": "error",
            "error": str(e)
        }


# ═════════════════════════════════════════════════════════════════════
# STRUCTURED OUTPUT
# ═════════════════════════════════════════════════════════════════════
def get_structured(index_name, top_k=5):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/analysis/structured",
            params={
                "document": index_name,
                "per_query_k": top_k
            },
            timeout=API_TIMEOUT
        )

        resp.raise_for_status()

        data = resp.json()

        return {
            "structured": data.get("structured", {}),
            "status": data.get("status", "success")
        }

    except Exception as e:
        logger.error(f"Get structured error: {e}")

        return {
            "structured": {},
            "status": "error",
            "error": str(e)
        }


# ═════════════════════════════════════════════════════════════════════
# LLM ENDPOINTS
# ═════════════════════════════════════════════════════════════════════
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

        return {
            "summary": "",
            "error": str(e)
        }


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

        return {
            "risk_analysis": "",
            "error": str(e)
        }


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

        return {
            "structured": {},
            "error": str(e)
        }


# ═════════════════════════════════════════════════════════════════════
# DELETE INDEX
# ═════════════════════════════════════════════════════════════════════
def delete_index(index_name):
    try:
        resp = requests.delete(
            f"{BACKEND_URL}/index/{index_name}",
            timeout=API_TIMEOUT
        )

        resp.raise_for_status()

        return resp.json()

    except Exception as e:
        logger.error(f"Delete index error: {e}")

        return {
            "status": "error",
            "message": str(e)
        }
