# CodeAnalyzer — Plan

## Top-Level Overview

Build a Python CLI tool called `codeanalyzer` that accepts a file or directory path, reads the source code inside it, and produces a combined report containing:

1. **Architectural summary** — a plain-English explanation of what the codebase does and how it is structured.
2. **Code review flags** — a list of identified refactoring opportunities and bug risks.

The tool uses IBM watsonx.ai as the LLM backend. Output is printed to the terminal by default, with an optional `--output <file.md>` flag to also save a Markdown report. Credentials are loaded from a `.env` file.

**Non-goals for this scope:**
- Language-specific AST parsing (all files treated as plain text)
- Diff-based review (no Git integration in this phase)
- Multi-file context linking / cross-reference analysis

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffolding & Credential Setup

**Status:** `[x] done`

**Intent:**
Establish the project folder structure, dependency manifest, and credential wiring before any logic is written. This ensures the project is Git-ready from the start and credentials are never hardcoded.

**Expected Outcomes:**
- `codeanalyzer/` folder exists with the correct module layout.
- `requirements.txt` lists all dependencies.
- `.env.example` documents the required keys.
- `.gitignore` excludes `.env` and `__pycache__`.
- `README.md` contains setup instructions.

**Todo List:**
1. Create folder structure:
   ```
   codeanalyzer/
   ├── analyze.py            ← CLI entrypoint
   ├── file_walker.py        ← file reading logic
   ├── prompt_builder.py     ← prompt assembly
   ├── watsonx_client.py     ← API call wrapper
   ├── parser.py             ← response parsing
   ├── requirements.txt
   ├── .env.example
   ├── .gitignore
   └── README.md
   ```
2. Populate `requirements.txt` with: `requests`, `python-dotenv`, `argparse` (stdlib — no install needed).
3. Write `.env.example` with placeholder keys: `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`.
4. Write `.gitignore` to exclude `.env`, `__pycache__/`, `*.pyc`, and any generated output files.
5. Write `README.md` with: project description, setup steps (clone → create `.env` → `pip install -r requirements.txt` → run), and example usage.

**Relevant Context:**
- Credentials needed: `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL` (the regional endpoint, e.g. `https://us-south.ml.cloud.ibm.com`).
- Use the `python-dotenv` library to load `.env` at runtime via `load_dotenv()`.

---

### Sub-Task 2 — File Walker (`file_walker.py`)

**Status:** `[x] done`

**Intent:**
Implement the module responsible for traversing a directory (or reading a single file) and returning a list of file content records. This is the data ingestion layer — everything downstream depends on its output.

**Expected Outcomes:**
- `walk(path: str) -> list[dict]` function exists and works correctly.
- Files larger than 50 KB are skipped with a printed warning.
- Binary files (images, compiled artifacts) are skipped silently.
- Each returned record contains the file path and its text content.

**Todo List:**
1. Implement `walk(path)`:
   - If `path` is a file, read it (subject to size check) and return a single-item list.
   - If `path` is a directory, use `os.walk()` to recursively collect all files.
2. For each file:
   - Check file size with `os.path.getsize()`. If > 50 KB (51,200 bytes), print a warning and skip.
   - Attempt to read as UTF-8 text. If a `UnicodeDecodeError` is raised, skip (binary file).
3. Return a list of dicts in the shape: `{"path": str, "content": str}`.

**Relevant Context:**
- Python note for Java/C++ background: Python's `os.walk()` is a generator — it lazily yields `(dirpath, dirnames, filenames)` tuples as you iterate. No equivalent of Java's `File.listFiles()` recursion is needed.
- No third-party libraries required — `os` is part of Python's standard library.

---

### Sub-Task 3 — Prompt Builder (`prompt_builder.py`)

**Status:** `[x] done`

**Intent:**
Assemble the list of file content records into a single, well-structured prompt string that instructs watsonx.ai to produce both a summary and a code review in one response. Good prompt design here directly determines output quality.

**Expected Outcomes:**
- `build_prompt(files: list[dict]) -> str` function exists.
- The prompt clearly requests both a summary section and a code review section.
- The prompt includes all file contents concatenated with clear file path headers.
- The output format requested from the LLM is specified in the prompt (Markdown with headings).

**Todo List:**
1. Design the prompt template with two explicit sections requested from the LLM:
   - `## Summary` — explain the purpose and architecture of the codebase.
   - `## Code Review` — list refactoring opportunities and bug risks as a bullet list, each with a file reference.
2. Prepend each file's content block with a separator header like `### File: <path>`.
3. Concatenate all file blocks and append them after the instruction preamble.
4. Return the complete prompt string.

**Relevant Context:**
- Python note: Python uses multi-line strings with triple quotes (`"""..."""`) — equivalent to Java's text blocks (available since Java 15) or C++ raw string literals. Ideal for prompt templates.
- Keep the instruction preamble concise. The LLM performs better with clear, direct instructions.

---

### Sub-Task 4 — watsonx Client (`watsonx_client.py`)

**Status:** `[x] done`

**Intent:**
Wrap the IBM watsonx.ai text generation REST API call. This module handles credential loading, token exchange (IBM IAM), request construction, and returning the raw LLM response text.

**Expected Outcomes:**
- `generate(prompt: str) -> str` function exists.
- IBM IAM bearer token is obtained from `WATSONX_API_KEY` before the main API call.
- The call targets the `/ml/v1/text/generation` endpoint on the configured `WATSONX_URL`.
- HTTP errors cause a clear, informative exception to be raised.
- Model ID and generation parameters (max tokens, temperature) are defined as constants at the top of the file for easy tuning.

