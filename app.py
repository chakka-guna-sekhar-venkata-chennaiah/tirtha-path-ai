"""
TirthaPathAI — Streamlit Chat Interface
Streams LangGraph agent thoughts, renders pyvis pilgrim network graph,
highlights GDS shortest paths in the visual.
"""
import json
import os
import tempfile

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from pyvis.network import Network

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TirthaPathAI 🕉️",
    page_icon="🕉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.tirtha-header {
    background: linear-gradient(90deg, #8B4513, #D2691E);
    padding: 14px 20px;
    border-radius: 10px;
    color: white;
    margin-bottom: 1rem;
}
.tirtha-header h1 { margin:0; font-size:1.5rem; }
.tirtha-header p  { margin:4px 0 0; font-size:0.85rem; opacity:0.9; }
.tool-tag {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    margin: 2px 0;
}
.tag-path    { background:#E6F1FB; color:#185FA5; }
.tag-analysis{ background:#E1F5EE; color:#0F6E56; }
.tag-community{ background:#FAEEDA; color:#854F0B; }
</style>
""", unsafe_allow_html=True)

# ── Node colours — same across pyvis and legend ────────────────────────────────
NODE_COLORS = {
    "City":       "#2a78d6",   # blue
    "Vishnu":     "#1baf7a",   # teal
    "Shiva":      "#7c5cbf",   # purple
    "Shakti":     "#e34948",   # coral/red
    "Saraswati":  "#eda100",   # amber
}
NODE_SIZES = {
    "City":       24,
    "Vishnu":     20,
    "Shiva":      20,
    "Shakti":     20,
    "Saraswati":  20,
}
HIGHLIGHT_COLOR = "#FF6B35"  # orange — highlighted route nodes

TOOL_META = {
    "gds_path_tool":      ("🗺️", "GDS Path",      "tag-path"),
    "gds_analysis_tool":  ("📊", "GDS Analysis",  "tag-analysis"),
    "gds_community_tool": ("🔮", "GDS Community", "tag-community"),
}

SAMPLE_QUESTIONS = [
    "🛣️ Vijayawada to Rameswaram shortest route?",
    "🛕 Temples I can visit in 2 stops from Hyderabad?",
    "🏙️ Best city to be based in for pilgrims?",
    "👑 Most important temple in the network?",
    "🔮 What are the natural pilgrimage circuits?",
    "⚡ Compare Srisailam vs Ahobilam distance from Kurnool",
    "🕉️ Which Jyotirlinga is closest to Vijayawada?",
    "📊 Show me closeness centrality of all nodes",
]


# ── Database helpers ────────────────────────────────────────────────────────────

def get_neo4j_driver():
    from neo4j import GraphDatabase
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI",      "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"),
              os.getenv("NEO4J_PASSWORD", "password")),
    )


@st.cache_data(ttl=300, show_spinner=False)
def fetch_graph_data():
    """Load all 32 nodes + 32 edges from Neo4j for pyvis rendering."""
    try:
        driver = get_neo4j_driver()
        with driver.session() as s:
            nodes_raw = s.run("""
                MATCH (n)
                RETURN n.name AS name,
                       labels(n) AS labels,
                       n.deity_form AS deity_form,
                       n.state AS state,
                       n.significance AS significance,
                       n.role AS role
            """).data()

            edges_raw = s.run("""
                MATCH (a)-[r:ROAD_CONNECTS]->(b)
                WHERE id(a) < id(b)
                RETURN a.name AS src, b.name AS tgt,
                       r.distance_km AS km, r.duration_hours AS hrs
            """).data()
        driver.close()
        return nodes_raw, edges_raw
    except Exception as e:
        return None, str(e)


def check_neo4j():
    try:
        driver = get_neo4j_driver()
        with driver.session() as s:
            n = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            g = s.run(
                "CALL gds.graph.list('tirtha-graph') YIELD nodeCount RETURN nodeCount"
            ).single()
        driver.close()
        return True, f"{n} nodes, GDS: {g['nodeCount'] if g else '—'}"
    except Exception as e:
        return False, str(e)


# ── pyvis graph renderer ────────────────────────────────────────────────────────

def render_pilgrim_graph(nodes_raw, edges_raw, highlighted: list = None, height=520):
    """
    Render the 32-node pilgrim network with pyvis.
    highlighted: list of node names to colour orange (route path).
    """
    highlighted = set(highlighted or [])

    net = Network(
        height=f"{height}px",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="#e8e8e8",
        directed=False,
        notebook=False,
    )
    net.barnes_hut(
        gravity=-6000,
        central_gravity=0.25,
        spring_length=140,
        spring_strength=0.05,
    )

    for n in nodes_raw:
        name   = n["name"]
        labels = n["labels"] or []

        # Determine color
        if name in highlighted:
            color = HIGHLIGHT_COLOR
            size  = 30
        elif "City" in labels:
            color = NODE_COLORS["City"]
            size  = NODE_SIZES["City"]
        else:
            for deity in ("Vishnu", "Shiva", "Shakti", "Saraswati"):
                if deity in labels:
                    color = NODE_COLORS[deity]
                    size  = NODE_SIZES[deity]
                    break
            else:
                color, size = "#888780", 18

        # Tooltip
        role  = n.get("deity_form") or n.get("role") or ""
        state = n.get("state") or ""
        sig   = n.get("significance") or ""
        tip   = f"<b>{name}</b><br>{role}<br>{state}"
        if sig:
            tip += f"<br><i>{sig[:60]}</i>"

        net.add_node(
            name,
            label=name,
            title=tip,
            color={
                "background": color,
                "border": "#ffffff55" if name not in highlighted else "#FF6B35",
                "highlight": {"background": HIGHLIGHT_COLOR},
            },
            size=size,
            font={"size": 11, "color": "#ffffff"},
            borderWidth=1 if name not in highlighted else 3,
        )

    for e in edges_raw:
        src, tgt = e["src"], e["tgt"]
        km  = e.get("km",  "?")
        hrs = e.get("hrs", "?")

        # Highlight edge if both endpoints are in the route
        on_route = (src in highlighted and tgt in highlighted)
        net.add_edge(
            src, tgt,
            title=f"{km} km / ~{hrs}h",
            label=f"{int(km)}km" if km and km != "?" else "",
            color="#FF6B35" if on_route else "#ffffff33",
            width=3 if on_route else 1,
            font={"size": 8, "color": "#cccccc", "align": "middle"},
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
        net.save_graph(f.name)
        html = open(f.name, encoding="utf-8").read()

    components.html(html, height=height + 20, scrolling=False)


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🕉️ TirthaPathAI")
    neo_ok, neo_msg = check_neo4j()

    if neo_ok:
        st.success(f"✅ Neo4j + GDS — {neo_msg}")
    else:
        st.error(f"❌ Neo4j — {neo_msg}")
        st.caption("Start Neo4j Desktop, enable GDS plugin, then run:")
        st.code("python database/neo4j_setup.py", language="bash")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pop("route_nodes", None)
            st.rerun()
    with col2:
        if st.button("🔄 Re-seed", use_container_width=True):
            with st.spinner("Seeding…"):
                from database.neo4j_setup import setup_neo4j
                setup_neo4j()
                st.cache_data.clear()
            st.success("✅ Done!")

    st.markdown("---")
    st.markdown("**🔍 Try asking:**")
    for q in SAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True, key=f"sq_{q}"):
            st.session_state["auto_input"] = q

    st.markdown("---")
    st.markdown("**🧠 GDS algorithms used**")
    st.markdown("""
| Question | Algorithm |
|---|---|
| Shortest route | Dijkstra |
| Temples nearby | BFS |
| Best hub city | Betweenness |
| Top temple | PageRank |
| Circuits | Louvain |
""")
    st.markdown("---")
    st.markdown("**🗺️ Node legend**")
    for label, color in NODE_COLORS.items():
        st.markdown(
            f'<span style="display:inline-block;width:12px;height:12px;'
            f'background:{color};border-radius:50%;margin-right:6px;"></span>'
            f'<span style="font-size:13px">{label}</span>',
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<span style="display:inline-block;width:12px;height:12px;'
        f'background:{HIGHLIGHT_COLOR};border-radius:50%;margin-right:6px;"></span>'
        f'<span style="font-size:13px">Route / highlighted</span>',
        unsafe_allow_html=True,
    )


# ── Main area ──────────────────────────────────────────────────────────────────

st.markdown("""
<div class="tirtha-header">
  <h1>🕉️ TirthaPathAI — South Indian Pilgrimage Route Planner</h1>
  <p>Powered by Neo4j GDS · Dijkstra · PageRank · Louvain · 32 sacred nodes
  &nbsp;|&nbsp; <a href="/🗺️_Pilgrimage_Network" style="color:#ffffffbb;">View full network map →</a></p>
</div>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Render past messages ───────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Agent runner ───────────────────────────────────────────────────────────────

def run_agent(user_prompt: str):
    from agent.agent import get_agent
    agent = get_agent()
    st.session_state.pop("route_nodes", None)  # clear previous question's highlight

    with st.chat_message("assistant"):
        with st.expander("🧠 Agent thinking…", expanded=False):
            thought_area = st.empty()

        answer_area  = st.empty()
        thoughts_md  = []
        final_answer = ""

        try:
            for chunk in agent.stream(
                {"messages": [HumanMessage(content=user_prompt)]},
                stream_mode="updates",
            ):
                # ── Agent node ────────────────────────────────────────
                if "agent" in chunk:
                    for msg in chunk["agent"]["messages"]:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                tname = tc.get("name", "unknown")
                                args  = tc.get("args", {})
                                emoji, label, css = TOOL_META.get(
                                    tname, ("🔧", tname, "tag-path")
                                )
                                block = (
                                    f'<span class="tool-tag {css}">'
                                    f'{emoji} {label}</span>\n\n'
                                )

                                if tname == "gds_path_tool":
                                    alg = args.get("algorithm", "")
                                    src = args.get("source_name", "")
                                    tgt = args.get("target_name", "")
                                    dep = args.get("max_depth", "")
                                    if alg == "dijkstra":
                                        block += f"**Dijkstra:** `{src}` → `{tgt}`"
                                    else:
                                        block += f"**BFS:** from `{src}`, depth={dep}"
                                elif tname == "gds_analysis_tool":
                                    block += f"**{args.get('algorithm','').title()}** centrality, top {args.get('top_n',8)}"
                                else:
                                    block += "**Louvain** community detection"

                                thoughts_md.append(block)
                                thought_area.markdown(
                                    "\n\n---\n\n".join(thoughts_md),
                                    unsafe_allow_html=True,
                                )

                        elif hasattr(msg, "content") and msg.content:
                            final_answer = msg.content
                            answer_area.markdown(final_answer)

                # ── Tools node ────────────────────────────────────────
                elif "tools" in chunk:
                    for msg in chunk["tools"]["messages"]:
                        raw = getattr(msg, "content", str(msg))
                        try:
                            parsed = json.loads(raw)

                            # Accumulate route nodes — don't overwrite, so multi-path
                            # comparisons (e.g. "closest of A vs B") highlight both routes
                            if isinstance(parsed, dict) and "__route_nodes__" in parsed:
                                existing = st.session_state.get("route_nodes", [])
                                merged = list(dict.fromkeys(existing + parsed["__route_nodes__"]))
                                st.session_state["route_nodes"] = merged

                            if isinstance(parsed, dict) and "error" in parsed:
                                thoughts_md.append(f"⚠️ {parsed['error']}")
                            else:
                                preview = raw[:300] + ("…" if len(raw) > 300 else "")
                                thoughts_md.append(
                                    f"✅ Result received\n```\n{preview}\n```"
                                )
                        except Exception:
                            preview = raw[:250] + ("…" if len(raw) > 250 else "")
                            thoughts_md.append(f"✅ `{preview}`")

                        thought_area.markdown(
                            "\n\n---\n\n".join(thoughts_md),
                            unsafe_allow_html=True,
                        )

        except Exception as e:
            final_answer = f"❌ Error: {e}"
            answer_area.error(final_answer)

        if final_answer:
            st.session_state.messages.append(
                {"role": "assistant", "content": final_answer}
            )

        # Render route graph inline below the answer
        route_nodes = st.session_state.get("route_nodes")
        if route_nodes:
            nodes_raw, edges_raw = fetch_graph_data()
            if nodes_raw:
                st.caption("🗺️ Route highlighted below — orange nodes are your path")
                render_pilgrim_graph(nodes_raw, edges_raw, highlighted=route_nodes, height=420)


# ── Input ──────────────────────────────────────────────────────────────────────
auto = st.session_state.pop("auto_input", None) if "auto_input" in st.session_state else None
prompt = st.chat_input("Ask your yatra question…") or auto

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    run_agent(prompt)
