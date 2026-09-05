import pytest
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from backend.nlp.neo4j_writer import write_analysis
from backend.nlp.pipeline import analyze_news
from backend.python.db import Neo4jConnection


TEST_TEXT = (
    "A labour action at the Port of Rotterdam is delaying "
    "shipments from Nordic Minerals. Mid-project review case."
)

EXPECTED_NODE_IDS = {
    "port-rotterdam",
    "supplier-sweden",
}


def test_repeated_ingestion_is_idempotent():
    analysis = analyze_news(
        text=TEST_TEXT,
        title="Mid-project ingestion review",
        source="AtmoGraph Review",
    )

    db = None
    connected = False
    original_nodes = []

    try:
        db = Neo4jConnection()

        try:
            db.verify_connection()
            connected = True
        except (Neo4jError, ServiceUnavailable) as error:
            pytest.skip(f"Neo4j is unavailable: {error}")

        records, _, _ = db.driver.execute_query(
            """
            MATCH (node:SupplyChainNode)
            WHERE node.id IN $node_ids
            RETURN
                node.id AS id,
                node.risk AS risk,
                node.risk_score AS risk_score
            """,
            node_ids=list(EXPECTED_NODE_IDS),
            database_="neo4j",
        )

        original_nodes = [dict(record) for record in records]

        assert {
            node["id"] for node in original_nodes
        } == EXPECTED_NODE_IDS

        first_result = write_analysis(analysis)
        second_result = write_analysis(analysis)

        assert set(first_result["updated_node_ids"]) == EXPECTED_NODE_IDS
        assert set(second_result["updated_node_ids"]) == EXPECTED_NODE_IDS

        records, _, _ = db.driver.execute_query(
            """
            MATCH (
                disruption:Disruption {id: $disruption_id}
            )
            OPTIONAL MATCH (
                disruption
            )-[relationship:AFFECTS]->(node)

            RETURN
                count(DISTINCT disruption) AS disruption_count,
                count(relationship) AS relationship_count,
                collect(node.id) AS affected_node_ids
            """,
            disruption_id=analysis["disruption_id"],
            database_="neo4j",
        )

        result = dict(records[0])

        assert result["disruption_count"] == 1
        assert result["relationship_count"] == 2
        assert set(result["affected_node_ids"]) == EXPECTED_NODE_IDS

    finally:
        if db is not None and connected:
            if analysis:
                db.driver.execute_query(
                    """
                    MATCH (
                        disruption:Disruption {id: $disruption_id}
                    )
                    DETACH DELETE disruption
                    """,
                    disruption_id=analysis["disruption_id"],
                    database_="neo4j",
                )

            if original_nodes:
                db.driver.execute_query(
                    """
                    UNWIND $nodes AS original
                    MATCH (
                        node:SupplyChainNode {id: original.id}
                    )
                    SET
                        node.risk = original.risk,
                        node.risk_score = original.risk_score
                    """,
                    nodes=original_nodes,
                    database_="neo4j",
                )

            db.close()
        elif db is not None:
            db.close()
