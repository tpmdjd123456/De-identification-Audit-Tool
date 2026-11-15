"""Local Streamlit review UI: rule-based demo and GraSCCo gold-span comparison."""
from html import escape
from pathlib import Path
import json

import streamlit as st

from audit_tool import audit_external_text, run_pipeline
from audit_tool.sample_data import SAMPLES
from evaluation.document_review import DEFAULT_ARCHIVE, PIPELINE_NAMES, load_review_documents, review_document

st.set_page_config(page_title="Clinical De-identification Audit", layout="wide")
st.title("Clinical De-identification Audit — Prototype")
st.caption("Research demonstration · synthetic data only · not validated for real patient records")

mode = st.sidebar.radio(
    "Workflow", ["Transform and review", "Audit existing text", "GraSCCo Document Review"]
)
if mode != "GraSCCo Document Review":
    language = st.sidebar.selectbox(
        "Language", ["de", "en"], format_func=lambda code: "German" if code == "de" else "English"
    )


def highlighted(text, spans):
    """Display the unchanged source text with safely escaped highlighted spans."""
    out = []
    index = 0
    for span in sorted(spans, key=lambda item: item.start):
        out.append(escape(text[index:span.start]))
        out.append(
            '<mark style="background:#fce4a6;padding:2px;border-radius:2px" '
            f'title="{escape(span.label)}">{escape(text[span.start:span.end])}</mark>'
        )
        index = span.end
    out.append(escape(text[index:]))
    return (
        '<div style="white-space:pre-wrap;line-height:1.8;padding:12px;'
        'border:1px solid #aaa;border-radius:6px">' + "".join(out) + "</div>"
    )


if mode == "Transform and review":
    st.subheader("Build a basic transformation pipeline")
    st.info("This workflow uses the small bilingual regex baseline, not GraSCCo gold annotations.")
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
        st.dataframe(
            [{"type": s.label, "value": s.text, "start": s.start, "end": s.end} for s in result.spans],
            use_container_width=True,
        )
    st.download_button("Download transformed text", result.transformed_text, "transformed.txt", mime="text/plain")

elif mode == "Audit existing text":
    st.subheader("Audit text transformed elsewhere")
    entered = st.text_area(
        "Paste only synthetic or authorized text",
        value="Patient [PERSON] was seen in Berlin on [DATE].",
        height=150,
    )
    flags = audit_external_text(entered, language=language)
    st.metric("Pattern matches for human review", len(flags))
    st.markdown(highlighted(entered, flags), unsafe_allow_html=True)
    if flags:
        st.dataframe(
            [{"type": s.label, "text": s.text, "start": s.start, "end": s.end} for s in flags],
            use_container_width=True,
        )
    st.info("Without original text or gold labels, this is only a basic pattern-matching audit; it cannot measure actual leakage.")

else:
    st.subheader("GraSCCo Document Review")
    st.caption(
        "German GraSCCo_PHI v1 · original text and gold PHI annotations embedded in the local JSON ZIP · "
        "the transformations are evaluated with gold labels, not live detector predictions"
    )
    archive = Path(DEFAULT_ARCHIVE)
    if not archive.is_file():
        st.warning("GraSCCo_PHI is not installed locally. The original demo workflows still work.")
        st.markdown("Download the **annotation JSON ZIP** from [Zenodo](https://doi.org/10.5281/zenodo.11502329) and save it as:")
        st.code(str(archive), language=None)
        st.caption("Do not extract the ZIP. The dataset and the generated audit records remain local and gitignored.")
    else:
        @st.cache_data(show_spinner=False)
        def cached_documents(path: str, modification_time_ns: int):
            return load_review_documents(path)

        try:
            documents = cached_documents(str(archive), archive.stat().st_mtime_ns)
            document_map = {doc.document_id: doc for doc in documents}
            if not document_map:
                st.error("The archive contained no GraSCCo documents.")
            else:
                left, right = st.columns(2)
                with left:
                    selected_id = st.selectbox("Clinical document", sorted(document_map))
                with right:
                    pipeline_name = st.selectbox(
                        "Transformation pipeline", PIPELINE_NAMES,
                        format_func=lambda name: {
                            "P0_mask": "P0 — Masking",
                            "P1_placeholder": "P1 — Typed placeholders",
                            "P2_surrogate": "P2 — Surrogates and generalization",
                        }[name],
                    )
                review = review_document(document_map[selected_id], pipeline_name)
                result = review.transformation
                a, b, c, d = st.columns(4)
                a.metric("Documents in corpus", len(documents))
                b.metric("Gold PHI spans", len(review.document.spans))
                c.metric("Placeholder fallbacks", review.fallback_count)
                d.metric("Unchanged annotated spans", review.unchanged_count)

                col_orig, col_new = st.columns(2)
                with col_orig:
                    st.markdown("**Original German document — gold annotations highlighted**")
                    st.markdown(highlighted(review.document.text, review.document.spans), unsafe_allow_html=True)
                with col_new:
                    st.markdown(f"**Transformed document — {pipeline_name}**")
                    st.code(result.output_text, language=None, wrap_lines=True)

                if review.original_string_flags:
                    st.info(
                        f"{review.original_string_flags} original-string reappearance flags: "
                        "an original value also occurs elsewhere in the transformed document. "
                        "These flags need review and are not a re-identification risk score."
                    )
                st.markdown("**Transformation audit log**")
                st.dataframe(review.audit_rows(), use_container_width=True)
                with st.expander("Pipeline configuration and reproducibility details"):
                    st.json(result.config)
                    st.caption(f"Document-specific date offset: {result.date_offset_days} days")
                st.download_button(
                    "Download transformed text", result.output_text,
                    f"{selected_id}_{pipeline_name}.txt", mime="text/plain",
                )
                audit_json = json.dumps(
                    {"document_id": selected_id, "config": result.config,
                     "date_offset_days": result.date_offset_days, "spans": review.audit_rows()},
                    ensure_ascii=False, indent=2,
                )
                st.download_button(
                    "Download audit JSON (contains original spans)", audit_json,
                    f"{selected_id}_{pipeline_name}_audit.json", mime="application/json",
                )
                st.caption(
                    "This dataset is synthetic, but the downloaded audit JSON includes original annotated values. "
                    "Keep it local and do not commit generated documents or logs."
                )
        except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
            st.error(f"Unable to read or transform the local GraSCCo archive: {error}")

st.warning(
    "Research prototype only. A zero unchanged-span count is not proof of anonymity or clinical utility. "
    "Do not use this interface for identifiable real-patient records."
)
