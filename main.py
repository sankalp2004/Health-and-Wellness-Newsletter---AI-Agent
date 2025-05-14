import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from tools import wellness_tools
from dotenv import load_dotenv
import pdfkit
import warnings
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool

from pydantic import BaseModel, Field
from typing import List

load_dotenv()
warnings.filterwarnings("ignore")

os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")



class WellnessInsight(BaseModel):
    date: str = Field(description="Date in YYYY-MM-DD")
    title: str = Field(description="Brief title of the insight")
    description: str = Field(description="Detailed explanation of the wellness insight")
    impact: str = Field(description="Why this insight matters for wellness")
    source: str = Field(description="Source of the insight")
    category: str = Field(description="Area of wellness (e.g., Nutrition, Exercise, Mental Health, Sleep, Longevity)")

class WellnessSummary(BaseModel):
    time_period: str
    popular_trends: List[str]
    social_buzz: List[str]
    notable_insights: List[WellnessInsight]
    lifestyle_recommendations: str
    future_outlook: str


def get_llm(temperature=0.6):
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        model="mistralai/mistral-small-3.1-24b-instruct:free",
        temperature=temperature
    )

def generate_email_html_from_summary(summary: dict) -> str:
    def clean_url(url):
        if url and not url.startswith(('http://', 'https://')):
            return 'https://' + url
        return url

    return f"""
    <html>
    <head>
        <meta charset='UTF-8'>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; padding: 30px; color: #333; line-height: 1.6; }}
            h1 {{ color: #34a853; }}
            h2 {{ border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
            .section {{ margin-bottom: 30px; }}
            .insight {{ margin-bottom: 20px; }}
            a {{ color: #34a853; text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>🌿 Wellness Digest: {summary['time_period']}</h1>

        <div class='section'><h2>📈 What's Trending Online</h2>
        <ul>
            {''.join(f"<li><strong>{trend.split(':')[0]}</strong>: {trend.split(':')[1]}</li>" if ':' in trend else f"<li>{trend}</li>" for trend in summary['popular_trends'])}
        </ul>
        </div>

        <div class='section'><h2>💬 What People Are Saying</h2>
        <ul>
            {''.join(f"<li>{buzz}</li>" for buzz in summary['social_buzz'])}
        </ul></div>

        <div class='section'><h2>📚 What Research Says</h2>
            {''.join(f"""
            <div class='insight'>
                <strong>{insight['date']} - {insight['title']}</strong>
                <p>{insight['description']}</p>
                <p><em>Impact:</em> {insight['impact']}</p>
                <p><strong>Category:</strong> {insight['category']}</p>
                <p><strong>Source:</strong> <a href="{clean_url(insight['source'])}" target="_blank" rel="noopener noreferrer">{clean_url(insight['source'])}</a></p>
            </div>
            """ for insight in summary['notable_insights'])}
        </div>

        <div class='section'><h2>🧠 Recommendations</h2><p>{summary['lifestyle_recommendations']}</p></div>
        <div class='section'><h2>🌟 Wellness in the Spotlight</h2><p>{summary['future_outlook']}</p></div>
    </body>
    </html>
    """

def save_summary_pdf(summary: dict, filename="wellness_summary.pdf"):
    html = generate_email_html_from_summary(summary)
    config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    pdfkit.from_string(html, filename, configuration=config)


def get_last_week_date_range():
    today = datetime.today()
    start_date = today - timedelta(days=7)
    return start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')

def extract_clean_output(result):
    """Extract and clean tool output from executor result."""
    if isinstance(result, dict) and "output" in result:
        output = result["output"].strip()
        # Remove markdown-style json code block markers if present
        if output.startswith("```json"):
            output = output.replace("```json", "").replace("```", "").strip()
        return output
    return ""

