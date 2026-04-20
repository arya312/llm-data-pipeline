import { useState, useEffect } from "react";
import { PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from "recharts";

const API = "https://humble-garbanzo-9vxxx667vcpx49-8000.app.github.dev";

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#22c55e",
  neutral: "#94a3b8",
  negative: "#ef4444"
};

interface Article {
  id: number;
  title: string;
  source: string;
  sentiment: string;
  sentiment_score: number;
  summary: string;
  entities: { companies: string[]; people: string[]; places: string[] };
  published_at: string;
  url: string;
}

interface Stats {
  total_articles: number;
  last_processed: string;
  sentiment_breakdown: { sentiment: string; count: number; avg_score: number }[];
}

export default function App() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [sentiment, setSentiment] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [searchInput, setSearchInput] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    const res = await fetch(`${API}/stats`);
    const data = await res.json();
    setStats(data);
  };

  const fetchArticles = async () => {
    setLoading(true);
    let url = `${API}/articles?limit=20`;
    if (sentiment) url += `&sentiment=${sentiment}`;
    if (search) url = `${API}/articles/search?q=${search}&limit=20`;
    const res = await fetch(url);
    const data = await res.json();
    setArticles(data.articles || []);
    setLoading(false);
  };

// eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    fetchStats();
    fetchArticles();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchStats();
      fetchArticles();
    }, 30000);
    return () => clearInterval(interval);
  }, [sentiment, search]);

  const handleSearch = () => setSearch(searchInput);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "2rem 1rem", fontFamily: "system-ui, sans-serif", background: "#f8fafc", minHeight: "100vh" }}>

      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>📰 LLM News Intelligence</h1>
        <p style={{ color: "#64748b", marginTop: 4 }}>
          Real-time news enriched with Claude AI · Auto-refreshes every 30s
          {stats && ` · Last update: ${new Date(stats.last_processed).toLocaleTimeString()}`}
        </p>
      </div>

      {/* Stats cards */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 16, marginBottom: "2rem" }}>
          <div style={{ background: "white", borderRadius: 12, padding: "1.25rem", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: 13, color: "#64748b" }}>Total articles</div>
            <div style={{ fontSize: 32, fontWeight: 700 }}>{stats.total_articles}</div>
          </div>
          {(stats.sentiment_breakdown || []).map(s => (
            <div key={s.sentiment} style={{ background: "white", borderRadius: 12, padding: "1.25rem", border: `2px solid ${SENTIMENT_COLORS[s.sentiment]}` }}>
              <div style={{ fontSize: 13, color: "#64748b", textTransform: "capitalize" }}>{s.sentiment}</div>
              <div style={{ fontSize: 32, fontWeight: 700, color: SENTIMENT_COLORS[s.sentiment] }}>{s.count}</div>
              <div style={{ fontSize: 12, color: "#94a3b8" }}>avg score: {s.avg_score}</div>
            </div>
          ))}
        </div>
      )}

      {/* Charts */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: "2rem" }}>
          <div style={{ background: "white", borderRadius: 12, padding: "1.25rem", border: "1px solid #e2e8f0" }}>
            <h3 style={{ margin: "0 0 1rem", fontSize: 15 }}>Sentiment distribution</h3>
            <PieChart width={280} height={200}>
              <Pie data={stats.sentiment_breakdown} dataKey="count" nameKey="sentiment" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}`}>
                {(stats.sentiment_breakdown || []).map(s => (
                  <Cell key={s.sentiment} fill={SENTIMENT_COLORS[s.sentiment]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </div>
          <div style={{ background: "white", borderRadius: 12, padding: "1.25rem", border: "1px solid #e2e8f0" }}>
            <h3 style={{ margin: "0 0 1rem", fontSize: 15 }}>Avg sentiment score</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={stats.sentiment_breakdown}>
                <XAxis dataKey="sentiment" />
                <YAxis domain={[-1, 1]} />
                <Tooltip />
                <Bar dataKey="avg_score">
                  {(stats.sentiment_breakdown || []).map(s => (
                    <Cell key={s.sentiment} fill={SENTIMENT_COLORS[s.sentiment]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: "1.5rem", flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: 8 }}>
          {["", "positive", "neutral", "negative"].map(s => (
            <button key={s} onClick={() => { setSentiment(s); setSearch(""); setSearchInput(""); }}
              style={{ padding: "8px 16px", borderRadius: 8, border: "1px solid #e2e8f0", background: sentiment === s && !search ? "#0f172a" : "white", color: sentiment === s && !search ? "white" : "#374151", cursor: "pointer", fontSize: 13 }}>
              {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8, flex: 1, minWidth: 200 }}>
          <input value={searchInput} onChange={e => setSearchInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
            placeholder="Search articles..." style={{ flex: 1, padding: "8px 12px", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 13 }} />
          <button onClick={handleSearch} style={{ padding: "8px 16px", borderRadius: 8, border: "none", background: "#0f172a", color: "white", cursor: "pointer", fontSize: 13 }}>
            Search
          </button>
        </div>
      </div>

      {/* Articles */}
      {loading ? (
        <p style={{ color: "#94a3b8" }}>Loading articles...</p>
      ) : articles.length === 0 ? (
        <p style={{ color: "#94a3b8" }}>No articles found.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {articles.map(article => (
            <div key={article.id} style={{ background: "white", borderRadius: 12, padding: "1.25rem", border: "1px solid #e2e8f0", borderLeft: `4px solid ${SENTIMENT_COLORS[article.sentiment]}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <a href={article.url} target="_blank" rel="noreferrer" style={{ fontSize: 16, fontWeight: 600, color: "#0f172a", textDecoration: "none" }}>
                    {article.title}
                  </a>
                  <p style={{ fontSize: 13, color: "#64748b", margin: "6px 0" }}>{article.summary}</p>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
                    {article.source && <span style={{ fontSize: 11, background: "#f1f5f9", padding: "2px 8px", borderRadius: 20, color: "#475569" }}>{article.source}</span>}
                    {article.entities?.companies?.map(c => <span key={c} style={{ fontSize: 11, background: "#eff6ff", padding: "2px 8px", borderRadius: 20, color: "#1d4ed8" }}>{c}</span>)}
                    {article.entities?.places?.map(p => <span key={p} style={{ fontSize: 11, background: "#f0fdf4", padding: "2px 8px", borderRadius: 20, color: "#166534" }}>{p}</span>)}
                  </div>
                </div>
                <div style={{ textAlign: "right", flexShrink: 0 }}>
                  <span style={{ background: SENTIMENT_COLORS[article.sentiment], color: "white", padding: "4px 10px", borderRadius: 20, fontSize: 12, fontWeight: 600 }}>
                    {article.sentiment}
                  </span>
                  <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>{article.sentiment_score}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <p style={{ fontSize: 12, color: "#cbd5e1", textAlign: "center", marginTop: "2rem" }}>
        Built with Kafka · PostgreSQL · Claude · FastAPI · React
      </p>
    </div>
  );
}