"""CLI entrypoint: parses arguments, loads credentials, and orchestrates the analysis pipeline."""

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

# Load .env relative to this file so subprocess invocations from any CWD
# still pick up credentials before any client module reads os.environ.
load_dotenv(Path(__file__).parent / ".env")

import file_walker
import groq_client
import prompt_builder
import watsonx_client
import parser

SEP = "=" * 60

_PROVIDERS = {
    "watsonx": watsonx_client.generate,
    "groq": groq_client.generate,
}


def main():
    """Parse CLI arguments and run the full analysis pipeline."""

    arg_parser = argparse.ArgumentParser(
        description="Analyse a codebase and generate a summary and code review."
    )
    arg_parser.add_argument("path", help="File or directory to analyse.")
    arg_parser.add_argument("--output", metavar="FILE", help="Save the Markdown report to FILE.")
    arg_parser.add_argument(
        "--provider",
        choices=["watsonx", "groq"],
        default="watsonx",
        help="LLM provider to use (default: watsonx).",
    )
    arg_parser.add_argument(
        "--lang",
        choices=["en", "es"],
        default="en",
        help="Language for the generated report (default: en).",
    )

    args = arg_parser.parse_args()

    files = file_walker.walk(args.path)
    if not files:
        print("No readable files found in the given path.")
        sys.exit(1)

    print(f"Analysing {len(files)} file(s) with {args.provider}...")

    generate = _PROVIDERS[args.provider]
    raw = generate(prompt_builder.build_prompt(files, lang=args.lang))
    result = parser.parse(raw)

    print(SEP)
    print("SUMMARY")
    print(SEP)
    print(result["summary"])
    print()
    print(SEP)
    print("CODE REVIEW")
    print(SEP)
    print(result["code_review"])

    if args.output:
        report = (
            "# CodeAnalyzer Report\n\n"
            "## Summary\n\n"
            f"{result['summary']}\n\n"
            "## Code Review\n\n"
            f"{result['code_review']}\n"
        )
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
