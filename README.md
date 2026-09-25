# codeanalyzer

A Python CLI tool that reads a file or directory of source code and produces a combined report using IBM watsonx.ai, including an architectural summary and a list of code review flags (refactoring opportunities and bug risks).

## Prerequisites

- Python 3.9 or higher
- An IBM watsonx.ai account with an API key, project ID, and regional URL

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd codeanalyzer
   ```

2. **Create your `.env` file from the example:**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in your credentials:
   ```
   WATSONX_API_KEY=<your api key>
   WATSONX_PROJECT_ID=<your project id>
   WATSONX_URL=https://us-south.ml.cloud.ibm.com
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Analyze a directory and print the report to the terminal:
```bash
python analyze.py ./myproject
```

Analyze a directory and also save the report as a Markdown file:
```bash
python analyze.py ./myproject --output report.md
```

For full usage help:
```bash
python analyze.py --help
```
