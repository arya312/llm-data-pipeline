from dotenv import load_dotenv
load_dotenv()

import os
import json
import time
import requests
from kafka import KafkaProducer
from datetime import datetime

def create_producer():
    return KafkaProducer(
        bootstrap_servers=os.environ["KAFKA_BROKER"],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",  # wait for all replicas to acknowledge
        retries=3
    )

def fetch_news(api_key: str, query: str = "technology AI", page_size: int = 10) -> list:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "pageSize": page_size,
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": api_key
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("articles", [])

def run_producer(interval_seconds: int = 60):
    api_key = os.environ["NEWS_API_KEY"]
    topic = os.environ["KAFKA_TOPIC"]
    producer = create_producer()

    print(f"Producer started. Fetching news every {interval_seconds}s...")

    while True:
        try:
            articles = fetch_news(api_key)
            print(f"Fetched {len(articles)} articles")

            for article in articles:
                message = {
                    "title": article.get("title", ""),
                    "content": article.get("content") or article.get("description", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "published_at": article.get("publishedAt", ""),
                    "fetched_at": datetime.utcnow().isoformat()
                }

                if message["title"] and message["url"]:
                    producer.send(topic, value=message)
                    print(f"  → Sent: {message['title'][:60]}...")

            producer.flush()
            print(f"Batch complete. Waiting {interval_seconds}s...\n")
            time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("Producer stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_producer(interval_seconds=30)