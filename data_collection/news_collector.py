import requests
from datetime import datetime

API_KEY = "a63dddbb11404a20a72933b2fd53c51d"

def fetch_gold_news():
    url = f"https://newsapi.org/v2/everything?q=gold&sortBy=publishedAt&apiKey={API_KEY}"
    
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception("Failed to fetch news")

    articles = response.json().get("articles", [])

    news_data = []

    for article in articles:
        news_data.append({
            "title": article["title"],
            "description": article["description"],
            "published_at": article["publishedAt"],
            "source": article["source"]["name"]
        })

    return news_data


if __name__ == "__main__":
    news = fetch_gold_news()
    for n in news[:5]:
        print(n)