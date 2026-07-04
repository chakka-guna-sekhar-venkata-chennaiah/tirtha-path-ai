"""
TirthaPathAI — Three LangChain tools backed by Neo4j GDS algorithms.

  1. gds_path_tool        → Dijkstra shortest path + BFS reachability
  2. gds_analysis_tool    → PageRank, Betweenness, Closeness centrality
  3. gds_community_tool   → Louvain community (pilgrimage circuits)
"""
import json
import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.tools import tool
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

GDS_GRAPH = "tirtha-graph"


def _driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def _ensure_projection(session):
    """Re-create GDS projection if DB restarted and dropped it from memory."""
    names = session.run(
        "CALL gds.graph.list() YIELD graphName RETURN collect(graphName) AS n"
    ).single()["n"]
    if GDS_GRAPH not in names:
        session.run(f"""
            CALL gds.graph.project(
                '{GDS_GRAPH}',
                ['Temple', 'City'],
                {{
                    ROAD_CONNECTS: {{
                        orientation: 'UNDIRECTED',
                        properties: ['distance_km', 'duration_hours']
                    }}
                }}
            )
        """)


# ── Tool 1: Path finding ───────────────────────────────────────────────────────

@tool
def gds_path_tool(
    algorithm: str,
    source_name: str,
    target_name: Optional[str] = None,
    max_depth: Optional[int] = 2,
) -> str:
    """
    Find pilgrimage routes using Neo4j GDS path algorithms.

    algorithm='dijkstra'
        Finds the shortest road route (by distance_km) between two nodes.
        Requires: source_name AND target_name
        Returns: ordered list of nodes, total km, cumulative distances

    algorithm='bfs'
        Finds all temples/cities reachable within max_depth road hops.
        Requires: source_name AND max_depth (default 2)
        Returns: list of reachable nodes sorted by hops

    All node names must exactly match the 32-node pilgrimage network:
    City hubs: Vijayawada, Hyderabad, Chennai, Tirupati, Guntur, Visakhapatnam,
               Nellore, Kurnool, Rajahmundry, Warangal, Trichy, Madurai
    Temples:   Tirumala, Srisailam, Kanaka Durga, Mahanandi, Ahobilam, Annavaram,
               Simhachalam, Srikalahasti, Bhadrachalam, Yadadri, Vemulawada, Basara,
               Keesaragutta, Rameswaram, Meenakshi Temple, Kamakshi Kanchipuram,
               Tiruvannamalai, Chidambaram, Srirangam, Thanjavur
    """
    try:
        driver = _driver()
        with driver.session() as s:
            _ensure_projection(s)

            if algorithm == "dijkstra":
                if not target_name:
                    return json.dumps({"error": "target_name required for dijkstra"})

                result = s.run("""
                    MATCH (src {name: $src})
                    MATCH (tgt {name: $tgt})
                    CALL gds.shortestPath.dijkstra.stream($graph, {
                        sourceNode: src,
                        targetNode: tgt,
                        relationshipWeightProperty: 'distance_km'
                    })
                    YIELD totalCost, nodeIds, costs
                    RETURN
                        [nid IN nodeIds | gds.util.asNode(nid).name] AS route,
                        round(totalCost)                              AS total_km,
                        [c IN costs | round(c)]                      AS cumulative_km,
                        size(nodeIds) - 1                            AS hops
                """, src=source_name, tgt=target_name, graph=GDS_GRAPH).single()

                if not result:
                    return json.dumps({"error": f"No path found from {source_name} to {target_name}"})

                route    = result["route"]
                total_km = result["total_km"]
                cum_km   = result["cumulative_km"]
                hops     = result["hops"]

                # Estimate total hours (avg 55 km/h on Indian highways)
                est_hours = round(total_km / 55, 1)

                # Enrich each stop with node metadata
                stops = []
                for i, name in enumerate(route):
                    meta = s.run("""
                        MATCH (n {name: $name})
                        RETURN labels(n) AS labels,
                               n.deity_form AS deity_form,
                               n.state AS state,
                               n.significance AS significance
                    """, name=name).single()

                    stop = {
                        "name":        name,
                        "km_from_start": int(cum_km[i]) if i < len(cum_km) else int(total_km),
                        "labels":      meta["labels"] if meta else [],
                        "deity_form":  meta["deity_form"] if meta else None,
                        "state":       meta["state"] if meta else None,
                        "significance":meta["significance"] if meta else None,
                    }
                    stops.append(stop)

                payload = {
                    "algorithm":    "dijkstra",
                    "source":       source_name,
                    "target":       target_name,
                    "total_km":     int(total_km),
                    "est_hours":    est_hours,
                    "hops":         hops,
                    "stops":        stops,
                    "__route_nodes__": route,    # used by UI for path highlighting
                }
                driver.close()
                return json.dumps(payload, ensure_ascii=False)

            elif algorithm == "bfs":
                depth = max_depth or 2

                results = s.run("""
                    MATCH (src {name: $src})
                    CALL gds.bfs.stream($graph, {
                        sourceNode: id(src),
                        maxDepth:   $depth
                    })
                    YIELD nodeIds
                    UNWIND nodeIds AS nid
                    WITH gds.util.asNode(nid) AS node
                    WHERE node.name <> $src
                    RETURN node.name     AS name,
                           labels(node)  AS labels,
                           node.state    AS state,
                           node.deity_form AS deity_form
                """, src=source_name, graph=GDS_GRAPH, depth=depth).data()

                temples = [r for r in results if "Temple" in r["labels"]]
                cities  = [r for r in results if "City"   in r["labels"]]

                payload = {
                    "algorithm":    "bfs",
                    "source":       source_name,
                    "max_depth":    depth,
                    "total_reachable": len(results),
                    "temples_reachable": len(temples),
                    "temples": [{"name": r["name"], "deity_form": r["deity_form"], "state": r["state"]}
                                for r in temples],
                    "city_hubs": [r["name"] for r in cities],
                    "__route_nodes__": [source_name] + [r["name"] for r in results],
                }
                driver.close()
                return json.dumps(payload, ensure_ascii=False)

            else:
                driver.close()
                return json.dumps({"error": f"Unknown algorithm '{algorithm}'. Use 'dijkstra' or 'bfs'."})

    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Tool 2: Centrality analysis ────────────────────────────────────────────────

