from backend.python.db import Neo4jConnection


def _write_analysis(transaction, analysis: dict) -> list[str]:
    classification = analysis["classification"]

    transaction.run(
        """
        MERGE (disruption:Disruption {id: $id})
        SET disruption.name = $name,
            disruption.text = $text,
            disruption.type = $type,
            disruption.severity = $severity,
            disruption.risk_score = $risk_score,
            disruption.source = $source,
            disruption.url = $url,
            disruption.analyzed_at = datetime($analyzed_at),
            disruption.status = 'active'
        """,
        id=analysis["disruption_id"],
        name=analysis["title"],
        text=analysis["text"],
        type=classification["type"],
        severity=classification["risk_level"],
        risk_score=classification["risk_score"],
        source=analysis["source"],
        url=analysis["url"],
        analyzed_at=analysis["analyzed_at"],
    )

    result = transaction.run(
        """
        MATCH (disruption:Disruption {id: $disruption_id})
        UNWIND $node_ids AS node_id
        MATCH (node:SupplyChainNode {id: node_id})

        SET node.risk_score =
            CASE
                WHEN coalesce(node.risk_score, 0.0) < $risk_score
                THEN $risk_score
                ELSE node.risk_score
            END

        SET node.risk =
            CASE
                WHEN node.risk_score >= 0.75 THEN 'high'
                WHEN node.risk_score >= 0.40 THEN 'medium'
                ELSE 'low'
            END

        MERGE (disruption)-[:AFFECTS]->(node)

        RETURN collect(node.id) AS updated_node_ids
        """,
        disruption_id=analysis["disruption_id"],
        node_ids=analysis["affected_node_ids"],
        risk_score=classification["risk_score"],
    )

    record = result.single()
    return record["updated_node_ids"] if record else []


def write_analysis(analysis: dict) -> dict:
    classification = analysis["classification"]

    if not classification["detected"]:
        raise ValueError("No disruption was detected in the supplied text")

    if not analysis["affected_node_ids"]:
        raise ValueError(
            "The disruption did not match any known supply-chain nodes"
        )

    db = Neo4jConnection()

    try:
        with db.driver.session(database="neo4j") as session:
            session.run(
                """
                CREATE CONSTRAINT disruption_id IF NOT EXISTS
                FOR (disruption:Disruption)
                REQUIRE disruption.id IS UNIQUE
                """
            ).consume()

            updated_node_ids = session.execute_write(
                _write_analysis,
                analysis,
            )
    finally:
        db.close()

    return {
        "disruption_id": analysis["disruption_id"],
        "updated_node_ids": updated_node_ids,
        "updated_node_count": len(updated_node_ids),
    }