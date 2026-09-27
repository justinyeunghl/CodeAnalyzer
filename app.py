"""Streamlit web interface for CodeAnalyzer."""

import os
import subprocess
import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Streamlit Cloud exposes secrets only via st.secrets, not as OS env vars.
# Copy each secret into os.environ so the analyze.py subprocess inherits them.
# ---------------------------------------------------------------------------
for _key in ["GROQ_API_KEY", "WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL"]:
    if _key in st.secrets:
        os.environ[_key] = st.secrets[_key]

# DEBUG — remove once secrets wiring is confirmed
st.write(f"DEBUG: GROQ_API_KEY in st.secrets: {'GROQ_API_KEY' in st.secrets}")
st.write(f"DEBUG: GROQ_API_KEY in os.environ: {'GROQ_API_KEY' in os.environ}")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CodeAnalyzer",
    page_icon="🔍",
    layout="wide",
)

REPORT_FILE = Path(__file__).parent / "report.md"

# ---------------------------------------------------------------------------
# Sidebar — inputs
# ---------------------------------------------------------------------------
st.sidebar.title("⚙️ Configuration")

target_path = st.sidebar.text_input(
    "Target project directory",
    value=".",
    help="Relative or absolute path to the directory (or file) to analyse.",
)

provider = st.sidebar.selectbox(
    "Provider",
    options=["watsonx", "groq"],
    index=0,
    help="LLM provider to use for analysis.",
)

lang_label = st.sidebar.selectbox(
    "Output language",
    options=["English", "Spanish"],
    index=0,
)
lang_code = "en" if lang_label == "English" else "es"

st.sidebar.markdown("---")
run_button = st.sidebar.button("🚀 Run Code Analysis", use_container_width=True)

# ---------------------------------------------------------------------------
# Main area — header
# ---------------------------------------------------------------------------
st.title("🔍 CodeAnalyzer")
st.caption("Powered by IBM watsonx.ai · Groq · IBM Bob 2.0 Hackathon")
st.markdown("---")

# ---------------------------------------------------------------------------
# Run analysis when button is clicked
# ---------------------------------------------------------------------------
if run_button:
    if not target_path.strip():
        st.error("Please enter a target directory path in the sidebar.")
    else:
        cmd = [
            sys.executable,          # same Python interpreter running Streamlit
            "analyze.py",
            target_path.strip(),
            "--provider", provider,
            "--lang", lang_code,
            "--output", str(REPORT_FILE),
        ]

        with st.spinner(f"Analysing `{target_path}` with **{provider}** ({lang_label})…"):
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=Path(__file__).parent,  # run from codeanalyzer/ so imports resolve
            )

        # Show stdout (progress lines, MOCK MODE notices, SKIP warnings)
        stdout_text = result.stdout or ""
        stderr_text = result.stderr or ""
        if stdout_text.strip():
            with st.expander("📋 Analysis log", expanded=False):
                st.code(stdout_text.strip(), language=None)

        if result.returncode != 0:
            st.error("Analysis failed. See details below.")
            if stderr_text.strip():
                st.code(stderr_text.strip(), language=None)
        else:
            st.success("Analysis complete!")

# ---------------------------------------------------------------------------
# Display report
# ---------------------------------------------------------------------------
if REPORT_FILE.exists():
    try:
        report_text = REPORT_FILE.read_text(encoding="utf-8")
        st.markdown(report_text)
    except OSError as exc:
        st.error(f"Could not read report file: {exc}")
elif not run_button:
    st.info("Configure your options in the sidebar and click **🚀 Run Code Analysis** to get started.")