**Todo List:**
1. Load `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL` from environment using `os.getenv()` (after `load_dotenv()` has been called in the entrypoint).
2. Implement `_get_iam_token(api_key: str) -> str`:
   - POST to `https://iam.cloud.ibm.com/identity/token` with `grant_type=urn:ibm:params:oauth:grant-type:apikey` and `apikey=<api_key>`.
   - Return the `access_token` from the JSON response.
3. Implement `generate(prompt: str) -> str`:
   - Call `_get_iam_token()` to get a fresh bearer token.
   - POST to `{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29`.
   - Request body: `model_id`, `project_id`, `input` (the prompt), and `parameters` (e.g. `max_new_tokens: 1024`).
   - Return the generated text from `response["results"][0]["generated_text"]`.
4. Use `response.raise_for_status()` on all HTTP responses to surface API errors immediately.

**Relevant Context:**
- Python note: Python's `requests` library is the standard HTTP client (equivalent to Java's `HttpClient` or C++ libcurl). `requests.post(url, json=body, headers=headers)` sends a JSON POST — no manual serialization needed.
- Recommended model: `ibm/granite-13b-instruct-v2` (strong for code tasks, available on watsonx.ai).
- IBM IAM token endpoint: `https://iam.cloud.ibm.com/identity/token`.
- watsonx.ai generation API reference: `POST /ml/v1/text/generation?version=2023-05-29`.

---

### Sub-Task 5 — Response Parser (`parser.py`)

**Status:** `[x] done`

**Intent:**
Extract structured data from the raw LLM response text. Since the prompt instructs the LLM to respond in Markdown with `## Summary` and `## Code Review` sections, the parser splits on those headings to produce a clean dict.

**Expected Outcomes:**
- `parse(raw: str) -> dict` function exists.
- Returns a dict with keys `"summary"` and `"code_review"`, each containing the respective section text.
- If a section is missing from the response (LLM didn't follow format), the value falls back to a meaningful default string rather than crashing.

**Todo List:**
1. Implement `parse(raw: str) -> dict`:
   - Split the raw response on `## Summary` and `## Code Review` headings using simple string operations.
   - Strip leading/trailing whitespace from each section.
   - Return `{"summary": <text>, "code_review": <text>}`.
2. Handle the fallback case: if a heading is not found, set the corresponding value to `"(section not found in response)"`.

**Relevant Context:**
- Python note: Python string splitting (`str.split()`, `str.partition()`) and slicing are more expressive than Java/C++ equivalents. No regex is needed here — simple string operations are sufficient and more readable.

---

### Sub-Task 6 — CLI Entrypoint (`analyze.py`)

**Status:** `[x] done`

**Intent:**
Wire all modules together into a runnable CLI. This is the file the user executes. It handles argument parsing, orchestrates the pipeline, prints results to the terminal, and optionally saves a Markdown report.

**Expected Outcomes:**
- `python analyze.py <path>` runs the full pipeline and prints results.
- `python analyze.py <path> --output report.md` also saves a Markdown file.
- A `--help` flag prints usage instructions automatically (via `argparse`).
- If no files are found (empty directory, all files skipped), the tool exits with a helpful message.

**Todo List:**
1. Use `argparse` to define:
   - Positional argument: `path` (the file or directory to analyze).
   - Optional argument: `--output <filename>` (path to save the Markdown report).
2. Call `load_dotenv()` at startup to populate environment variables from `.env`.
3. Orchestrate the pipeline in order:
   1. `file_walker.walk(path)` → list of file records.
   2. Guard: if list is empty, print an error and exit.
   3. `prompt_builder.build_prompt(files)` → prompt string.
   4. `watsonx_client.generate(prompt)` → raw LLM response.
   5. `parser.parse(raw)` → structured dict.
4. Print the summary and code review sections to the terminal with clear formatting.
5. If `--output` was provided, write the full Markdown report to the specified file.

**Relevant Context:**
- Python note: `argparse` is part of the standard library — no install needed. It auto-generates `--help` output from the argument definitions, similar in spirit to Java's Apache Commons CLI but built in.
- Python note: `if __name__ == "__main__":` is the Python idiom for "run this block only when executed directly, not when imported." It is equivalent to Java's `public static void main(String[] args)` as a guarded entrypoint.

---

## Dependency Map

```
analyze.py
  ├── file_walker.py      (no internal dependencies)
  ├── prompt_builder.py   (no internal dependencies)
  ├── watsonx_client.py   (no internal dependencies)
  └── parser.py           (no internal dependencies)
```

All five modules are independent of each other — only `analyze.py` imports from them. This means each sub-task can be implemented and tested in isolation.

---

## Implementation Order

Sub-tasks are ordered to build on a stable foundation:

1. Scaffolding (structure + credentials) → enables everything else
2. File Walker → produces data for manual testing
3. Prompt Builder → can be tested standalone with mock file data
4. watsonx Client → tested once credentials are set up
5. Parser → tested against a pasted sample LLM response
6. CLI Entrypoint → final integration, wires all modules

---

## Key Python Concepts Used

| Concept | Where Used | Java/C++ Equivalent |
|---|---|---|
| `if __name__ == "__main__":` | `analyze.py` | `public static void main()` |
| `os.walk()` generator | `file_walker.py` | Recursive `File.listFiles()` |
| Triple-quoted strings | `prompt_builder.py` | Text blocks / raw string literals |
| `requests.post()` | `watsonx_client.py` | `HttpClient.send()` / libcurl |
| `str.partition()` | `parser.py` | `String.split()` |
| `python-dotenv` | `analyze.py` | Environment variable loading |
| `argparse` | `analyze.py` | Apache Commons CLI / getopt |