def main():
    print("Wellness Timeline Assistant")

    start_date_str, end_date_str = get_last_week_date_range()

    llm = get_llm()
    parser = PydanticOutputParser(pydantic_object=WellnessSummary)

    format_instructions = parser.get_format_instructions()
    safe_format_instructions = format_instructions.replace("{", "{{").replace("}", "}}")

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""
        You are a Wellness Timeline Generator.

        Your task is to generate a structured wellness summary based strictly on real data retrieved from tools. You may use creativity and engaging language **only in how the summary is written**, but **not in the factual content** (e.g., trends, tweets, Reddit posts, research papers).

        ONLY use the following tools to generate content**:
        1. `GetWellnessTrends` — for Google Trends data
        2. `GetSocialBuzzPosts` — for top tweets/X posts
        3. `GetRedditWellnessDiscussions` — for Reddit posts
        4. `GetResearchPapers` — for research-backed insights

        Do NOT fabricate or assume information from other platforms like TikTok, Pinterest, or HubSpot unless the tools return that data explicitly.

        Time Period**: {start_date_str} to {end_date_str}

        IMPORTANT: You must return your response as a single JSON string that matches this exact structure:
        {{{{
            "time_period": "string (e.g., 'Last Week')",
            "popular_trends": ["string", "string", ...],
            "social_buzz": ["string", "string", ...],
            "notable_insights": [
                {{{{
                    "date": "YYYY-MM-DD",
                    "title": "string",
                    "description": "string",
                    "impact": "string",
                    "source": "string",
                    "category": "string"
                }}}},
                ...
            ],
            "lifestyle_recommendations": "string",
            "future_outlook": "string"
        }}}}

        Do not include any additional text or formatting. Return ONLY the JSON string.

        {{agent_scratchpad}}
        """),
        ("human", "Generate the wellness summary.")
    ])

    agent = create_tool_calling_agent(llm=llm, prompt=prompt, tools=wellness_tools)
    executor = AgentExecutor(agent=agent, tools=wellness_tools, verbose=True)

    try:
        print("🔍 Executing wellness summary generation...")

        # 1. Get trends
        trends_result = executor.invoke({
            "input": "GetWellnessTrends"
        })

        # 2. Get Twitter
        twitter_result = executor.invoke({
            "input": "GetSocialBuzzPosts"
        })

        # 3. Get Reddit
        reddit_result = executor.invoke({
            "input": "GetRedditWellnessDiscussions"
        })

        # 4. Get research papers
        research_result = executor.invoke({
            "input": f"GetResearchPapers {start_date_str} {end_date_str} 'wellness research'"
        })

        # 5. Extract and clean results
        trends_output = extract_clean_output(trends_result)
        twitter_output = extract_clean_output(twitter_result)
        reddit_output = extract_clean_output(reddit_result)
        research_output = extract_clean_output(research_result)

        # 6. Combine top 5 social buzz entries
        social_buzz = []
        if twitter_output:
            social_buzz.extend(twitter_output.split("\n"))
        if reddit_output:
            social_buzz.extend(reddit_output.split("\n"))
        social_buzz = [buzz.strip() for buzz in social_buzz if buzz.strip()]
        social_buzz_text = "\n".join(social_buzz[:5])

        # 7. Format the agent_scratchpad string
        agent_scratchpad_text = (
            f"POPULAR TRENDS:\n{trends_output}\n\n"
            f"SOCIAL BUZZ:\n{social_buzz_text}\n\n"
            f"NOTABLE INSIGHTS:\n{research_output}"
        )

        # 8. Generate the final wellness summary
        final_summary = executor.invoke({
            "agent_scratchpad": agent_scratchpad_text,
            "input": "Generate the wellness summary"
        })

        # 9. Parse and save the summary
        parsed = parser.parse(final_summary["output"] if isinstance(final_summary, dict) else final_summary)
        summary = parsed.dict() if hasattr(parsed, "dict") else parsed

        html = generate_email_html_from_summary(summary)
        with open("wellness_summary.html", "w", encoding="utf-8") as f:
            f.write(html)

        save_summary_pdf(summary)
        print("✅ Wellness summary saved as 'wellness_summary.html' and 'wellness_summary.pdf'.")

    except Exception as e:
        print("❌ Error generating wellness timeline:", e)
        print("Detailed error:", str(e))

        if "Google Trends" in str(e):
            print("⚠️ Google Trends error: Check API availability or query format.")
        if "Twitter" in str(e):
            print("⚠️ Twitter API error: Check credentials or query format.")

if __name__ == "__main__":
    main()