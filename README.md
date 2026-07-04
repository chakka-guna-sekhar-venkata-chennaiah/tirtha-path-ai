# TirthaPathAI — South Indian Pilgrimage Route Planner

> Neo4j GraphAcademy Cup — GDS Round of 32 Submission | Country: India
> Courses: Get Started with GDS · Path Finding with GDS

---

## What is TirthaPathAI?

TirthaPathAI is an AI-powered pilgrimage route planner for South Indian sacred sites, built as a LangGraph ReAct agent that uses **Neo4j Graph Data Science (GDS)** algorithms to help devotees plan their yatra.

A devotee can ask in Telugu, Hindi, or English:

| Question | Tool | Algorithm |
|---|---|---|
| "Vijayawada to Rameswaram shortest route?" | **GDS Path** | Dijkstra |
| "Temples within 2 stops from Hyderabad?" | **GDS Path** | BFS |
| "Best city to base myself for temples?" | **GDS Analysis** | Betweenness |
| "Most important temple in the network?" | **GDS Analysis** | PageRank |
| "What are the natural pilgrimage circuits?" | **GDS Community** | Louvain |

---

## Graph Design — Rule of 32

| | Count |
|---|---|
| **Nodes** | **32** (20 temples + 12 city hubs) |
| **Relationships** | **32** (`ROAD_CONNECTS` with `distance_km` + `duration_hours`) |
| **GDS algorithms** | 5 (Dijkstra, BFS, PageRank, Betweenness, Louvain) |

---

## Architecture

```
Devotee (Hindi / Telugu / English)
          │
    Streamlit Chat UI
    (streaming agent thoughts + highlighted network graph)
          │
    LangGraph ReAct Agent ──── DeepSeek LLM
          │
    ┌─────┼──────────────────────┐
    │     │                      │
gds_path  gds_analysis    gds_community
 tool      tool              tool
    │     │                      │
    └─────┴──────────────────────┘
                  │
         Neo4j (local) + GDS plugin
         32 nodes · 32 edges · 'tirtha-graph' projection
```

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | DeepSeek Chat API |
| Agent | LangGraph `create_react_agent` (ReAct pattern) |
| Graph DB | Neo4j 5.x (Docker or Desktop) |
| GDS | Neo4j Graph Data Science plugin |
| UI | Streamlit (streaming agent thoughts) |
| Graph viz | pyvis (interactive force-directed) |

---

## Quick Start

### 1. Start Neo4j with GDS plugin

**Docker (easiest):**
```bash
docker run --name neo4j-tirtha \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["graph-data-science"]' \
  -d neo4j:5
```

GDS is bundled automatically. To stop/start later: `docker stop neo4j-tirtha` / `docker start neo4j-tirtha`

**Neo4j Desktop:** Download from [neo4j.com/download](https://neo4j.com/download/), create a Local DBMS, install the Graph Data Science plugin from the Plugins tab.

### 2. Clone & install
```bash
git clone https://github.com/chakka-guna-sekhar-venkata-chennaiah/tirtha-path-ai
cd tirtha-path-ai
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
# Edit .env — add DEEPSEEK_API_KEY and NEO4J_PASSWORD
```

### 4. Seed & run
```bash
python database/neo4j_setup.py
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) 🙏

---

## Project Structure

```
tirtha-path-ai/
├── app.py                    # Streamlit chat UI + pyvis graph
├── requirements.txt
├── .env.example
├── agent/
│   ├── agent.py              # LangGraph ReAct agent builder
│   └── tools.py              # gds_path_tool, gds_analysis_tool, gds_community_tool
├── database/
│   └── neo4j_setup.py        # 32 nodes + 32 edges + GDS projection
└── pages/
    └── 1_🗺️_Pilgrimage_Network.py  # Full network map page
```

---

## Sample Queries

```
You:  "Which Jyotirlinga is closest to Vijayawada?"

AI:   Srisailam is closer — 487 km via 2 hops (Vijayawada → Kurnool → Srisailam).
      Rameswaram is 1045 km via 6 hops.
      
      Jai Sri Ram 🙏

You:  "What are the natural pilgrimage circuits?"

AI:   Louvain detected 3 circuits:
      
      Circuit 1 — Andhra Pradesh:
        Tirumala, Srisailam, Ahobilam, Mahanandi, Srikalahasti · via Tirupati, Kurnool
      
      Circuit 2 — Tamil Nadu:
        Rameswaram, Meenakshi, Srirangam, Thanjavur, Tiruvannamalai · via Chennai, Trichy
      
      Circuit 3 — Telangana:
        Bhadrachalam, Yadadri, Vemulawada, Basara · via Hyderabad, Warangal
      
      Jai Sri Ram 🙏
```

---

*Built with devotion for India's 12 million pilgrims 🙏*
