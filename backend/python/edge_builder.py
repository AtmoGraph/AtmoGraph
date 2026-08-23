from backend.python.graph_loader import load_nodes, load_relationships
from backend.python.db import Neo4jConnection


RELATIONSHIP_TYPES = [
    "SUPPLIES",
    "PRODUCES",
    "USES_PORT",
    "FROM",
    "TO",
    "SERVES",
    "DISTRIBUTES_TO",
    "AFFECTS",
    "SHIPS_TO",
]


def create_node_mapping(nodes):
    """
    Convert Neo4j element IDs into integer node IDs.
    """

    return {
        node["neo4j_id"]: index
        for index, node in enumerate(nodes)
    }


def build_edges(relationships, node_mapping):
    """
    Convert Neo4j relationships into integer-indexed edges.
    """

    edges = []

    for relationship in relationships:

        source = node_mapping[
            relationship["source_neo4j_id"]
        ]

        target = node_mapping[
            relationship["target_neo4j_id"]
        ]

        relationship_type = (
            relationship["relationship_type"]
        )

        relationship_id = RELATIONSHIP_TYPES.index(
            relationship_type
        )

        edges.append({
            "source": source,
            "target": target,
            "type": relationship_id,
            "relationship_type": relationship_type,
            "properties": relationship["properties"],
        })

    return edges


def main():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            nodes = load_nodes(session)
            relationships = load_relationships(session)

            node_mapping = create_node_mapping(nodes)

            edges = build_edges(
                relationships,
                node_mapping
            )

            print("\n========== EDGE SUMMARY ==========")

            print(
                "Total edges:",
                len(edges)
            )

            print("\n========== EDGE TYPE MAPPING ==========")

            for index, relationship_type in enumerate(
                RELATIONSHIP_TYPES
            ):
                print(
                    f"{index} -> {relationship_type}"
                )

            print("\n========== SAMPLE EDGES ==========")

            for edge in edges:

                print(
                    f"{edge['source']} "
                    f"--[{edge['relationship_type']}]--> "
                    f"{edge['target']} "
                    f"(type={edge['type']})"
                )

    finally:

        db.close()


if __name__ == "__main__":
    main()