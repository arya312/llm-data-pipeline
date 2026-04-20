from dotenv import load_dotenv
load_dotenv()

import os
import json
import psycopg2
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime

app = FastAPI(title="LLM News Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def row_to_dict(row, cursor):
    cols = [desc[0] for desc in cursor.description]
    d = dict(zip(cols, row))
    # Convert datetime to string
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
        if isinstance(v, str):
            try:
                d[k] = json.loads(v)
            except:
                pass
    return d


@app.get("/")
def root():
    return {"status": "LLM News Pipeline API is running"}


@app.get("/articles")
def get_articles(
    sentiment: Optional[str] = Query(None, description="Filter by sentiment: positive, negative, neutral"),
    company: Optional[str] = Query(None, description="Filter by company name in entities"),
    limit: int = Query(20, le=100),
    offset: int = Query(0)
):
    """Get enriched articles with optional filters"""
    conn = get_conn()
    cur = conn.cursor()

    query = "SELECT * FROM articles WHERE 1=1"
    params = []

    if sentiment:
        query += " AND sentiment = %s"
        params.append(sentiment)

    if company:
        query += " AND entities::text ILIKE %s"
        params.append(f"%{company}%")

    query += " ORDER BY processed_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cur.execute(query, params)
    rows = cur.fetchall()
    articles = [row_to_dict(r, cur) for r in rows]

    conn.close()
    return {"articles": articles, "count": len(articles)}


@app.get("/articles/latest")
def get_latest(limit: int = Query(5, le=20)):
    """Get the most recently processed articles"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM articles ORDER BY processed_at DESC LIMIT %s",
        (limit,)
    )
    rows = cur.fetchall()
    articles = [row_to_dict(r, cur) for r in rows]
    conn.close()
    return {"articles": articles}


@app.get("/stats")
def get_stats():
    """Sentiment distribution and top entities"""
    conn = get_conn()
    cur = conn.cursor()

    # Sentiment breakdown
    cur.execute("""
        SELECT sentiment, COUNT(*) as count, ROUND(AVG(sentiment_score)::numeric, 3) as avg_score
        FROM articles
        GROUP BY sentiment
        ORDER BY count DESC
    """)
    sentiment_rows = cur.fetchall()
    sentiment_breakdown = [
        {"sentiment": r[0], "count": r[1], "avg_score": float(r[2])}
        for r in sentiment_rows
    ]

    # Total count
    cur.execute("SELECT COUNT(*) FROM articles")
    total = cur.fetchone()[0]

    # Most recent article
    cur.execute("SELECT processed_at FROM articles ORDER BY processed_at DESC LIMIT 1")
    last_row = cur.fetchone()
    last_processed = last_row[0].isoformat() if last_row else None

    conn.close()
    return {
        "total_articles": total,
        "last_processed": last_processed,
        "sentiment_breakdown": sentiment_breakdown,
    }


@app.get("/articles/search")
def search_articles(
    q: str = Query(..., description="Search term for title or summary"),
    limit: int = Query(10, le=50)
):
    """Full text search across title and summary"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM articles
        WHERE title ILIKE %s OR summary ILIKE %s
        ORDER BY processed_at DESC
        LIMIT %s
    """, (f"%{q}%", f"%{q}%", limit))
    rows = cur.fetchall()
    articles = [row_to_dict(r, cur) for r in rows]
    conn.close()
    return {"articles": articles, "count": len(articles), "query": q}