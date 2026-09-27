# CodeAnalyzer

A Python CLI and web tool that analyzes a codebase and generates an
AI-powered report with an architectural summary and code review flags —
built for the **IBM Bob 2.0 Hackathon**.

## What it does

Point it at any folder or file, and it produces a Markdown report with:

- **Summary** — a plain-English explanation of what the codebase does and how it's structured.
- **Code Review** — refactoring opportunities and potential bug risks, referenced per file.

## Architecture

```
file_walker.py      → reads and filters source files (size limit, binary skip)
prompt_builder.py    → assembles the LLM prompt (supports --lang en/es)
watsonx_client.py    → IBM watsonx.ai / Granite provider (with mock fallback)
groq_client.py       → Groq provider (live inference)
parser.py            → extracts Summary + Code Review from the LLM response
analyze.py           → CLI entrypoint
app.py               → Streamlit web UI
```


## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and fill in credentials for whichever
provider you want to use:
```
WATSONX_API_KEY=your_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com

GROQ_API_KEY=your_key_here
```


**No credentials?** The tool automatically falls back to a **mock mode**
that simulates the model's response, so the full pipeline can still be
tested end-to-end without any network access.

## Usage

### Command line
```bash
python analyze.py <path> --provider [watsonx|groq] --output report.md
```

### Web interface
```bash
streamlit run app.py
```

## Built with IBM Bob 2.0

Designed in Bob's **Plan mode**, implemented in **Agent mode**, with Git
commits after each step. See `/screenshots` for session evidence.

## Notes

IBM watsonx.ai access could not be provisioned during the hackathon due
to an IBM Cloud verification issue. Groq was integrated as a live
secondary provider so the tool always has a working path to real LLM
inference, while watsonx support remains fully implemented.
