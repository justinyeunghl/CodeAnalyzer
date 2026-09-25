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

    Args:
        prompt: The full prompt string to send to the model.

    Returns:
        The generated text from the first result in the API response.

    Raises:
        RuntimeError: if any required environment variable is missing.
        requests.HTTPError: if either the IAM or generation API call fails.
    """
    api_key = os.getenv("WATSONX_API_KEY")
    project_id = os.getenv("WATSONX_PROJECT_ID")
    watsonx_url = os.getenv("WATSONX_URL")

    missing = [name for name, val in (
        ("WATSONX_API_KEY", api_key),
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
