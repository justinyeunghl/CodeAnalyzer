"""Extracts the Summary and Code Review sections from the raw LLM response text."""

_FALLBACK_SUMMARY = "(summary not found in response)"
_FALLBACK_REVIEW = "(code review not found in response)"


def parse(raw: str) -> dict:
    """Parse the raw generated text returned by watsonx_client.generate().

    The function expects the LLM to have responded with two Markdown sections:
      ## Summary
      ## Code Review

    It uses str.partition() to split on each heading and returns the content
    that falls between (and after) them.  If either heading is absent, the
    corresponding value is set to the fallback string rather than raising an
    exception.

    Args:
        raw: Raw text string returned by the LLM.

    Returns:
        A dict with exactly two keys:
          "summary"     - text between ## Summary and ## Code Review, stripped.
          "code_review" - text after ## Code Review, stripped.
        Either value is a section-specific fallback string when the heading is
        missing from the raw text.
    """
    _, summary_sep, after_summary = raw.partition("## Summary")
    summary_raw, review_sep, after_review = after_summary.partition("## Code Review")

    summary = summary_raw.strip() if summary_sep else _FALLBACK_SUMMARY
    code_review = after_review.strip() if review_sep else _FALLBACK_REVIEW

    return {"summary": summary, "code_review": code_review}
