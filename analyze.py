"""CLI entrypoint: parses arguments, loads credentials, and orchestrates the analysis pipeline."""

import argparse
import sys

from dotenv import load_dotenv

import file_walker
import prompt_builder
import watsonx_client
import parser

SEP = "=" * 60


def main():
    """Parse CLI arguments and run the full analysis pipeline."""
    load_dotenv()

    arg_parser = argparse.ArgumentParser(
        description="Analyse a codebase and generate a summary and code review using IBM watsonx.ai."
    )
    arg_parser.add_argument("path", help="File or directory to analyse.")
    arg_parser.add_argument("--output", metavar="FILE", help="Save the Markdown report to FILE.")

    args = arg_parser.parse_args()

    files = file_walker.walk(args.path)
    if not files:
        print("No readable files found in the given path.")
        sys.exit(1)

    print(f"Analysing {len(files)} file(s) with watsonx.ai...")

    raw = watsonx_client.generate(prompt_builder.build_prompt(files))
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
