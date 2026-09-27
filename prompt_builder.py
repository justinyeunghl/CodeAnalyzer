"""Assembles file content records into a structured prompt string for the LLM."""

# Maps --lang codes to a short instruction fragment injected into the preamble.
_LANG_INSTRUCTIONS = {
    "en": "Write your response in English.",
    "es": "Escribe tu respuesta en español.",
}


def build_prompt(files: list[dict], lang: str = "en") -> str:
    """Build a prompt string instructing the LLM to produce a summary and code review.

    Args:
        files: A list of dicts with keys "path" (str) and "content" (str), as
               returned by file_walker.walk().
        lang:  Two-letter language code ("en" or "es"). Controls the language
               of the generated summary and code review text. Defaults to "en".

    Returns:
        A single prompt string containing an instruction preamble, all file
        contents with separator headers, and a closing instruction.
    """
    lang_instruction = _LANG_INSTRUCTIONS.get(lang, _LANG_INSTRUCTIONS["en"])

    preamble = f"""\
You are an expert software engineer performing a code review.
{lang_instruction}
Analyse the source files provided below and respond with exactly two Markdown sections:

## Summary
Explain the overall purpose and high-level architecture of the codebase in plain English.

## Code Review
A bullet list of refactoring opportunities and bug risks. Each bullet must reference
the specific file it applies to (e.g. "- **file_walker.py**: ...").

Do not include any other sections or commentary outside these two headings.
"""

    file_blocks = []
    for f in files:
        content = f["content"][:1500]
        block = f"### File: {f['path']}\n{content}"
        file_blocks.append(block)

    files_section = "\n\n".join(file_blocks)

    closing = (
        "\n\nRespond using exactly the headings "
        "`## Summary` and `## Code Review` as shown above."
    )

    return preamble + "\n" + files_section + closing