@tool
def gds_analysis_tool(
    algorithm: str,
    top_n: int = 8,
) -> str:
    """
    Analyse the pilgrimage network using Neo4j GDS centrality algorithms.

    algorithm='pagerank'
        Ranks nodes by their importance in the network (like Google PageRank).
        High score = highly connected, many routes pass through here.
        Use when asked: "most important temple", "most visited in network", "top sites"

    algorithm='betweenness'
        Ranks nodes by how often they appear on shortest paths between other nodes.
        High score = best transit hub for pilgrims.
        Use when asked: "best hub city", "most central place", "best base to visit temples"

    algorithm='closeness'
        Ranks nodes by how close they are on average to every other node.
        High score = can reach all other temples fastest from here.
        Use when asked: "most accessible place", "closest to everything"

    top_n: how many top results to return (default 8)
    """
    try:
        driver = _driver()
        with driver.session() as s:
            _ensure_projection(s)

            if algorithm == "pagerank":
                rows = s.run("""
                    CALL gds.pageRank.stream($graph, {
                        maxIterations: 20,
                        dampingFactor: 0.85
                    })
                    YIELD nodeId, score
                    WITH gds.util.asNode(nodeId) AS node, score
                    RETURN
                        node.name                                           AS name,
                        CASE WHEN 'Temple' IN labels(node)
                             THEN node.deity_form ELSE 'City hub' END       AS role,
                        node.state                                          AS state,
                        CASE WHEN 'Temple' IN labels(node)
                             THEN 'Temple' ELSE 'City' END                  AS type,
                        round(score * 1000) / 1000                         AS score
                    ORDER BY score DESC
                    LIMIT $top_n
                """, graph=GDS_GRAPH, top_n=top_n).data()

                driver.close()
                return json.dumps({
                    "algorithm": "pagerank",
                    "description": "Most influential nodes in the pilgrimage network",
                    "rankings": rows,
                }, ensure_ascii=False)

            elif algorithm == "betweenness":
                rows = s.run("""
                    CALL gds.betweenness.stream($graph)
                    YIELD nodeId, score
                    WITH gds.util.asNode(nodeId) AS node, score
                    RETURN
                        node.name                                           AS name,
                        CASE WHEN 'Temple' IN labels(node)
                             THEN node.deity_form ELSE 'City hub' END       AS role,
                        node.state                                          AS state,
                        CASE WHEN 'Temple' IN labels(node)
                             THEN 'Temple' ELSE 'City' END                  AS type,
                        round(score)                                        AS score
                    ORDER BY score DESC
                    LIMIT $top_n
                """, graph=GDS_GRAPH, top_n=top_n).data()

                driver.close()
                return json.dumps({
                    "algorithm": "betweenness",
                    "description": "Best transit hubs — appear most on shortest paths",
                    "rankings": rows,
                }, ensure_ascii=False)

            elif algorithm == "closeness":
                rows = s.run("""
                    CALL gds.closeness.stream($graph)
                    YIELD nodeId, score
                    WITH gds.util.asNode(nodeId) AS node, score
                    RETURN
                        node.name                                           AS name,
                        CASE WHEN 'Temple' IN labels(node)
                             THEN node.deity_form ELSE 'City hub' END       AS role,
                        node.state                                          AS state,
                        CASE WHEN 'Temple' IN labels(node)
                             THEN 'Temple' ELSE 'City' END                  AS type,
                        round(score * 1000) / 1000                         AS score
                    ORDER BY score DESC
                    LIMIT $top_n
                """, graph=GDS_GRAPH, top_n=top_n).data()

                driver.close()
                return json.dumps({
                    "algorithm": "closeness",
                    "description": "Nodes closest on average to every other node",
                    "rankings": rows,
                }, ensure_ascii=False)

            else:
                driver.close()
                return json.dumps({
                    "error": f"Unknown algorithm '{algorithm}'. Use 'pagerank', 'betweenness', or 'closeness'."
                })

    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Tool 3: Community / circuit detection ──────────────────────────────────────

