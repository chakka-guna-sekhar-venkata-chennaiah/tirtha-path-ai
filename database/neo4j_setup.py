"""
TirthaPathAI — Neo4j database setup.

Exactly 32 nodes  : 20 Temple nodes + 12 City nodes
Exactly 32 edges  : ROAD_CONNECTS {distance_km, duration_hours}
GDS projection    : 'tirtha-graph' (undirected, weighted by distance_km)

Run once:  python database/neo4j_setup.py
"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# ── 20 Temple nodes ─────────────────────────────────────────────────────────
# (name, deity_label, deity_form, state, significance, lat, lng)
TEMPLES = [
    # Andhra Pradesh (8)
    ("Tirumala",                "Vishnu",     "Venkateswara (Balaji)",          "Andhra Pradesh", "Richest temple, Saptagiri hills",              13.6833,  79.3667),
    ("Srisailam",               "Shiva",      "Mallikarjuna (Jyotirlinga)",     "Andhra Pradesh", "One of 12 Jyotirlingas, Shakti Peetha",        16.0723,  78.8682),
    ("Kanaka Durga",            "Shakti",     "Kanaka Durga",                   "Andhra Pradesh", "Shakti Peetha, Inrakeeladri hill, Vijayawada", 16.5157,  80.6027),
    ("Mahanandi",               "Shiva",      "Mahanandiswara",                 "Andhra Pradesh", "Nava Nandis circuit, 7th century Chalukya",    15.1847,  78.5028),
    ("Ahobilam",                "Vishnu",     "Narasimha (9 forms)",            "Andhra Pradesh", "Nava Narasimha Kshetram, Nallamala hills",     15.1417,  78.6595),
    ("Annavaram",               "Vishnu",     "Veera Venkata Satyanarayana",    "Andhra Pradesh", "Ratnagiri hills, banks of Pampa river",        17.0264,  82.0451),
    ("Simhachalam",             "Vishnu",     "Varaha Narasimha",               "Andhra Pradesh", "11th century Chalukya, Vizag hills",           17.7643,  83.2669),
    ("Srikalahasti",            "Shiva",      "Srikalahasteeswara (Vayu Linga)","Andhra Pradesh", "Pancha Bhuta Stala — Air element",             13.7493,  79.6985),
    # Telangana (5)
    ("Bhadrachalam",            "Vishnu",     "Sita Ramachandra Swamy",         "Telangana",      "Godavari riverside Rama temple",               17.6688,  80.8930),
    ("Yadadri",                 "Vishnu",     "Pancha Narasimha",               "Telangana",      "5 Narasimha forms, Yadagirigutta hill",        17.5779,  78.9243),
    ("Vemulawada",              "Shiva",      "Rajrajeswara (Bhima Lingam)",    "Telangana",      "Vemulawada Rajanna, major Telangana shrine",   18.4802,  78.8665),
    ("Basara",                  "Saraswati",  "Gnana Saraswati",                "Telangana",      "Vidya Peetha, Godavari banks, Saraswati",      18.8654,  78.0041),
    ("Keesaragutta",            "Shiva",      "Keesaragutta Ramalingeshwara",   "Telangana",      "Ancient Shiva temple in forest near Hyderabad",17.5693,  78.7718),
    # Tamil Nadu (7)
    ("Rameswaram",              "Shiva",      "Ramanatha (Jyotirlinga)",        "Tamil Nadu",     "Jyotirlinga + Char Dham, Sethu island",         9.2885,  79.3174),
    ("Meenakshi Temple",        "Shakti",     "Meenakshi Amman",                "Tamil Nadu",     "Madurai, 14 coloured gopurams, 2500 years",     9.9195,  78.1193),
    ("Kamakshi Kanchipuram",    "Shakti",     "Kamakshi Amman",                 "Tamil Nadu",     "Shakti Peetha, Kanchi Mutt headquarters",      12.8395,  79.7003),
    ("Tiruvannamalai",          "Shiva",      "Arunachaleswarar (Agni Linga)",  "Tamil Nadu",     "Pancha Bhuta — Fire, Arunachala girivalam",    12.2253,  79.0674),
    ("Chidambaram",             "Shiva",      "Nataraja (Akasha Lingam)",       "Tamil Nadu",     "Pancha Bhuta — Ether/Space, cosmic dance",     11.3992,  79.6930),
    ("Srirangam",               "Vishnu",     "Ranganatha (Adi Ranga)",         "Tamil Nadu",     "Largest functioning Hindu temple complex",      10.8651,  78.6896),
    ("Thanjavur",               "Shiva",      "Brihadeeswarar",                 "Tamil Nadu",     "UNESCO World Heritage, Chola masterpiece",      10.7832,  79.1318),
]

# ── 12 City/hub nodes ───────────────────────────────────────────────────────
CITIES = [
    # (name, state, role)
    ("Vijayawada",    "Andhra Pradesh", "Major transit hub, Krishna river"),
    ("Hyderabad",     "Telangana",      "Metro hub, Charminar, IT capital"),
    ("Chennai",       "Tamil Nadu",     "Coastal metro, major rail/air hub"),
    ("Tirupati",      "Andhra Pradesh", "Pilgrim city, gateway to Tirumala"),
    ("Guntur",        "Andhra Pradesh", "Trade city, near Amaravathi"),
    ("Visakhapatnam", "Andhra Pradesh", "Port city, Vizag, coast"),
    ("Nellore",       "Andhra Pradesh", "Southern AP transit town"),
    ("Kurnool",       "Andhra Pradesh", "Gateway to Rayalaseema temples"),
    ("Rajahmundry",   "Andhra Pradesh", "Godavari delta, cultural capital"),
    ("Warangal",      "Telangana",      "Kakatiya heritage, north Telangana"),
    ("Trichy",        "Tamil Nadu",     "Central TN hub, Kaveri delta"),
    ("Madurai",       "Tamil Nadu",     "Temple city, South TN hub"),
]

# ── 32 ROAD_CONNECTS relationships ──────────────────────────────────────────
# EXACTLY 32 edges — do not add or remove
# (from_name, to_name, distance_km, duration_hours)
ROADS = [
    # Vijayawada spokes (5)
    ("Vijayawada",    "Kanaka Durga",           5,   0.1),
    ("Vijayawada",    "Guntur",                55,   1.0),
    ("Vijayawada",    "Hyderabad",            275,   4.5),
    ("Vijayawada",    "Rajahmundry",          178,   3.0),
    ("Vijayawada",    "Nellore",              165,   2.8),
    # Hyderabad spokes (7)
    ("Hyderabad",     "Yadadri",               80,   1.5),
    ("Hyderabad",     "Vemulawada",           210,   3.5),
    ("Hyderabad",     "Basara",               220,   4.0),
    ("Hyderabad",     "Srisailam",            212,   4.0),
    ("Hyderabad",     "Kurnool",              215,   3.5),
    ("Hyderabad",     "Keesaragutta",          25,   0.5),
    ("Hyderabad",     "Warangal",             145,   2.5),
    # Warangal spoke (1)
    ("Warangal",      "Bhadrachalam",         180,   3.5),
    # Kurnool spokes (3)
    ("Kurnool",       "Srisailam",            183,   3.5),
    ("Kurnool",       "Mahanandi",             90,   1.8),
    ("Kurnool",       "Ahobilam",             140,   2.5),
    # Nellore spoke (1)
    ("Nellore",       "Tirupati",             110,   2.0),
    # Tirupati spokes (3)
    ("Tirupati",      "Tirumala",              22,   0.5),
    ("Tirupati",      "Srikalahasti",          35,   0.7),
    ("Tirupati",      "Chennai",              135,   2.5),
    # Rajahmundry spokes (2)
    ("Rajahmundry",   "Annavaram",             84,   1.5),
    ("Rajahmundry",   "Visakhapatnam",        180,   3.0),
    # Visakhapatnam spoke (1)
    ("Visakhapatnam", "Simhachalam",           16,   0.4),
    # Chennai spokes (3)
    ("Chennai",       "Kamakshi Kanchipuram",  75,   1.5),
    ("Chennai",       "Tiruvannamalai",       190,   3.5),
    ("Chennai",       "Trichy",               328,   5.5),
    # Trichy spokes (3)
    ("Trichy",        "Srirangam",              5,   0.2),
    ("Trichy",        "Thanjavur",             57,   1.2),
    ("Trichy",        "Madurai",              140,   2.5),
    # Madurai spokes (2)
    ("Madurai",       "Meenakshi Temple",       2,   0.1),
    ("Madurai",       "Rameswaram",           167,   3.0),
    # TN chain (1)
    ("Tiruvannamalai","Chidambaram",          100,   2.0),
]

assert len(TEMPLES) == 20, f"Expected 20 temples, got {len(TEMPLES)}"
assert len(CITIES)  == 12, f"Expected 12 cities, got {len(CITIES)}"
assert len(ROADS)   == 32, f"Expected 32 roads, got {len(ROADS)}"


def setup_neo4j():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as s:

        # ── Wipe existing data + projections ────────────────────────
        print("🧹 Clearing existing data…")
        try:
            s.run("CALL gds.graph.drop('tirtha-graph', false) YIELD graphName")
        except Exception:
            pass
        s.run("MATCH (n) DETACH DELETE n")

        # ── Constraints ─────────────────────────────────────────────
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Temple) REQUIRE n.name IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:City)   REQUIRE n.name IS UNIQUE")

        # ── Temple nodes ────────────────────────────────────────────
        print("🛕 Creating temple nodes…")
        for name, deity_label, deity_form, state, significance, lat, lng in TEMPLES:
            s.run(f"""
                CREATE (t:Temple:{deity_label} {{
                    name:         $name,
                    deity_label:  $deity_label,
                    deity_form:   $deity_form,
                    state:        $state,
                    significance: $significance,
                    lat:          $lat,
                    lng:          $lng
                }})
            """, name=name, deity_label=deity_label, deity_form=deity_form,
                 state=state, significance=significance, lat=lat, lng=lng)

        # ── City nodes ──────────────────────────────────────────────
        print("🏙️ Creating city nodes…")
        for name, state, role in CITIES:
            s.run("""
                CREATE (c:City {
                    name:  $name,
                    state: $state,
                    role:  $role
                })
            """, name=name, state=state, role=role)

        # ── ROAD_CONNECTS relationships ──────────────────────────────
        print("🛣️ Creating 32 road connections…")
        for src, tgt, dist_km, dur_hr in ROADS:
            s.run("""
                MATCH (a {name: $src})
                MATCH (b {name: $tgt})
                MERGE (a)-[:ROAD_CONNECTS {
                    distance_km:    $dist_km,
                    duration_hours: $dur_hr
                }]->(b)
                MERGE (b)-[:ROAD_CONNECTS {
                    distance_km:    $dist_km,
                    duration_hours: $dur_hr
                }]->(a)
            """, src=src, tgt=tgt, dist_km=float(dist_km), dur_hr=float(dur_hr))

        # ── GDS graph projection ─────────────────────────────────────
        print("📊 Creating GDS in-memory graph projection…")
        s.run("""
            CALL gds.graph.project(
                'tirtha-graph',
                ['Temple', 'City'],
                {
                    ROAD_CONNECTS: {
                        orientation: 'UNDIRECTED',
                        properties: ['distance_km', 'duration_hours']
                    }
                }
            )
        """)

        # ── Verify ──────────────────────────────────────────────────
        nc = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rc = s.run("MATCH ()-[r:ROAD_CONNECTS]->() RETURN count(r) AS c").single()["c"]
        gds_info = s.run(
            "CALL gds.graph.list('tirtha-graph') YIELD nodeCount, relationshipCount"
        ).single()

        print(f"\n✅ Neo4j setup complete!")
        print(f"   Nodes              : {nc}  (expected 32)")
        print(f"   Relationships (dir): {rc}  (expected 64 — 32 roads × 2 directions)")
        print(f"   GDS nodes          : {gds_info['nodeCount']}")
        print(f"   GDS relationships  : {gds_info['relationshipCount']}")

    driver.close()


def ensure_projection(session):
    """Re-create GDS projection if it was dropped (e.g. after DB restart)."""
    result = session.run(
        "CALL gds.graph.list() YIELD graphName RETURN collect(graphName) AS names"
    ).single()
    if "tirtha-graph" not in result["names"]:
        session.run("""
            CALL gds.graph.project(
                'tirtha-graph',
                ['Temple', 'City'],
                {
                    ROAD_CONNECTS: {
                        orientation: 'UNDIRECTED',
                        properties: ['distance_km', 'duration_hours']
                    }
                }
            )
        """)
        return True
    return False


if __name__ == "__main__":
    setup_neo4j()
