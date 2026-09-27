"""Wraps the Groq inference API using the openai-compatible client."""

import os

from openai import OpenAI, APIError, APIConnectionError

# ---------------------------------------------------------------------------
# Constants — tune model behaviour here without touching call logic
# ---------------------------------------------------------------------------
MODEL_ID = "openai/gpt-oss-20b"

# Sentinel value matching the placeholder in .env.example
_DUMMY_API_KEY = "your_groq_api_key_here"

_MOCK_RESPONSE = """\
## Summary
This is a **mock response** from the CodeAnalyzer demo mode (Groq not reached).

The analysed codebase appears to be a Python CLI tool structured as a pipeline of independent \
modules: a file walker that collects source files, a prompt builder that assembles them into an \
LLM instruction, a provider client that calls the chosen model, and a parser that extracts \
structured sections from the response. The entrypoint wires all modules together and supports \
optional Markdown report output via --output.

## Code Review
- **General**: No real analysis was performed — set a valid `GROQ_API_KEY` in your `.env` \
file to enable live Groq inference.
- **analyze.py**: The `--provider` flag makes it easy to switch between watsonx and Groq \
at runtime; ensure both clients handle errors consistently.
- **groq_client.py**: For production use, consider handling quota/rate-limit errors \
(HTTP 429) with an exponential back-off retry.
- **prompt_builder.py**: The `--lang` flag delegates language selection to the model; \
verify that heading names remain in English so the parser can still split on them reliably.
"""


def generate(prompt: str) -> str:
    """Send a prompt to the Groq API and return the generated text.

    Reads GROQ_API_KEY from the environment (expected to have been
    populated by load_dotenv() in the CLI entrypoint before this function
    is called).

    If GROQ_API_KEY is absent or set to the placeholder value from
    .env.example, the function prints a warning and returns a simulated
    Markdown response instead of making a real API call.

    Args:
        prompt: The full prompt string to send to the model.

    Returns:
        The generated text from the Groq response,
        or a simulated response when running in mock mode.
    """
    api_key = os.environ.get("GROQ_API_KEY")

    # ------------------------------------------------------------------
    # Mock mode: no key provided, or still using the placeholder value
    # ------------------------------------------------------------------
    if not api_key or api_key == _DUMMY_API_KEY:
        print("[MOCK MODE] GROQ_API_KEY not set — returning simulated response.")
        return _MOCK_RESPONSE

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except APIConnectionError as exc:
        print(f"Groq connection error: {exc}")
        return ""
    except APIError as exc:
        print(f"Groq APIError: {exc}")
        return ""
