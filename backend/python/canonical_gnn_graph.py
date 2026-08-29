"""Reproducible graph snapshot used by GNN training and inference.

The live Neo4j graph is intentionally small and changes when NLP events are
ingested.  A model cannot be trained against one graph and evaluated against a
different one, so the GNN uses this deterministic snapshot reconstructed from
the committed ripple dataset.
"""

import csv

from backend.python.config import FULL_RIPPLE_DATASET, SYNTHETIC_DISRUPTIONS


PORT_ORIGINS = {
    "Taipei": ("PORT001", "Taipei Port"),
    "Shanghai": ("PORT002", "Shanghai Port"),
    "Hamburg": ("PORT004", "Hamburg Port"),
}

MANUFACTURER_ORIGINS = {
    "MAN001": "PORT001",
    "MAN002": "PORT002",
    "MAN003": "PORT004",
    "MAN004": "PORT002",
}

# Deterministic development values.  They are inputs, not prediction labels.
MANUFACTURER_CAPACITY = {
    "MAN001": 100.0,
    "MAN002": 92.0,
    "MAN003": 68.0,
    "MAN004": 110.0,
}

ROUTE_PROPERTIES = {
    "Taipei-Rotterdam Route": (20.0, 9440.0, 92.0),
    "Shanghai-Rotterdam Route": (24.0, 8900.0, 96.0),
    "Hamburg-Rotterdam Route": (2.0, 465.0, 78.0),
    "Taipei-Los Angeles Route": (16.0, 10900.0, 94.0),
    "Shanghai-Los Angeles Route": (18.0, 10400.0, 98.0),
}


def _node(node_id, name, label, **properties):
    return {
        "neo4j_id": node_id,
        "labels": [label],
        "properties": {"id": node_id, "name": name, **properties},
    }


def _relationship(source, relationship_type, target):
    return {
        "source_neo4j_id": source,
        "target_neo4j_id": target,
        "relationship_type": relationship_type,
        "properties": {},
    }


def _port_properties():
    properties = {}
    with open(SYNTHETIC_DISRUPTIONS, "r", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            properties.setdefault(
                row["port_id"],
                {
                    "name": row["port_name"],
                    "risk_score": float(row["port_risk"]),
                    "congestion_level": float(row["port_congestion"]),
                },
            )
    return properties


def load_canonical_gnn_graph():
    """Return nodes and relationships in graph_loader-compatible form."""
    with open(FULL_RIPPLE_DATASET, "r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise RuntimeError("The canonical ripple dataset is empty")

    nodes = {}
    relationships = set()

    for port_id, properties in _port_properties().items():
        nodes[port_id] = _node(port_id, properties.pop("name"), "Port", **properties)

    for row in rows:
        manufacturer_id = row["manufacturer_id"]
        product_id = row["product_id"]
        warehouse_id = row["warehouse_id"]
        market_id = row["market_id"]
        destination_id = row["disrupted_port_id"]
        route_name = row["route"]
        route_id = "ROUTE-" + route_name.upper().replace(" ", "-")

        origin_name = route_name.split("-", 1)[0]
        origin_id, origin_port_name = PORT_ORIGINS[origin_name]

        nodes.setdefault(
            manufacturer_id,
            _node(
                manufacturer_id,
                row["manufacturer"],
                "Manufacturer",
                production_capacity=MANUFACTURER_CAPACITY[manufacturer_id],
            ),
        )
        nodes.setdefault(product_id, _node(product_id, row["product"], "Product"))
        nodes.setdefault(warehouse_id, _node(warehouse_id, row["warehouse"], "Warehouse", capacity=90.0))
        nodes.setdefault(market_id, _node(market_id, row["market"], "Market", capacity=100.0))
        nodes.setdefault(origin_id, _node(origin_id, origin_port_name, "Port"))
        nodes.setdefault(destination_id, _node(destination_id, row["disrupted_port"], "Port"))

        transit_days, distance_km, capacity = ROUTE_PROPERTIES[route_name]
        nodes.setdefault(
            route_id,
            _node(
                route_id,
                route_name,
                "ShippingRoute",
                transit_days=transit_days,
                distance_km=distance_km,
                capacity=capacity,
            ),
        )

        relationships.update(
            {
                (manufacturer_id, "USES_PORT", origin_id),
                (manufacturer_id, "PRODUCES", product_id),
                (route_id, "FROM", origin_id),
                (route_id, "TO", destination_id),
                (destination_id, "SERVES", warehouse_id),
                (warehouse_id, "DISTRIBUTES_TO", market_id),
            }
        )

    ordered_nodes = [nodes[node_id] for node_id in sorted(nodes)]
    ordered_relationships = [
        _relationship(source, relationship_type, target)
        for source, relationship_type, target in sorted(relationships)
    ]

    required_ids = {
        value
        for row in rows
        for value in (
            row["disrupted_port_id"],
            row["manufacturer_id"],
            row["product_id"],
            row["warehouse_id"],
            row["market_id"],
        )
    }
    missing_ids = sorted(required_ids - nodes.keys())
    if missing_ids:
        raise RuntimeError(f"Canonical GNN graph is missing IDs: {missing_ids}")

    return ordered_nodes, ordered_relationships

