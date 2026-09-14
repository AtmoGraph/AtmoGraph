from backend.python.canonical_gnn_graph import load_canonical_gnn_graph
from backend.python.db import Neo4jConnection


ALLOWED_LABELS = {
    "Port",
    "Manufacturer",
    "Product",
    "Warehouse",
    "Market",
    "ShippingRoute",
}

ALLOWED_RELATIONSHIP_TYPES = {
    "USES_PORT",
    "PRODUCES",
    "FROM",
    "TO",
    "SERVES",
    "DISTRIBUTES_TO",
}


def risk_label(score):
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def load_seed_data():
    canonical_nodes, canonical_relationships = load_canonical_gnn_graph()

    nodes = []

    for item in canonical_nodes:
        label = item["labels"][0]
        properties = dict(item["properties"])
        score = float(properties.get("risk_score", 0.2))

        properties.setdefault("risk_score", score)
        properties.setdefault("risk", risk_label(score))
        properties.setdefault(
            "capacity",
            properties.get("production_capacity", 100),
        )
        properties.setdefault("aliases", [properties["name"]])

        nodes.append({
            "label": label,
            **properties,
        })

    relationships = [
        (
            relationship["source_neo4j_id"],
            relationship["relationship_type"],
            relationship["target_neo4j_id"],
        )
        for relationship in canonical_relationships
    ]

    return nodes, relationships


def create_constraints(session):
    session.run(
        """
        CREATE CONSTRAINT supply_chain_node_id IF NOT EXISTS
        FOR (node:SupplyChainNode)
        REQUIRE node.id IS UNIQUE
        """
    )

def create_nodes(session, nodes):
    for node in nodes:
        label = node["label"]

        if label not in ALLOWED_LABELS:
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


def create_relationships(session, relationships):
    for source_id, relationship_type, target_id in relationships:
        if relationship_type not in ALLOWED_RELATIONSHIP_TYPES:
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
    nodes, relationships = load_seed_data()
    db = Neo4jConnection()

    try:
        with db.driver.session(database="neo4j") as session:
            create_constraints(session)
            create_nodes(session, nodes)
            create_relationships(session, relationships)

            result = session.run(
                """
                MATCH (node:SupplyChainNode)
                WITH count(node) AS nodes
                OPTIONAL MATCH
                  (:SupplyChainNode)-[relationship]->(:SupplyChainNode)
                RETURN nodes, count(relationship) AS relationships
                """
            )

            summary = result.single()

            print(
                "Graph seeded successfully: "
                f"{summary['nodes']} nodes, "
                f"{summary['relationships']} relationships"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()