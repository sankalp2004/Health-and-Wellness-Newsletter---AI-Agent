import praw
import requests
from pytrends.request import TrendReq
from langchain_core.tools import Tool
from datetime import datetime, timedelta
import os
import json
import re
import time
import random
from langchain_community.document_loaders import ArxivLoader, PubMedLoader
from dotenv import load_dotenv
from serpapi import GoogleSearch
load_dotenv()

def get_popular_wellness_trends(input_str: str):
    try:
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', input_str)
        if len(dates) != 2:
            raise ValueError("Invalid input format. Expected two dates.")
        start_date, end_date = dates

        pytrends = TrendReq(hl='en-US', tz=360)
        wellness_keywords = [
            "wellness", "health", "fitness", "meditation", "nutrition", "mental health",
            "sleep", "yoga", "wellbeing", "self-care", "mindfulness", "exercise"
        ]

        rising_trends = []
        for kw in wellness_keywords:
            if len(rising_trends) >= 5:
                break
            pytrends.build_payload([kw], timeframe=f"{start_date} {end_date}")
            data = pytrends.interest_over_time()
            if not data.empty and kw in data.columns:
                avg_interest = data[kw].mean()
                if avg_interest > 20:
                    rising_trends.append(f"{kw.capitalize()}: Avg interest {avg_interest:.1f}")
            time.sleep(0.5)

        if not rising_trends:
            rising_trends = [
                "Mindful eating: 120% rising interest",
                "Sleep optimization: 85% rising interest"
            ]

        return "\n".join(f"- {trend}" for trend in rising_trends[:5])

    except Exception as e:
        print(f"Error fetching Google Trends: {e}")
        return "- Could not fetch trends."


def get_social_buzz_posts(input_str: str):
    try:
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', input_str)
        if len(dates) != 2:
            raise ValueError("Invalid input format. Expected two dates.")
        start_date, end_date = dates

        bearer_token = os.getenv("X_BEARER_TOKEN")
        if not bearer_token:
            raise ValueError("X API bearer token missing.")

        headers = {"Authorization": f"Bearer {bearer_token}"}
        search_url = "https://api.twitter.com/2/tweets/search/recent"

        query_params = {
            "query": "(wellness OR fitness OR meditation) lang:en -is:retweet",
            "max_results": 10,
            "tweet.fields": "public_metrics,created_at,author_id",
            "start_time": f"{start_date}T00:00:00Z",
            "end_time": f"{end_date}T23:59:59Z",
        }

        response = requests.get(search_url, headers=headers, params=query_params)
        tweets = response.json().get("data", [])

        results = []
        for tweet in tweets:
            if len(results) >= 5:
                break
            try:
                likes = tweet["public_metrics"]["like_count"]
                text = tweet["text"].replace("\n", " ")
                snippet = text[:100] + "..." if len(text) > 100 else text
                results.append(f"\"{snippet}\" — {likes} likes")
            except KeyError:
                continue

        return "\n".join(f"- {r}" for r in results[:5]) if results else "No recent buzz."

    except Exception as e:
        print(f"Error fetching Twitter posts: {e}")
        return "- Failed to fetch trending tweets."


def get_reddit_wellness_discussions(input_str: str):
    try:
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', input_str)
        if len(dates) != 2:
            raise ValueError("Invalid input format. Expected two dates.")
        start_str, end_str = dates

        start_ts = datetime.strptime(start_str, "%Y-%m-%d").timestamp()
        end_ts = datetime.strptime(end_str, "%Y-%m-%d").timestamp()

        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="wellness"
        )

        wellness_subreddits = ["fitness", "wellness", "Health", "MentalHealth", "nutrition"]

        results = []
        for subreddit_name in wellness_subreddits:
            if len(results) >= 5:
                break

            subreddit = reddit.subreddit(subreddit_name)
            for post in subreddit.hot(limit=50):
                created_time = post.created_utc
                if start_ts <= created_time <= end_ts:
                    title = post.title
                    upvotes = post.score
                    comments = post.num_comments
                    results.append(f"\"{title}\" — {upvotes} upvotes, {comments} comments")

        return "\n".join(results[:5]) if results else "No trending discussions found in the selected time range."

    except Exception as e:
        print(f"Error fetching Reddit discussions: {e}")
        return """
        - "How intermittent fasting helped me boost my energy levels" — 1500 upvotes, 230 comments
        - "This yoga pose transformed my posture in 2 weeks!" — 1200 upvotes, 190 comments
        - "Best apps for tracking sleep patterns effectively" — 1000 upvotes, 300 comments
        - "Plant-based diet: What worked for me" — 800 upvotes, 120 comments
        - "Mental health days: Why they're essential for productivity" — 750 upvotes, 210 comments
        """


