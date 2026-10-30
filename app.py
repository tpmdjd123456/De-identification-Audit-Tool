"""Streamlit document-review demo. Run with: streamlit run app.py"""
from html import escape

import streamlit as st

from audit_tool import RegexDetector, audit_external_text, run_pipeline
from audit_tool.sample_data import SAMPLES

st.set_page_config(page_title="Clinical De-identification Audit", layout="wide")
st.title("Clinical De-identification Audit — Prototype")
st.caption("Research demo · synthetic data only · not validated for patient records")

language = st.sidebar.selectbox("Language", ["de", "en"], format_func=lambda code: "German" if code == "de" else "English")
mode = st.sidebar.radio("Workflow", ["Transform and review", "Audit existing text"])


def highlighted(text, spans):
    out = []
    index = 0
    for span in spans:
        out.append(escape(text[index:span.start]))
        out.append(
            '<mark style="background:#fce4a6;padding:2px;border-radius:2px" '
            f'title="{escape(span.label)}">{escape(text[span.start:span.end])}</mark>'
        )
        index = span.end
    out.append(escape(text[index:]))
    return '<div style="white-space:pre-wrap;line-height:1.8;padding:12px;border:1px solid #aaa;border-radius:6px">' + "".join(out) + "</div>"


if mode == "Transform and review":
    st.subheader("Build a basic transformation pipeline")
    text = st.text_area("Synthetic clinical note", value=SAMPLES[language], height=140)
    types = ["PERSON", "DATE", "LOCATION", "PATIENT_ID", "AGE"]
    strategies = {}
    left, right = st.columns(2)
    for i, label in enumerate(types):
        with (left if i % 2 == 0 else right):
            choices = ["placeholder", "mask", "keep", "surrogate", "date_shift", "generalize"]
            strategies[label] = st.selectbox(f"{label} strategy", choices, key=f"strategy_{label}")
    shift = st.number_input("Date shift (days, when selected)", -365, 365, 30, step=1)
    result = run_pipeline(text, language=language, strategies=strategies, shift_days=int(shift))
    st.subheader("Document review")
    col_orig, col_new = st.columns(2)
    with col_orig:
        st.markdown("**Original text — detected identifiers highlighted**")
        st.markdown(highlighted(text, result.spans), unsafe_allow_html=True)
    with col_new:
        st.markdown("**Transformed text**")
        st.code(result.transformed_text, language=None, wrap_lines=True)
    a, b = st.columns(2)
    a.metric("Detected spans", result.detected_count)
    b.metric("Original values still present", result.unchanged_identifier_count)
    if result.spans:
        st.dataframe([{"type": s.label, "value": s.text, "start": s.start, "end": s.end} for s in result.spans], use_container_width=True)
    st.download_button("Download transformed text", result.transformed_text, "transformed.txt", mime="text/plain")
else:
    st.subheader("Audit text transformed elsewhere")
    entered = st.text_area("Paste only synthetic or authorized text", value="Patient [PERSON] was seen in Berlin on [DATE].", height=150)
    flags = audit_external_text(entered, language=language)
    st.metric("Pattern matches for human review", len(flags))
    st.markdown(highlighted(entered, flags), unsafe_allow_html=True)
    if flags:
        st.dataframe([{"type": s.label, "text": s.text, "start": s.start, "end": s.end} for s in flags], use_container_width=True)
    st.info("Without original text or gold labels, this is only a basic pattern-matching audit; it cannot measure actual leakage.")

st.warning("Prototype only: regex rules miss many direct and indirect identifiers. A zero count does NOT mean a document is anonymous. Do not upload real patient data.")
