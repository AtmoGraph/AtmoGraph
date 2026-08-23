from backend.python.edge_builder import (
    build_edges,
    create_node_mapping,
)
from backend.python.feature_builder import build_feature_vector


def test_string_severity_is_converted_to_numeric_value():
    node = {
        "labels": ["Disruption"],
        "properties": {
            "severity": "high",
            "risk_score": 0.9,
        },
    }

    feature_vector = build_feature_vector(node)

    # Severity is the second-last numerical feature.
    assert feature_vector[-2] == 0.9


def test_ships_to_relationship_is_supported():
    nodes = [
        {
            "neo4j_id": "source-node",
            "labels": ["Port"],
            "properties": {"id": "port-a"},
        },
        {
            "neo4j_id": "target-node",
            "labels": ["Factory"],
            "properties": {"id": "factory-a"},
        },
    ]

    relationships = [
        {
            "source_neo4j_id": "source-node",
            "target_neo4j_id": "target-node",
            "relationship_type": "SHIPS_TO",
            "properties": {},
        }
    ]

    node_mapping = create_node_mapping(nodes)
    edges = build_edges(relationships, node_mapping)

    assert len(edges) == 1
    assert edges[0]["source"] == 0
    assert edges[0]["target"] == 1
    assert edges[0]["relationship_type"] == "SHIPS_TO"
    assert isinstance(edges[0]["type"], int)