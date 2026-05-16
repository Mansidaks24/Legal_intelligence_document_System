import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.api import (
    get_documents,
    get_clauses,
    get_risk,
    get_compliance,
    get_summary,
    get_structured,
)

from utils.styles import apply_judicial_theme

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Analysis - Legal Document Intelligence",
    page_icon="📊",
    layout="wide"
)

apply_judicial_theme()

# ── Header ───────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='text-align: center; color: #1F3A5E;'>📊 DOCUMENT ANALYSIS</h1>",
    unsafe_allow_html=True
)

st.markdown("---")

# ── Document Check ───────────────────────────────────────────────────
docs = get_documents()

if docs.get("total", 0) == 0:
    st.warning(
        "📌 No documents indexed yet. Please upload documents first."
    )
    st.stop()

indices = [
    d.get("index_name", "")
    for d in docs.get("documents", [])
]

selected_index = st.selectbox(
    "Select document index:",
    indices
)

top_k = st.slider(
    "Number of items to retrieve:",
    1,
    10,
    5
)

# ── Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Clauses",
        "Risk",
        "Compliance",
        "Summary",
        "Structured"
    ]
)

# ═════════════════════════════════════════════════════════════════════
# TAB 1 — CLAUSES
# ═════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown(
        "<h3 style='color: #1F3A5E;'>📋 Key Clauses</h3>",
        unsafe_allow_html=True
    )

    if st.button(
        "📖 Retrieve Clauses",
        use_container_width=True,
        key="btn_clauses"
    ):

        with st.spinner("Retrieving clauses..."):

            result = get_clauses(
                selected_index,
                top_k
            )

            if result.get("error"):
                st.error(
                    f"Failed to retrieve clauses: {result['error']}"
                )

            else:
                clauses = result.get("clauses", [])

                if clauses:
                    st.success(
                        f"Found {len(clauses)} key clauses"
                    )

                    for clause in clauses:
                        chunk_index = clause.get(
                            "chunk_index",
                            "N/A"
                        )

                        relevance = clause.get(
                            "relevance_score",
                            0
                        )

                        with st.expander(
                            f"Clause #{chunk_index} | Relevance Score: {relevance}"
                        ):

                            st.markdown(
                                clause.get(
                                    "content",
                                    "No content available."
                                )
                            )

                            st.caption(
                                f"Source: {clause.get('source', 'Unknown')} | "
                                f"Words: {clause.get('word_count', 0)}"
                            )

                            if clause.get(
                                "has_monetary_amounts"
                            ):
                                st.info(
                                    "💰 Contains monetary references"
                                )

                            if clause.get(
                                "has_dates"
                            ):
                                st.info(
                                    "📅 Contains date references"
                                )

                else:
                    st.info(
                        "No clauses found."
                    )

# ═════════════════════════════════════════════════════════════════════
# TAB 2 — RISK ANALYSIS
# ═════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(
        "<h3 style='color: #1F3A5E;'>⚠️ Risk Analysis</h3>",
        unsafe_allow_html=True
    )

    if st.button(
        "🔍 Analyze Risks",
        use_container_width=True,
        key="btn_risk"
    ):

        with st.spinner("Analyzing risks..."):

            result = get_risk(
                selected_index,
                top_k
            )

            if result.get("error"):
                st.error(
                    f"Failed to analyze risks: {result['error']}"
                )

            else:
                risks = result.get("risks", [])

                if risks:

                    avg_score = result.get(
                        "avg_score",
                        0
                    )

                    severity = result.get(
                        "severity",
                        "unknown"
                    ).upper()

                    # ── Summary Metrics ─────────────────────
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "Average Risk Score",
                            avg_score
                        )

                    with col2:
                        st.metric(
                            "Severity Level",
                            severity
                        )

                    # ── Severity Banner ─────────────────────
                    if severity == "HIGH":
                        st.error(
                            f"⚠️ HIGH RISK DOCUMENT"
                        )

                    elif severity == "MEDIUM":
                        st.warning(
                            f"⚠️ MEDIUM RISK DOCUMENT"
                        )

                    else:
                        st.success(
                            f"✅ LOW RISK DOCUMENT"
                        )

                    # ── Individual Risks ────────────────────
                    for i, risk in enumerate(
                        risks,
                        1
                    ):

                        score = risk.get(
                            "score",
                            risk.get(
                                "risk_score",
                                0
                            )
                        )

                        keywords = risk.get(
                            "matched_keywords",
                            []
                        )

                        risk_level = risk.get(
                            "risk_level",
                            "Unknown"
                        )

                        with st.expander(
                            f"Risk {i} | Score: {score} | Level: {risk_level}"
                        ):

                            st.markdown(
                                risk.get(
                                    "content",
                                    "No content available."
                                )
                            )

                            if keywords:
                                st.caption(
                                    f"🔴 Risk Keywords: {', '.join(keywords)}"
                                )

                else:
                    st.info(
                        "No significant risks detected."
                    )

