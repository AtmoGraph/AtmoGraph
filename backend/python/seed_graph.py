from backend.python.db import Neo4jConnection


NODES = [
    {
        "label": "Supplier",
        "id": "supplier-sweden",
        "name": "Nordic Minerals",
        "location": "Kiruna, Sweden",
        "risk": "medium",
        "risk_score": 0.5,
        "capacity": 82,
        "aliases": ["Nordic Minerals", "Nordic Metals"],
    },
    {
        "label": "Port",
        "id": "port-rotterdam",
        "name": "Port of Rotterdam",
        "location": "Rotterdam, Netherlands",
        "risk": "high",
        "risk_score": 0.9,
        "capacity": 54,
        "aliases": ["Port of Rotterdam", "Rotterdam Port", "Rotterdam"],
    },
    {
        "label": "Supplier",
        "id": "supplier-taiwan",
        "name": "Silica Systems",
        "location": "Hsinchu, Taiwan",
        "risk": "low",
        "risk_score": 0.2,
        "capacity": 94,
        "aliases": ["Silica Systems"],
    },
    {
        "label": "Factory",
        "id": "factory-india",
        "name": "Atlas Assembly",
        "location": "Pune, India",
        "risk": "medium",
        "risk_score": 0.5,
        "capacity": 76,
        "aliases": ["Atlas Assembly"],
    },
    {
        "label": "Port",
        "id": "port-singapore",
        "name": "Port of Singapore",
        "location": "Singapore",
        "risk": "low",
        "risk_score": 0.2,
        "capacity": 91,
        "aliases": ["Port of Singapore", "Singapore Port"],
    },
    {
        "label": "DistributionCentre",
        "id": "distribution-usa",
        "name": "North America DC",
        "location": "Chicago, USA",
        "risk": "medium",
        "risk_score": 0.5,
        "capacity": 73,
        "aliases": ["North America DC", "Chicago Distribution Centre"],
    },
    {
        "label": "Market",
        "id": "market-europe",
        "name": "European Market",
        "location": "Berlin, Germany",
        "risk": "high",
        "risk_score": 0.9,
        "capacity": 61,
        "aliases": ["European Market"],
    },
]


RELATIONSHIPS = [
    ("supplier-sweden", "SUPPLIES", "port-rotterdam"),
    ("port-rotterdam", "SHIPS_TO", "factory-india"),
    ("supplier-taiwan", "SUPPLIES", "factory-india"),
    ("factory-india", "SHIPS_TO", "port-singapore"),
    ("factory-india", "SERVES", "market-europe"),
    ("port-singapore", "SHIPS_TO", "distribution-usa"),
    ("port-rotterdam", "SERVES", "market-europe"),
]


def create_constraints(session):
    session.run(
        """
        CREATE CONSTRAINT supply_chain_node_id IF NOT EXISTS
        FOR (node:SupplyChainNode)
        REQUIRE node.id IS UNIQUE
        """
    )


def create_nodes(session):
    allowed_labels = {
        "Supplier",
        "Port",
        "Factory",
        "DistributionCentre",
        "Market",
    }

    for node in NODES:
        label = node["label"]

        if label not in allowed_labels:
            raise ValueError(f"Unsupported node label: {label}")

        properties = {
            key: value
            for key, value in node.items()
            if key != "label"
        }

        session.run(
            f"""
            MERGE (node:SupplyChainNode:{label} {{id: $id}})
            SET node += $properties
            """,
            id=node["id"],
            properties=properties,
        )


def create_relationships(session):
    allowed_types = {"SUPPLIES", "SHIPS_TO", "SERVES"}

    for source_id, relationship_type, target_id in RELATIONSHIPS:
        if relationship_type not in allowed_types:
            raise ValueError(
                f"Unsupported relationship type: {relationship_type}"
            )

        session.run(
            f"""
            MATCH (source:SupplyChainNode {{id: $source_id}})
            MATCH (target:SupplyChainNode {{id: $target_id}})
            MERGE (source)-[:{relationship_type}]->(target)
            """,
            source_id=source_id,
            target_id=target_id,
        )


def main():
    db = Neo4jConnection()

    try:
        with db.driver.session(database="neo4j") as session:
            create_constraints(session)
            create_nodes(session)
            create_relationships(session)

            result = session.run(
                """
                MATCH (node:SupplyChainNode)
                WITH count(node) AS nodes
                OPTIONAL MATCH (:SupplyChainNode)-[relationship]->(:SupplyChainNode)
                RETURN nodes, count(relationship) AS relationships
                """
            )

            summary = result.single()

            print(
                f"Graph seeded successfully: "
                f"{summary['nodes']} nodes, "
                f"{summary['relationships']} relationships"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()