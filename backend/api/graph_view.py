"""Pure helpers for accurate graph and disruption API responses."""

from collections import Counter


GENERIC_LABELS = {"SupplyChainNode"}
OPERATIONAL_RELATIONSHIPS = {"SUPPLIES", "SHIPS_TO", "SERVES"}


def specific_node_type(labels):
    return next(
        (label for label in labels if label not in GENERIC_LABELS),
        "SupplyChainNode",
    )


def build_graph_summary(nodes, relationships):
    supply_nodes = [
        node
        for node in nodes
        if "SupplyChainNode" in node.get("labels", [])
    ]
    node_types = Counter(
        specific_node_type(node.get("labels", []))
        for node in supply_nodes
    )
    relationship_types = Counter(
        relationship["relationship_type"]
        for relationship in relationships
    )
    at_risk_nodes = sum(
        1
        for node in supply_nodes
        if float(node.get("properties", {}).get("risk_score", 0.0)) >= 0.4
    )
    operational_relationships = sum(
        count
        for relationship_type, count in relationship_types.items()
        if relationship_type in OPERATIONAL_RELATIONSHIPS
    )

    return {
        "total_nodes": len(nodes),
        "supply_chain_nodes": len(supply_nodes),
        "disruption_nodes": len(nodes) - len(supply_nodes),
        "at_risk_nodes": at_risk_nodes,
        "risk_threshold": 0.4,
        "total_relationships": len(relationships),
        "operational_relationships": operational_relationships,
        "node_types": dict(sorted(node_types.items())),
        "relationship_types": dict(sorted(relationship_types.items())),
    }


def deduplicate_disruptions(disruptions):
    """Collapse multiple active records describing the same port event."""
    grouped = {}

    for disruption in disruptions:
        key = (
            str(disruption.get("name") or "").strip().casefold(),
            str(disruption.get("type") or "").strip().casefold(),
            disruption.get("port_id"),
        )
        current = grouped.get(key)
        analyzed_at = str(disruption.get("analyzed_at") or "")

        if current is None:
            grouped[key] = {**disruption, "duplicate_count": 1}
            continue

        duplicate_count = current["duplicate_count"] + 1
        current_time = str(current.get("analyzed_at") or "")
        if analyzed_at > current_time:
            grouped[key] = {
                **disruption,
                "duplicate_count": duplicate_count,
            }
        else:
            current["duplicate_count"] = duplicate_count

    return sorted(
        grouped.values(),
        key=lambda item: str(item.get("analyzed_at") or ""),
        reverse=True,
    )