# ═════════════════════════════════════════════════════════════════════
# TAB 3 — COMPLIANCE
# ═════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(
        "<h3 style='color: #1F3A5E;'>✅ Compliance Review</h3>",
        unsafe_allow_html=True
    )

    st.info(
        "📌 Define compliance rules below as JSON. "
        "Each rule checks if a pattern exists in the document."
    )

    # ── Compliance Rules Input ──────────────────────────────────────
    st.markdown("**Define Compliance Rules (JSON format):**")
    
    default_rules = '''[
    {
        "name": "Confidentiality Check",
        "description": "Document must contain confidentiality clause",
        "pattern": "confidential",
        "required": true
    },
    {
        "name": "Termination Check",
        "description": "Document must contain termination clause",
        "pattern": "termination",
        "required": true
    }
]'''

    rules_json = st.text_area(
        "Compliance Rules (JSON):",
        value=default_rules,
        height=200,
        key="compliance_rules_input"
    )

    if st.button(
        "📋 Check Compliance",
        use_container_width=True,
        key="btn_compliance"
    ):

        with st.spinner("Checking compliance..."):
            import json
            
            # Validate JSON
            try:
                rules_list = json.loads(rules_json)
                if not isinstance(rules_list, list):
                    st.error("Rules must be a JSON array")
                    st.stop()
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON format: {str(e)}")
                st.stop()

            # Call compliance API
            result = get_compliance(
                selected_index,
                rules_json
            )

            if result.get("error"):
                st.error(
                    f"Compliance check failed: {result['error']}"
                )

            elif result.get("status") == "success":
                compliance_results = result.get("compliance_results", [])
                
                if compliance_results:
                    st.success(
                        f"✅ Compliance check complete"
                    )

                    # Show summary
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Total Checks",
                            len(compliance_results)
                        )
                    with col2:
                        passed = sum(
                            1 for r in compliance_results 
                            if r.get("passed")
                        )
                        st.metric(
                            "Passed",
                            f"{passed}/{len(compliance_results)}"
                        )

                    # Show detailed results
                    st.markdown("**Detailed Results:**")
                    for check in compliance_results:
                        name = check.get("name", "Unknown")
                        passed = check.get("passed", False)
                        pattern = check.get("pattern", "")
                        
                        if passed:
                            st.success(
                                f"✅ {name} - Pattern '{pattern}' found"
                            )
                        else:
                            st.warning(
                                f"⚠️ {name} - Pattern '{pattern}' NOT found"
                            )

                else:
                    st.info("No compliance results available.")

            else:
                st.warning(
                    "Compliance check returned unexpected result"
                )

# ═════════════════════════════════════════════════════════════════════
# TAB 4 — SUMMARY
# ═════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown(
        "<h3 style='color: #1F3A5E;'>📄 Document Summary</h3>",
        unsafe_allow_html=True
    )

    if st.button(
        "📊 Generate Summary",
        use_container_width=True,
        key="btn_summary"
    ):

        with st.spinner("Generating summary..."):

            result = get_summary(
                selected_index,
                top_k
            )

            if result.get("error"):
                st.error(
                    f"Failed to generate summary: {result['error']}"
                )

            else:
                summary_text = result.get(
                    "summary",
                    ""
                )

                if summary_text:
                    st.success(
                        "✅ Summary generated"
                    )

                    st.text_area(
                        "Summary",
                        summary_text,
                        height=400
                    )

                else:
                    st.warning(
                        "Unable to generate summary."
                    )

# ═════════════════════════════════════════════════════════════════════
# TAB 5 — STRUCTURED EXTRACTION
# ═════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown(
        "<h3 style='color: #1F3A5E;'>🗂️ Structured Extraction</h3>",
        unsafe_allow_html=True
    )

    if st.button(
        "📑 Extract Structured Data",
        use_container_width=True,
        key="btn_structured"
    ):

        with st.spinner("Extracting structured data..."):

            result = get_structured(
                selected_index,
                top_k
            )

            if result.get("error"):
                st.error(
                    f"Failed to extract data: {result['error']}"
                )

            else:
                structured_data = result.get(
                    "structured",
                    {}
                )

                if structured_data:
                    st.success(
                        "Structured data extracted"
                    )

                    st.json(
                        structured_data
                    )

                else:
                    st.info(
                        "No structured data available."
                    )

# ── Footer ───────────────────────────────────────────────────────────
st.markdown("---")

st.markdown(
    "<p style='text-align: center; color: #555;'>"
    "💡 Perform comprehensive legal analysis on your indexed documents"
    "</p>",
    unsafe_allow_html=True
)
