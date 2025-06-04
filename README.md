# Wellness Timeline Assistant

The **Wellness Timeline Assistant** is an AI-powered tool that generates a weekly summary of health and wellness trends, social buzz, and research insights. It aggregates data from Google Trends, Twitter (X), Reddit, Google Scholar, Arxiv, and PubMed, and produces a user-friendly PDF and HTML report.

---

## Features
- **Aggregates wellness trends** from Google Trends
- **Fetches top social buzz** from Twitter (X) and Reddit
- **Summarizes recent research** from Arxiv, PubMed, Google Scholar, and Semantic Scholar
- **Generates a structured, readable summary** in both PDF and HTML formats
- **No domain expertise required** to understand the output

---

## Setup & Installation

1. **Clone the repository** and navigate to the project directory.
2. **Install dependencies** (preferably in a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```
3. **Install [wkhtmltopdf](https://wkhtmltopdf.org/downloads.html)** (required for PDF generation):
   - On Windows, ensure the path to `wkhtmltopdf.exe` matches the one in `main.py` (default: `C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe`).

4. **Set up environment variables**:
   - Copy `.env` to your project root or `venv/` directory and fill in the required API keys:
     - `OPENROUTER_API_KEY` (for OpenRouter/LLM)
     - `OPENAI_API_KEY` (for OpenAI/LLM)
     - `X_BEARER_TOKEN` (for Twitter/X API)
     - `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` (for Reddit API)
     - `SERP_API_KEY` (for SerpAPI/Google Scholar)

---

## Usage

From the `venv/` directory, run:
```bash
python main.py
```

- The script will automatically fetch data for the last 7 days.
- Outputs:
  - `wellness_summary.html` — a styled HTML summary
  - `wellness_summary.pdf` — a printable PDF summary

---

## Output Example
- **Trends**: Top 5 rising wellness topics from Google Trends
- **Social Buzz**: Top posts from Twitter/X and Reddit
- **Research Insights**: Summaries of recent academic papers
- **Lifestyle Recommendations**: AI-generated, based on real data
- **Future Outlook**: AI-generated, based on real data

---

## Dependencies
See `requirements.txt` for the full list. Key packages:
- `langchain`, `langchain-core`, `langchain-openai`
- `openai`, `requests`, `serpapi`, `praw`, `pytrends`
- `arxiv`, `biopython`, `pdfkit`, `python-dotenv`, `pydantic`
- `beautifulsoup4`, `lxml`, `pandas`

---

## Environment Variables
Example `.env` file:
```
OPENROUTER_API_KEY=your_openrouter_key
OPENAI_API_KEY=your_openai_key
X_BEARER_TOKEN=your_twitter_bearer_token
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
SERP_API_KEY=your_serpapi_key
```

---

## Notes
- **API Quotas**: Ensure your API keys have sufficient quota.
- **PDF Generation**: If PDF output fails, check your `wkhtmltopdf` installation and path.
- **Customization**: You can modify the time window or add more wellness sources in `main.py` and `tools.py`.