@tool
def gds_community_tool() -> str:
    """
    Detect natural pilgrimage circuits using the Louvain community detection algorithm.

    The Louvain algorithm groups nodes that are densely connected to each other into
    communities. For our pilgrimage network, these communities correspond to natural
    geographic pilgrimage circuits — e.g. an AP circuit, a Telangana circuit, a TN circuit.

    Use when asked:
    - "What are the natural pilgrimage circuits?"
    - "Group temples into clusters"
    - "Plan a circuit yatra"
    - "Which temples are close to each other?"
    - "Weekend pilgrimage suggestions"
    """
    try:
        driver = _driver()
        with driver.session() as s:
            _ensure_projection(s)

            rows = s.run("""
                CALL gds.louvain.stream($graph)
                YIELD nodeId, communityId
                WITH gds.util.asNode(nodeId) AS node, communityId
                WITH communityId,
                     collect(node.name)                                AS members,
                     collect(CASE WHEN 'Temple' IN labels(node)
                                  THEN node.name ELSE null END)        AS temples,
                     collect(CASE WHEN 'City'   IN labels(node)
                                  THEN node.name ELSE null END)        AS cities,
                     count(*)                                          AS total_size
                ORDER BY total_size DESC
                RETURN communityId,
                       [t IN temples WHERE t IS NOT NULL]              AS temples,
                       [c IN cities  WHERE c IS NOT NULL]              AS hubs,
                       total_size
            """, graph=GDS_GRAPH).data()

        driver.close()

        # Label each circuit meaningfully
        circuits = []
        for i, row in enumerate(rows):
            states = set()
            for t in row["temples"]:
                # Rough geographic labelling
                if any(n in t for n in ["Tirumala","Srisailam","Kanaka","Mahanandi","Ahobilam","Annavaram","Simhachalam","Srikalahasti"]):
                    states.add("Andhra Pradesh")
                if any(n in t for n in ["Bhadrachalam","Yadadri","Vemulawada","Basara","Keesaragutta"]):
                    states.add("Telangana")
                if any(n in t for n in ["Rameswaram","Meenakshi","Kamakshi","Tiruvannamalai","Chidambaram","Srirangam","Thanjavur"]):
                    states.add("Tamil Nadu")

            label = " + ".join(sorted(states)) if states else f"Circuit {i+1}"
            circuits.append({
                "circuit_id":    i + 1,
                "label":         label,
                "temples":       row["temples"],
                "transit_hubs":  row["hubs"],
                "total_nodes":   row["total_size"],
            })

        return json.dumps({
            "algorithm":        "louvain",
            "description":      "Natural pilgrimage circuits detected by community analysis",
            "total_circuits":   len(circuits),
            "circuits":         circuits,
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)})
