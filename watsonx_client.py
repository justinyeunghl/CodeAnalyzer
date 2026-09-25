"""Wraps the IBM watsonx.ai text generation API, including IAM token exchange."""

import os

import requests

# ---------------------------------------------------------------------------
# Constants — tune model behaviour here without touching call logic
# ---------------------------------------------------------------------------
MODEL_ID = "ibm/granite-13b-instruct-v2"
MAX_NEW_TOKENS = 1024
TEMPERATURE = 0.2

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
GENERATION_API_PATH = "/ml/v1/text/generation"
API_VERSION = "2023-05-29"

# Sentinel value copied from .env.example — treated as "no real key provided"
_DUMMY_API_KEY = "your_api_key_here"

_MOCK_RESPONSE = """\
## Summary
This is a **mock response** from the CodeAnalyzer demo mode (ibm/granite-13b-instruct-v2 not reached).

The analysed codebase appears to be a Python CLI tool. It is structured as a pipeline of \
independent modules: a file walker that collects source files, a prompt builder that assembles \
them into an LLM instruction, a watsonx client that calls the IBM Granite model, and a parser \
that extracts structured sections from the response. The entrypoint wires all modules together \
and supports optional Markdown report output via --output.

## Code Review
- **General**: No real analysis was performed — set a valid `WATSONX_API_KEY` in your `.env` \
file to enable live Granite inference.
- **analyze.py**: Consider adding a `--version` flag to expose the tool version for demo purposes.
- **file_walker.py**: The 50 KB per-file limit is intentionally conservative; large minified \
files or data files will be skipped with a printed warning.
- **watsonx_client.py**: IAM tokens are short-lived (~60 min). For high-volume usage, \
cache the token and refresh only when expired rather than fetching a new one per call.
- **prompt_builder.py**: If the total prompt exceeds the model context window, \
consider chunking files and summarising them incrementally.
"""


def _get_iam_token(api_key: str) -> str:
    """Exchange an IBM Cloud API key for a short-lived IAM bearer token.

    Args:
        api_key: IBM Cloud API key (value of WATSONX_API_KEY).

    Returns:
        The IAM access token string.

    Raises:
        requests.HTTPError: if the IAM endpoint returns a non-2xx status.
    """
    response = requests.post(
        IAM_TOKEN_URL,
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


def generate(prompt: str) -> str:
    """Send a prompt to watsonx.ai and return the generated text.

    Reads WATSONX_API_KEY, WATSONX_PROJECT_ID, and WATSONX_URL from the
    environment (expected to have been populated by load_dotenv() in the
    CLI entrypoint before this function is called).

    If WATSONX_API_KEY is absent or set to the placeholder value from
    .env.example, the function prints a warning and returns a simulated
    Granite Markdown response instead of making a real API call.  This
    allows the full pipeline (including the parser and report output) to
    be exercised without live credentials.

    Args:
        prompt: The full prompt string to send to the model.

    Returns:
        The generated text from the first result in the API response,
        or a simulated response when running in mock mode.

    Raises:
        RuntimeError: if PROJECT_ID or URL are missing in live mode.
        requests.HTTPError: if either the IAM or generation API call fails.
    """
    api_key = os.getenv("WATSONX_API_KEY")

    # ------------------------------------------------------------------
    # Mock mode: no key provided, or still using the placeholder value
    # ------------------------------------------------------------------
    if not api_key or api_key == _DUMMY_API_KEY:
        print("[MOCK MODE] WATSONX_API_KEY not set — returning simulated response.")
        return _MOCK_RESPONSE

    project_id = os.getenv("WATSONX_PROJECT_ID")
    watsonx_url = os.getenv("WATSONX_URL")

    missing = [name for name, val in (
        ("WATSONX_PROJECT_ID", project_id),
        ("WATSONX_URL", watsonx_url),
    ) if val is None]

    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Copy .env.example to .env and fill in your credentials."
        )

    token = _get_iam_token(api_key)

    url = f"{watsonx_url}{GENERATION_API_PATH}?version={API_VERSION}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "model_id": MODEL_ID,
        "project_id": project_id,
        "input": prompt,
        "parameters": {
            "max_new_tokens": MAX_NEW_TOKENS,
            "temperature": TEMPERATURE,
        },
    }

    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()["results"][0]["generated_text"]
