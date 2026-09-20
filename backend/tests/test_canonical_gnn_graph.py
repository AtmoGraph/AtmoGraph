import csv

from backend.python.config import FULL_RIPPLE_DATASET
from backend.python.canonical_gnn_graph import (
    PORT_COORDINATES,
    load_canonical_gnn_graph,
)

def test_canonical_graph_contains_every_dataset_node_id():
    nodes, relationships = load_canonical_gnn_graph()
    graph_ids = {node["properties"]["id"] for node in nodes}

    with open(FULL_RIPPLE_DATASET, "r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    dataset_ids = {
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

    assert dataset_ids <= graph_ids
    assert len(nodes) == 25
    assert len(relationships) == 25


def test_canonical_graph_is_deterministic():
    first = load_canonical_gnn_graph()
    second = load_canonical_gnn_graph()

    assert first == second

def test_every_operational_port_has_valid_coordinates():
    nodes, _ = load_canonical_gnn_graph()
    ports = [
        node for node in nodes
        if "Port" in node["labels"]
    ]

    assert {
        node["properties"]["id"] for node in ports
    } == set(PORT_COORDINATES)

    for port in ports:
        latitude = port["properties"]["latitude"]
        longitude = port["properties"]["longitude"]

        assert -90 <= latitude <= 90
        assert -180 <= longitude <= 180
