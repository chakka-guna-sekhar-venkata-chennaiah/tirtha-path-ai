"""
Full 32-node pilgrimage network map — static view for exploration.
"""
import os
import tempfile

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Pilgrimage Network", page_icon="🗺️", layout="wide")

NODE_COLORS = {
    "City":      "#2a78d6",
    "Vishnu":    "#1baf7a",
    "Shiva":     "#7c5cbf",
    "Shakti":    "#e34948",
    "Saraswati": "#eda100",
}
NODE_SIZES = {"City": 24, "Vishnu": 20, "Shiva": 20, "Shakti": 20, "Saraswati": 20}


def get_driver():
    from neo4j import GraphDatabase
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")),
    )


@st.cache_data(ttl=300, show_spinner=False)
def fetch_graph_data():
    try:
        driver = get_driver()
        with driver.session() as s:
            nodes = s.run("""
                MATCH (n)
                RETURN n.name AS name, labels(n) AS labels,
                       n.deity_form AS deity_form, n.state AS state,
                       n.significance AS significance, n.role AS role
            """).data()
            edges = s.run("""
                MATCH (a)-[r:ROAD_CONNECTS]->(b) WHERE id(a) < id(b)
                RETURN a.name AS src, b.name AS tgt,
                       r.distance_km AS km, r.duration_hours AS hrs
            """).data()
        driver.close()
        return nodes, edges
    except Exception as e:
        return None, str(e)


def render_network(nodes_raw, edges_raw, height=600):
    from pyvis.network import Network
    net = Network(height=f"{height}px", width="100%", bgcolor="#1a1a2e",
                  font_color="#e8e8e8", directed=False, notebook=False)
    net.barnes_hut(gravity=-6000, central_gravity=0.25,
                   spring_length=140, spring_strength=0.05)

    for n in nodes_raw:
        name, labels = n["name"], n["labels"] or []
        if "City" in labels:
            color, size = NODE_COLORS["City"], NODE_SIZES["City"]
        else:
            color, size = "#888780", 18
            for deity in ("Vishnu", "Shiva", "Shakti", "Saraswati"):
                if deity in labels:
                    color, size = NODE_COLORS[deity], NODE_SIZES[deity]
                    break
        role  = n.get("deity_form") or n.get("role") or ""
        state = n.get("state") or ""
        sig   = n.get("significance") or ""
        tip   = f"<b>{name}</b><br>{role}<br>{state}"
        if sig:
            tip += f"<br><i>{sig[:80]}</i>"
        net.add_node(name, label=name, title=tip,
                     color={"background": color, "border": "#ffffff44"},
                     size=size, font={"size": 11, "color": "#ffffff"})

    for e in edges_raw:
        net.add_edge(e["src"], e["tgt"],
                     title=f"{e['km']} km / ~{e['hrs']}h",
                     label=f"{int(e['km'])}km" if e.get("km") else "",
                     color="#ffffff33", width=1,
                     font={"size": 8, "color": "#cccccc", "align": "middle"})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
        net.save_graph(f.name)
        html = open(f.name, encoding="utf-8").read()
    components.html(html, height=height + 20, scrolling=False)


st.markdown("## 🗺️ Full Pilgrimage Network — 32 Sacred Nodes")
st.caption("20 temples · 12 city hubs · 32 road connections | Click nodes to explore")

st.markdown("**Legend:**")
cols = st.columns(len(NODE_COLORS))
for col, (label, color) in zip(cols, NODE_COLORS.items()):
    col.markdown(
        f'<span style="display:inline-block;width:12px;height:12px;background:{color};'
        f'border-radius:50%;margin-right:6px;"></span>{label}',
        unsafe_allow_html=True,
    )

nodes_raw, edges_raw = fetch_graph_data()
if nodes_raw:
    render_network(nodes_raw, edges_raw, height=620)
else:
    st.error(f"Could not connect to Neo4j: {edges_raw}")
