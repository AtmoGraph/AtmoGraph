from backend.api.graph_view import (
    build_graph_summary,
    deduplicate_disruptions,
    specific_node_type,
)


def _node(labels, risk_score=0.0):
    return {
        "labels": labels,
        "properties": {"risk_score": risk_score},
    }


def test_specific_node_type_ignores_generic_label():
    assert specific_node_type(["SupplyChainNode", "Port"]) == "Port"
    assert specific_node_type(["Disruption"]) == "Disruption"


def test_graph_summary_uses_supply_nodes_and_operational_edges():
    nodes = [
        _node(["SupplyChainNode", "Port"], 0.9),
        _node(["SupplyChainNode", "Supplier"], 0.2),
        _node(["Disruption"], 1.0),
    ]
    relationships = [
        {"relationship_type": "SHIPS_TO"},
        {"relationship_type": "AFFECTS"},
    ]

    summary = build_graph_summary(nodes, relationships)

    assert summary["total_nodes"] == 3
    assert summary["supply_chain_nodes"] == 2
    assert summary["disruption_nodes"] == 1
    assert summary["at_risk_nodes"] == 1
    assert summary["operational_relationships"] == 1
    assert summary["node_types"] == {"Port": 1, "Supplier": 1}


def test_duplicate_active_disruptions_collapse_to_latest():
    disruptions = [
        {
            "id": "old",
            "name": "Rotterdam strike",
            "type": "labour_strike",
            "port_id": "port-rotterdam",
            "analyzed_at": "2026-09-01T10:00:00Z",
        },
        {
            "id": "new",
            "name": "Rotterdam strike",
            "type": "labour_strike",
            "port_id": "port-rotterdam",
            "analyzed_at": "2026-09-02T10:00:00Z",
        },
    ]

    result = deduplicate_disruptions(disruptions)

    assert len(result) == 1
    assert result[0]["id"] == "new"
    assert result[0]["duplicate_count"] == 2
