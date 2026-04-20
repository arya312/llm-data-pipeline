from dotenv import load_dotenv
load_dotenv()

import os
import json
import anthropic
import psycopg2
from kafka import KafkaConsumer
from datetime import datetime

claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def get_db_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def enrich_article(title: str, content: str) -> dict:
    """Send article to Claude for sentiment + entities + summary"""
    prompt = f"""Analyze this news article and return a JSON object with exactly these fields:
{{
  "sentiment": "positive" or "negative" or "neutral",
  "sentiment_score": a float from -1.0 (very negative) to 1.0 (very positive),
  "entities": {{
    "companies": ["list of company names mentioned"],
    "people": ["list of person names mentioned"],
    "places": ["list of locations mentioned"]
  }},
  "summary": "A single sentence summary of the article"
}}

Return ONLY the JSON object, no other text.

Title: {title}
Content: {content[:1500]}"""

    message = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    # Strip markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

def save_article(conn, article: dict, enrichment: dict):
    """Save enriched article to PostgreSQL"""
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO articles 
                (title, content, url, source, published_at, 
                 sentiment, sentiment_score, entities, summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING
        """, (
            article["title"],
            article["content"],
            article["url"],
            article["source"],
            article.get("published_at"),
            enrichment["sentiment"],
            enrichment["sentiment_score"],
            json.dumps(enrichment["entities"]),
            enrichment["summary"]
        ))
        conn.commit()
        return cur.rowcount > 0  # True if inserted, False if duplicate
    except Exception as e:
        conn.rollback()
        print(f"DB error: {e}")
        return False
    finally:
        cur.close()

def run_consumer():
    topic = os.environ["KAFKA_TOPIC"]
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=os.environ["KAFKA_BROKER"],
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        group_id="news_enrichment_group",
        auto_offset_reset="earliest"
    )

    conn = get_db_connection()
    print(f"Consumer started. Listening to topic: {topic}")

    try:
        for message in consumer:
            article = message.value
            print(f"\nProcessing: {article['title'][:60]}...")

            try:
                enrichment = enrich_article(article["title"], article["content"])
                saved = save_article(conn, article, enrichment)

                if saved:
                    print(f"  Sentiment: {enrichment['sentiment']} ({enrichment['sentiment_score']})")
                    print(f"  Summary: {enrichment['summary'][:80]}...")
                    print(f"  Entities: {enrichment['entities']}")
                    print(f"  ✅ Saved to DB")
                else:
                    print(f"  ⏭ Duplicate, skipped")

            except Exception as e:
                print(f"  ❌ Enrichment error: {e}")
                continue

    except KeyboardInterrupt:
        print("\nConsumer stopped.")
    finally:
        conn.close()
        consumer.close()

if __name__ == "__main__":
    run_consumer()