import csv

from backend.python.canonical_gnn_graph import load_canonical_gnn_graph
from backend.python.config import FULL_RIPPLE_DATASET


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

