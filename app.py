"""Streamlit interface for the support assistant."""

from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

from verithra.config import Settings, VerithraError
from verithra.indexing import build_index
from verithra.rag.grounding import ABSTENTION_MESSAGE
from verithra.rag.pipeline import Pipeline
from verithra.retrieval.faiss_index import FaissIndex
from verithra.runtime import clients, index_directory, parameters
from verithra.support.cases import load_knowledge

st.set_page_config(page_title="Verithra · Technical support", page_icon="◈", layout="wide")
st.markdown(
    """<style>
    .block-container {max-width:1120px;padding-top:2.8rem;padding-bottom:3rem;}
    h1 {letter-spacing:-.06em;font-size:3.6rem!important;font-weight:650!important;}
    h2,h3 {letter-spacing:-.025em;}
    .hero-label {color:#167568;font-size:.8rem;letter-spacing:.15em;font-weight:650;}
    .hero-description {color:#50615e;font-size:1.15rem;max-width:700px;line-height:1.65;}
    [data-testid="stForm"] {background:white;border-radius:14px;}
    [data-testid="stMetric"] {
      background:white;border:1px solid #e1e8e4;border-radius:10px;padding:14px;
    }
    </style>""",
    unsafe_allow_html=True,
)


def show_citations(identifiers, sources):
    known = {source.chunk_id: source for source in sources}
    labels = [known[i].title for i in identifiers if i in known]
    if labels:
        st.caption("Evidence: " + " · ".join(dict.fromkeys(labels)))


def show_resolution(result):
    st.divider()
    if result.support_status == "INSUFFICIENT_EVIDENCE":
        st.warning("INSUFFICIENT_EVIDENCE")
        st.write(ABSTENTION_MESSAGE)
        st.write(
            "Share the endpoint, exact error code, and relevant logs with secrets removed. "
            "If the issue is outside RelayDesk, add the appropriate documentation first."
        )
    else:
        st.success("SUPPORTED · Evidence-backed response")
        st.subheader("Issue Interpretation")
        st.write(result.interpretation)
        st.subheader("Likely Cause")
        st.write(result.likely_cause)
        show_citations(result.cause_citation_ids, result.sources)
        st.subheader("Recommended Resolution")
        for number, step in enumerate(result.recommended_steps, 1):
            st.write(f"{number}. {step.text}")
            show_citations(step.citation_ids, result.sources)
        st.subheader("Sources")
        for source in result.sources:
            label = (
                "Synthetic resolved case"
                if source.source_type == "resolved_case"
                else "Demo documentation"
            )
            with st.expander(f"{label} · {source.title} · {source.section}"):
                st.caption(source.chunk_id)
                st.text(source.text)
                if source.source_refs:
                    st.caption("Based on documentation: " + ", ".join(source.source_refs))
                if urlparse(source.source_url).scheme in {"http", "https"}:
                    st.link_button("Open original source", source.source_url)
    with st.expander("Retrieved evidence and request details"):
        st.caption(
            f"Mode: {result.mode} · Model: {result.model} · "
            f"{result.latency_ms:.1f} ms · {result.context_characters:,} context characters"
        )
        if result.input_tokens is not None:
            st.caption(f"Provider tokens: {result.input_tokens} in / {result.output_tokens} out")
        if result.abstention_reason:
            st.caption("Abstention reason: " + result.abstention_reason)
        for hit in result.retrieved_evidence:
            st.caption(
                f"{hit.chunk.title} · {hit.chunk.section} · "
                + (f"cosine {hit.score:.3f}" if result.mode == "rag" else "Full-context source")
            )
            st.text(hit.chunk.text)


