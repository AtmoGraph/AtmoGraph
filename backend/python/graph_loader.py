from collections import Counter

try:
    from backend.python.db import Neo4jConnection
except ImportError:
    from backend.python.db import Neo4jConnection


def load_nodes(session):
    query = """
    MATCH (n)
    RETURN
        elementId(n) AS neo4j_id,
        labels(n) AS labels,
        properties(n) AS properties
    """

    result = session.run(query)

    nodes = []

    for record in result:
        properties = record["properties"]

        nodes.append({
            "neo4j_id": record["neo4j_id"],
            "labels": record["labels"],
            "properties": properties
        })

    return nodes


def load_relationships(session):
    query = """
    MATCH (source)-[r]->(target)
    RETURN
        elementId(source) AS source_neo4j_id,
        elementId(target) AS target_neo4j_id,
        type(r) AS relationship_type,
        properties(r) AS properties
    """

    result = session.run(query)

    relationships = []

    for record in result:
        relationships.append({
            "source_neo4j_id": record["source_neo4j_id"],
            "target_neo4j_id": record["target_neo4j_id"],
            "relationship_type": record["relationship_type"],
            "properties": record["properties"]
        })

    return relationships


def create_node_mapping(nodes):
    """
    Convert Neo4j element IDs into sequential integer IDs.
    """

    node_mapping = {}

    for index, node in enumerate(nodes):
        node_mapping[node["neo4j_id"]] = index

    return node_mapping


def create_graph_edges(relationships, node_mapping):
    """
    Convert relationship source/target Neo4j IDs
    into integer source/target IDs.
    """

    edges = []

    for relationship in relationships:

        source_id = node_mapping[
            relationship["source_neo4j_id"]
        ]

        target_id = node_mapping[
            relationship["target_neo4j_id"]
        ]

        edges.append({
            "source": source_id,
            "target": target_id,
            "relationship_type": relationship["relationship_type"],
            "properties": relationship["properties"]
        })

    return edges


def main():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            # Load graph
            nodes = load_nodes(session)
            relationships = load_relationships(session)

            # Create Neo4j ID → integer ID mapping
            node_mapping = create_node_mapping(nodes)

            # Convert relationships
            edges = create_graph_edges(
                relationships,
                node_mapping
            )

            # ==========================
            # GRAPH SUMMARY
            # ==========================

            print("\n========== GRAPH SUMMARY ==========")

            print("Total nodes:", len(nodes))
            print("Total relationships:", len(relationships))

            # ==========================
            # NODE TYPES
            # ==========================

            node_types = Counter()

            for node in nodes:

                for label in node["labels"]:
                    node_types[label] += 1

            print("\n========== NODE TYPES ==========")

            for node_type, count in sorted(node_types.items()):
                print(f"{node_type}: {count}")

            # ==========================
            # NODE MAPPING
            # ==========================

            print("\n========== NODE MAPPING ==========")

            for node in nodes[:10]:

                neo4j_id = node["neo4j_id"]
                integer_id = node_mapping[neo4j_id]

                properties = node["properties"]

                print(
                    f"{integer_id} -> "
                    f"{properties.get('id')} -> "
                    f"{properties.get('name')}"
                )

            # ==========================
            # EDGES
            # ==========================

            print("\n========== GRAPH EDGES ==========")

            for edge in edges[:10]:

                print(
                    f"{edge['source']} "
                    f"--[{edge['relationship_type']}]--> "
                    f"{edge['target']}"
                )

    finally:

        db.close()


if __name__ == "__main__":
    main()