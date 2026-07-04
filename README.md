# 🕉️ TirthaPathAI — South Indian Pilgrimage Route Planner

> **Neo4j GraphAcademy Cup — GDS Round of 32 Submission**  
> Country: 🇮🇳 India | Courses: *Get Started with GDS* + *Path Finding with GDS*

---

## What is TirthaPathAI?

TirthaPathAI is an AI-powered pilgrimage route planner for South Indian sacred sites, built as a LangChain ReAct agent that uses **Neo4j Graph Data Science (GDS)** algorithms to help devotees plan their yatra.

A devotee can ask in Telugu, Hindi, or English:
> *"Vijayawada nundi Rameswaram shortest route emi?"*  
> *"Which temples can I visit in 2 stops from Hyderabad?"*  
> *"Best city to be based in for visiting maximum temples?"*

…and the agent intelligently routes each question to the appropriate GDS algorithm.

---

## The Rule of 32 — Graph Design

| | Count |
|---|---|
| **Nodes** | **32** (20 temples + 12 city hubs) |
| **Relationships** | **32** (`ROAD_CONNECTS` with `distance_km` + `duration_hours`) |
| **GDS algorithms** | 5 (Dijkstra, BFS, PageRank, Betweenness, Louvain) |

### 20 Temple Nodes

**Andhra Pradesh (8):** Tirumala, Srisailam (Jyotirlinga), Kanaka Durga, Mahanandi, Ahobilam, Annavaram, Simhachalam, Srikalahasti (Pancha Bhuta)

**Telangana (5):** Bhadrachalam, Yadadri, Vemulawada, Basara, Keesaragutta

**Tamil Nadu (7):** Rameswaram (Jyotirlinga + Char Dham), Meenakshi Temple, Kamakshi Kanchipuram, Tiruvannamalai (Pancha Bhuta), Chidambaram (Pancha Bhuta), Srirangam, Thanjavur (UNESCO)

### 12 City Hub Nodes
Vijayawada, Hyderabad, Chennai, Tirupati, Guntur, Visakhapatnam, Nellore, Kurnool, Rajahmundry, Warangal, Trichy, Madurai

---

## GDS Algorithms → Pilgrim Questions

| Pilgrim Question | GDS Algorithm |
|---|---|
| "Shortest route from Vijayawada to Rameswaram?" | **Dijkstra** (weighted by `distance_km`) |
| "Which temples within 2 stops from Hyderabad?" | **BFS** (breadth-first, maxDepth=2) |
| "Best city to base myself for maximum temples?" | **Betweenness Centrality** |
| "Most important temple in the network?" | **PageRank** |
| "What are the natural pilgrimage circuits?" | **Louvain** community detection |

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

## Setup

### 1. Install Neo4j Desktop + GDS Plugin

1. Download **Neo4j Desktop** from [neo4j.com/download](https://neo4j.com/download/)
2. Create a new **Local DBMS** (Neo4j 5.x)
3. In the database panel → **Plugins** tab → **Graph Data Science** → Install
4. Start the database
5. Note your password (set when creating)

### 2. Install Python dependencies

```bash
git clone https://github.com/YOUR_USERNAME/tirtha-path-ai
cd tirtha-path-ai

python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env:
#   DEEPSEEK_API_KEY=sk-...
#   NEO4J_PASSWORD=<your neo4j desktop password>
```

### 4. Seed the database (32 nodes + 32 edges + GDS projection)

```bash
python database/neo4j_setup.py
```

Expected output:
```
🧹 Clearing existing data…
🛕 Creating temple nodes…
🏙️ Creating city nodes…
🛣️ Creating 32 road connections…
📊 Creating GDS in-memory graph projection…
✅ Neo4j setup complete!
   Nodes              : 32  (expected 32)
   Relationships (dir): 64  (expected 64 — 32 roads × 2 directions)
   GDS nodes          : 32
   GDS relationships  : 64
```

### 5. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) 🙏

---

## Example Conversations

```
You:    "Vijayawada to Rameswaram shortest route?"

AI:     🛣️ Route: Vijayawada → Nellore → Tirupati → Chennai → Trichy → Madurai → Rameswaram
        📍 Distance: 817 km  |  ⏱️ Est. time: ~14.9 hours
        
        🕉️ Tirumala — Venkateswara (Balaji), Saptagiri hills. Richest temple in the world.
        🕉️ Rameswaram — Ramanatha Jyotirlinga. One of the 12 Jyotirlingas and Char Dham. 
        
        Jai Sri Ram 🙏
```

```
You:    "Which pilgrimage circuits exist?"

AI:     The Louvain algorithm detected 3 natural circuits:
        
        Circuit 1 — Andhra Pradesh:
          Tirumala, Srisailam, Ahobilam, Mahanandi, Srikalahasti
          Via: Tirupati, Kurnool
        
        Circuit 2 — Tamil Nadu:
          Rameswaram, Meenakshi Temple, Srirangam, Thanjavur, Tiruvannamalai, Chidambaram
          Via: Chennai, Trichy, Madurai
        
        Circuit 3 — Telangana:
          Bhadrachalam, Yadadri, Vemulawada, Basara, Keesaragutta
          Via: Hyderabad, Warangal
        
        Jai Sri Ram 🙏
```

---

## What I Learned (GraphAcademy — Path Finding with GDS)

The most valuable insight from the *Path Finding with GDS* course was understanding that **graph traversal algorithms have a direct 1:1 mapping with real human navigation problems.**

For TirthaPathAI, I applied:

1. **Dijkstra's algorithm** with `distance_km` as the weight property — gives pilgrims the optimal road route, not just the fewest stops.
2. **BFS (Breadth-First Search)** with `maxDepth` — shows all temples reachable within a given number of road connections, perfect for "what can I visit in a weekend?".
3. **Betweenness Centrality** — revealed that Hyderabad and Chennai are the most critical transit hubs, which intuitively matches how pilgrims actually plan their journeys.
4. **PageRank** — when applied to the pilgrimage network, Tirumala scores highest because almost every pilgrimage route passes through or near Tirupati.
5. **Louvain community detection** — automatically grouped temples into geographic circuits that match traditional pilgrimage traditions — AP, TN, and Telangana circuits emerged naturally from the graph structure alone.

The architecture of combining a LangChain ReAct agent with Neo4j GDS shows how AI can make graph science accessible to ordinary devotees who just want to know *"what's the best route to my next temple?"* without understanding any of the algorithms running underneath.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | DeepSeek Chat API |
| Agent | LangGraph `create_react_agent` |
| Graph DB | Neo4j 5.x (local Desktop) |
| GDS | Neo4j Graph Data Science plugin |
| UI | Streamlit |
| Visualisation | pyvis (vis.js — same engine as Neo4j Browser) |

---

## 🏆 Competition Submission

- **GraphAcademy Cup Team**: [India team URL]
- **Username**: [GraphAcademy public profile]
- **Courses completed**: Get Started with Graph Data Science + Path Finding with GDS
- **Country**: 🇮🇳 India

---

*Built with devotion for India's 12 million pilgrims 🙏*