def main():
    st.markdown('<div class="hero-label">EVIDENCE BEFORE ANSWERS</div>', unsafe_allow_html=True)
    st.title("Verithra")
    st.markdown(
        '<p class="hero-description">AI Technical Support Resolution Assistant.<br>'
        "Describe an issue. Find relevant knowledge. Resolve it with traceable evidence.</p>",
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.header("Workspace")
        provider = st.radio("Run mode", ["Offline demo", "OpenAI"])
        demo = provider == "Offline demo"
        mode = st.radio("Evidence approach", ["RAG", "Full context"])
        st.caption(
            "RelayDesk is a fictional HTTP support service. Manuals are locally authored; "
            "all 24 cases are synthetic."
        )
        if demo:
            st.info(
                "Offline demo uses keyword-based vectors and copies evidence excerpts. "
                "It does not call an LLM or demonstrate learned semantic retrieval."
            )
        else:
            st.caption("Uses your configured OpenAI models. Credentials stay in the environment.")
        refresh = st.button("Build / refresh index", use_container_width=True)
        st.caption("OpenAI indexing sends source text to the embedding API and incurs usage.")
    try:
        settings = Settings.from_env()
        documents = load_knowledge(Path("data/raw"), Path("data/support_cases/cases.jsonl"))
        config = parameters(demo, settings)
        embedder, generator = clients(demo, settings)
        directory = index_directory(demo)
        if refresh or (demo and not (directory / "metadata.json").exists()):
            with st.spinner("Preparing the local knowledge index…"):
                index = build_index(
                    Path("data/raw"),
                    directory,
                    embedder,
                    config.chunk_size,
                    config.overlap,
                    Path("data/support_cases/cases.jsonl"),
                )
                index.save(directory, vars(config))
            st.sidebar.success("Knowledge index ready.")
            st.session_state.pop("resolution", None)
        if mode == "RAG":
            index = FaissIndex.load(directory)
            index.require_model(embedder.model)
        else:
            index = None
    except (VerithraError, OSError, ValueError) as exc:
        message = (
            str(exc)
            if isinstance(exc, VerithraError)
            else "Local data could not be loaded. Check corpus and configuration files."
        )
        st.error(message)
        st.stop()
    cols = st.columns(3)
    for col, label, value in zip(
        cols,
        ["Manuals", "Demo cases", "Mode"],
        [
            str(sum(d.source_type == "documentation" for d in documents)),
            str(sum(d.source_type == "resolved_case" for d in documents)),
            mode,
        ],
        strict=True,
    ):
        col.metric(label, value)
    st.caption(
        "Try: “401 during simultaneous refresh requests” "
        "or “Export job remains queued while API is healthy.”"
    )
    with st.form("issue_form"):
        question = st.text_area(
            "Describe your technical issue",
            placeholder="What happened, what did you expect, and which error did you see?",
            height=120,
            max_chars=4000,
        )
        submitted = st.form_submit_button(
            "Analyze Issue", type="primary", use_container_width=True, key="analyze_issue"
        )
    signature = (provider, mode)
    if st.session_state.get("signature") != signature:
        st.session_state.pop("resolution", None)
        st.session_state["signature"] = signature
    if submitted:
        try:
            with st.spinner("Finding evidence and analyzing your issue…"):
                pipeline = Pipeline(
                    index,
                    embedder,
                    generator,
                    config.top_k,
                    config.threshold,
                    settings.max_context_characters,
                )
                result = (
                    pipeline.ask(question)
                    if mode == "RAG"
                    else pipeline.full_context(
                        question,
                        documents,
                    )
                )
                st.session_state["resolution"] = result
        except (VerithraError, OSError, ValueError) as exc:
            st.session_state.pop("resolution", None)
            st.error(
                str(exc)
                if isinstance(exc, VerithraError)
                else "Unable to read local knowledge. Rebuild the index and try again."
            )
    if "resolution" in st.session_state:
        show_resolution(st.session_state["resolution"])
    else:
        st.caption(
            "Answers use supplied knowledge. If evidence is insufficient, Verithra abstains."
        )
    st.divider()
    st.caption(
        "RAG reduces hallucination risk; citation validity does not guarantee factual correctness. "
        "Review suggested changes before applying them."
    )


main()