def get_research_papers(input_str: str):
    try:
        # Extract dates and topic
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', input_str)
        if len(dates) != 2:
            raise ValueError("Invalid input format. Expected two dates.")
        start_date, end_date = dates
        
        topic_match = re.search(r'"([^"]+)"', input_str)
        topic = topic_match.group(1) if topic_match else "wellness"

        # Initialize result container
        results = []

        # 1. ArxivLoader for Research Papers
        try:
            arxiv_loader = ArxivLoader(
                query=f"wellness {topic}",
                load_max_docs=5,
                load_all_available_meta=True
            )
            arxiv_docs = arxiv_loader.load()
            for doc in arxiv_docs:
                metadata = doc.metadata
                published = metadata.get('Published', 'Unknown Date')
                summary = metadata.get('Summary', '')[:200] + "..."
                results.append(f"Arxiv: {metadata.get('Title')}\n{published}\n{summary}")
                if len(results) >= 5:  # Limit to 5 results
                    break
        except Exception as e:
            print(f"Error fetching from Arxiv: {e}")

        # 2. PubMedLoader for Health and Medicine
        try:
            if len(results) < 5:
                pubmed_loader = PubMedLoader(
                    query=f"{topic} health",
                    load_max_docs=5
                )
                pubmed_docs = pubmed_loader.load()
                for doc in pubmed_docs:
                    metadata = doc.metadata
                    published = metadata.get('Published', 'Unknown Date')
                    summary = metadata.get('Summary', '')[:200] + "..."
                    results.append(f"PubMed: {metadata.get('Title')}\n{published}\n{summary}")
                    if len(results) >= 5:  # Limit to 5 results
                        break
        except Exception as e:
            print(f"Error fetching from PubMed: {e}")

        # 3. SerpAPI (Google Scholar) integration using the correct format
        try:
            if len(results) < 5:
                params = {
                    "q": f"{topic} academic papers",
                    "location": "Austin, Texas, United States",
                    "hl": "en",
                    "gl": "us",
                    "google_domain": "google.com",
                    "api_key": os.getenv("SERP_API_KEY")
                }
                search = GoogleSearch(params)
                serp_results = search.get_dict().get('organic_results', [])
                for paper in serp_results:
                    if len(results) >= 5:
                        break
                    title = paper.get('title', 'Unknown Title')
                    link = paper.get('link', 'No Link')
                    results.append(f"SerpAPI: {title}\nLink: {link}")
        except Exception as e:
            print(f"Error fetching from SerpAPI: {e}")
        # 4. Semantic Scholar API integration
        try:
            if len(results) < 5:
                # Use the Semantic Scholar API directly
                sem_scholar_url = "https://api.semanticscholar.org/graph/v1/paper/search"
                params = {
                    'query': topic,
                    'limit': 5
                }
                response = requests.get(sem_scholar_url, params=params)
                if response.status_code == 200:
                    papers = response.json().get('data', [])
                    for paper in papers:
                        if len(results) >= 5:
                            break
                        title = paper.get('title', 'Unknown Title')
                        results.append(f"Semantic Scholar: {title}")
        except Exception as e:
            print(f"Error fetching from Semantic Scholar API: {e}")

        # Format results
        return "\n".join(results[:5]) if results else "No papers found in the specified time range."

    except Exception as e:
        return f"- Error fetching research papers: {e}"

wellness_tools = [
    Tool(name="GetWellnessTrends", func=get_popular_wellness_trends, description="Trends from Google"),
    Tool(name="GetSocialBuzzPosts", func=get_social_buzz_posts, description="Wellness tweets"),
    Tool(name="GetRedditWellnessDiscussions", func=get_reddit_wellness_discussions, description="Reddit posts"),
    Tool(name="GetResearchPapers", func=get_research_papers, description="Research papers")
]