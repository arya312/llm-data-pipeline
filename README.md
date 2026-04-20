<video src="https://drive.google.com/file/d/1EW9t6ijyW4eA6a2Qo1eifB83tO74hUPD/view?usp=sharing" width="320" height="240" controls></video>

# LLM News Intelligence Pipeline

A real-time data pipeline that ingests live news, enriches it with Claude AI, and displays results on a live dashboard.

## What it does
NewsAPI → Kafka Producer → Kafka Topic → Consumer → Claude API → PostgreSQL → FastAPI → React Dashboard

Every article is automatically enriched with:
- **Sentiment** — positive / neutral / negative with a score from -1.0 to 1.0
- **Named entities** — companies, people, and places mentioned
- **Summary** — one sentence summary of the article

Results are queryable via REST API and visualised on a live dashboard that auto-refreshes every 30 seconds.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Message queue | Apache Kafka |
| Database | PostgreSQL |
| LLM enrichment | Claude (Anthropic) |
| Backend API | FastAPI |
| Frontend | React + TypeScript + Recharts |
| Infrastructure | Docker Compose |

---

## Quick start

### Prerequisites
- Docker + Docker Compose
- Python 3.11+
- Node.js 18+
- Anthropic API key ([console.anthropic.com](https://console.anthropic.com))
- NewsAPI key ([newsapi.org](https://newsapi.org)) — free tier works

### 1. Clone and configure

```bash
git clone https://github.com/arya312/llm-data-pipeline
cd llm-data-pipeline
```

Create `.env`:
ANTHROPIC_API_KEY="your_anthropic_key"
NEWS_API_KEY="your_newsapi_key"
DATABASE_URL="postgresql://pipeline_user:pipeline_pass@localhost:5432/news_pipeline"
KAFKA_BROKER="localhost:9092"
KAFKA_TOPIC="news_articles"

### 2. Start infrastructure

```bash
docker compose up -d
```

Wait 30 seconds for Kafka and PostgreSQL to fully start.

### 3. Set up database

```bash
pip install -r requirements.txt
python setup_db.py
```

### 4. Run the pipeline

Open two terminals:

**Terminal 1 — Consumer (processes articles with Claude):**
```bash
python src/consumer.py
```

**Terminal 2 — Producer (fetches live news):**
```bash
python src/producer.py
```

Watch Terminal 1 — articles will be enriched in real time with sentiment, entities, and summaries.

### 5. Start the API

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Start the dashboard

```bash
cd frontend
npm install
# Update API URL in src/App.tsx to http://localhost:8000
npm start
```

Visit `http://localhost:3000` for the dashboard.

---

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /articles` | All articles (supports `?sentiment=positive`, `?company=Apple`) |
| `GET /articles/latest` | Most recently processed articles |
| `GET /articles/search?q=robots` | Full text search |
| `GET /stats` | Sentiment breakdown and totals |
| `GET /docs` | Interactive API documentation |

---

## Dashboard features

- Live sentiment distribution pie chart
- Average sentiment score bar chart
- Filter articles by positive / neutral / negative
- Search across titles and summaries
- Entity tags per article (companies, places)
- Auto-refreshes every 30 seconds

---

## Architecture decisions

**Why Kafka?** Producer and consumer are fully decoupled. The producer fetches articles in 2 seconds. Claude takes ~2 seconds per article. Without Kafka, the producer would block waiting for each enrichment. With Kafka, they run independently at their own pace — a core event-driven architecture pattern.

**Why idempotent storage?** The `ON CONFLICT (url) DO NOTHING` pattern means running the pipeline multiple times produces the same result. Safe for retries, no duplicates.

**Why structured LLM output?** Claude returns JSON with defined fields rather than free text — making the output machine-readable and directly storable in PostgreSQL.

---

## Sample output
Processing: Humanoid robots race past humans in Beijing half-marathon...
Sentiment: positive (0.7)
Summary: Chinese-made humanoid robots outpaced human runners in Beijing...
Entities: {'companies': [], 'people': [], 'places': ['Beijing', 'China']}
✅ Saved to DB

---

Built by [arya312](https://github.com/arya312)
