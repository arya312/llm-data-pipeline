from dotenv import load_dotenv
load_dotenv()

import os
import psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT UNIQUE,
    source TEXT,
    published_at TIMESTAMP,
    sentiment VARCHAR(20),
    sentiment_score FLOAT,
    entities JSONB,
    summary TEXT,
    processed_at TIMESTAMP DEFAULT NOW()
);
""")

conn.commit()
cur.close()
conn.close()
print("Database schema created successfully!")
