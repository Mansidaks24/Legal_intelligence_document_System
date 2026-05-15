import streamlit as st
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.api import (
    get_documents,
    get_clauses,
    get_risk,
    get_compliance,
    get_summary,
    get_structured
)

from utils.styles import apply_judicial_theme


# ═════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Analysis - Legal Document Intelligence",
    page_icon="📊",
    layout="wide"
)

apply_judicial_theme()


# ═════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════
st.markdown(
    "<h1 style='text-align: center; color: #1F3A5E;'>📊 DOCUMENT ANALYSIS</h1>",
    unsafe_allow_html=True
)

st.markdown("---")


# ═════════════════════════════════════════════════════════════════════
# DOCUMENT SELECTION
# ═════════════════════════════════════════════════════════════════════
docs = get_documents()

if docs.get("total", 0) == 0:
    st.warning(
        "📌 No documents indexed yet. Please upload documents first."
    )
    st.stop()

indices = [
    d["index_name"]
    for d in docs["documents"]
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


# ═════════════════════════════════════════════════════════════════════
# TABS
# ═════════════════════════════════════════════════════════════════════
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

                    for i, clause in enumerate(
                        clauses,
                        1
                    ):
                        with st.expander(
                            f"Clause {i}"
                        ):
                            st.markdown(
                                clause.get(
                                    "content",
                                    clause.get(
                                        "text",
                                        ""
                                    )
                                )
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
                    severity = result.get(
                        "severity",
                        "unknown"
                    ).upper()

                    avg_score = result.get(
                        "avg_score",
                        0
                    )

                    if severity == "HIGH":
                        st.error(
                            f"⚠️ HIGH RISK - Average Score: {avg_score}"
                        )

                    elif severity == "MEDIUM":
                        st.warning(
                            f"⚠️ MEDIUM RISK - Average Score: {avg_score}"
                        )

                    else:
                        st.success(
                            f"✅ LOW RISK - Average Score: {avg_score}"
                        )

                    for i, risk in enumerate(
                        risks,
                        1
                    ):

                        score = risk.get(
                            "score",
                            0
                        )

                        keywords = risk.get(
                            "matched_keywords",
                            []
                        )

                        with st.expander(
                            f"Risk {i} (Score: {score})"
                        ):

                            st.markdown(
                                risk.get(
                                    "content",
                                    ""
                                )
                            )

                            if keywords:
                                st.caption(
                                    f"🔴 Risk Keywords: {', '.join(keywords)}"
                                )

                else:
                    st.info(
                        "No risk analysis available."
                    )


# ═════════════════════════════════════════════════════════════════════
# TAB 3 — COMPLIANCE
# ═════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(
        "<h3 style='color: #1F3A5E;'>✅ Compliance Review</h3>",
        unsafe_allow_html=True
    )

    st.markdown(
        "### Upload Compliance Rules File (JSON or TXT)"
    )

    uploaded_rules = st.file_uploader(
        "Upload compliance rules file",
        type=["json", "txt"],
        key="compliance_rules_upload"
    )

    default_rules = [
        {
            "name": "Notice Period Check",
            "description": "Document must contain notice period clause",
            "pattern": "notice period",
            "required": True
        },
        {
            "name": "Penalty Clause Check",
            "description": "Document must contain reimbursement or penalty clause",
            "pattern": "reimbursement|penalty",
            "required": True
        },
        {
            "name": "Confidentiality Check",
            "description": "Document must contain confidentiality clause",
            "pattern": "confidential",
            "required": True
        },
        {
            "name": "Termination Check",
            "description": "Document must contain termination clause",
            "pattern": "termination",
            "required": True
        }
    ]

    # ── Parse Uploaded Rules ────────────────────────────────────────
    if uploaded_rules is not None:
        try:
            file_content = uploaded_rules.read().decode(
                "utf-8"
            )

            custom_rules = json.loads(
                file_content
            )

            if isinstance(
                custom_rules,
                list
            ):
                rules_to_use = custom_rules

                st.success(
                    f"Loaded {len(custom_rules)} custom compliance rules."
                )

            else:
                rules_to_use = default_rules

                st.warning(
                    "Uploaded file must contain a valid JSON list. Using default rules."
                )

        except Exception as e:
            rules_to_use = default_rules

            st.error(
                f"Failed to parse uploaded rules: {str(e)}"
            )

    else:
        rules_to_use = default_rules

    # ── Display Active Rules ────────────────────────────────────────
    with st.expander(
        "📜 Active Compliance Rules"
    ):
        st.json(
            rules_to_use
        )

    # ── Compliance Check ────────────────────────────────────────────
    if st.button(
        "📋 Check Compliance",
        use_container_width=True,
        key="btn_compliance"
    ):

        with st.spinner(
            "Checking compliance..."
        ):

            result = get_compliance(
                selected_index,
                rules_to_use
            )

        if result.get("error"):
            st.error(
                f"Compliance check failed: {result['error']}"
            )

        else:
            passed = result.get(
                "passed_checks",
                0
            )

            total = result.get(
                "total_checks",
                0
            )

            if passed == total:
                st.success(
                    f"✅ Compliance Passed! {passed}/{total} rules satisfied"
                )

            elif passed > 0:
                st.warning(
                    f"⚠️ Partial Compliance: {passed}/{total} rules satisfied"
                )

            else:
                st.error(
                    f"❌ Compliance Failed! Only {passed}/{total} rules satisfied"
                )

            for rule in result.get(
                "compliance_results",
                []
            ):

                rule_name = rule.get(
                    "name",
                    "Unknown Rule"
                )

                passed_rule = rule.get(
                    "passed",
                    False
                )

                description = rule.get(
                    "description",
                    ""
                )

                matched_text = rule.get(
                    "matched_text",
                    ""
                )

                icon = (
                    "✅"
                    if passed_rule
                    else "❌"
                )

                with st.expander(
                    f"{icon} {rule_name}"
                ):
                    st.write(
                        f"**Description:** {description}"
                    )

                    st.write(
                        f"**Status:** {'Passed' if passed_rule else 'Failed'}"
                    )

                    if matched_text:
                        st.code(
                            matched_text,
                            language="text"
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

        with st.spinner(
            "Generating summary..."
        ):

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
                    "No summary available."
                )

                if summary_text:
                    st.success(
                        "✅ Summary generated"
                    )

                    st.markdown(
                        summary_text
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

        with st.spinner(
            "Extracting structured data..."
        ):

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


# ═════════════════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════════════════
st.markdown("---")

st.markdown(
    "<p style='text-align: center; color: #555;'>"
    "💡 Perform comprehensive analysis on your indexed documents"
    "</p>",
    unsafe_allow_html=True
)
