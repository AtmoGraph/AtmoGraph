import torch
from pydantic import BaseModel

from backend.python.canonical_gnn_graph import load_canonical_gnn_graph
from backend.python.scenario_graph import (
    build_scenario_graph,
)
from backend.python.gnn_model import RippleGCN
from backend.python.config import GNN_MODEL


class PredictionRequest(BaseModel):
    disrupted_port_id: str
    disruption_type: str
    severity: float


def load_gnn_model():
    model = RippleGCN(input_features=23)

    state_dict = torch.load(
        GNN_MODEL,
        map_location="cpu",
    )

    model.load_state_dict(state_dict)

    model.eval()

    return model


def generate_predictions(
    disrupted_port_id,
    disruption_type,
    severity,
):
    aliases = {
        "port-rotterdam": "PORT003",
    }
    disrupted_port_id = aliases.get(disrupted_port_id, disrupted_port_id)
    nodes, relationships = load_canonical_gnn_graph()
    valid_port_ids = {
        node["properties"]["id"]
        for node in nodes
        if "Port" in node["labels"]
    }
    if disrupted_port_id not in valid_port_ids:
        raise ValueError(
            f"Unknown canonical port ID: {disrupted_port_id}. "
            f"Valid IDs: {sorted(valid_port_ids)}"
        )

    x, edge_index, edge_type = build_scenario_graph(
        nodes=nodes,
        relationships=relationships,
        disrupted_port_id=disrupted_port_id,
        disruption_type=disruption_type,
        severity=severity,
    )

    model = load_gnn_model()

    with torch.no_grad():
        predictions = model(x, edge_index)

    results = []
    predicted_node_types = {"Manufacturer", "Product", "Warehouse", "Market"}

    for index, node in enumerate(nodes):

        node_id = node["properties"].get("id")

        node_name = node["properties"].get("name")

        node_type = node["labels"][0] if node.get("labels") else "Unknown"

        if node_type not in predicted_node_types:
            continue

        prediction = float(predictions[index].item())

        results.append(
            {
                "node_id": node_id,
                "node_name": node_name,
                "node_type": node_type,
                "prediction": round(prediction, 4),
            }
        )

    results.sort(key=lambda item: item["prediction"], reverse=True)

    return results


def predict_scenario(
    request: PredictionRequest,
):
    predictions = generate_predictions(
        disrupted_port_id=(
            request.disrupted_port_id
        ),
        disruption_type=(
            request.disruption_type
        ),
        severity=request.severity,
    )

    return {
        "scenario": {
            "disrupted_port_id": (
                request.disrupted_port_id
            ),
            "disruption_type": (
                request.disruption_type
            ),
            "severity": request.severity,
        },
        "total_nodes": len(predictions),
        "predictions": predictions,
        "top_impacted_nodes": predictions[:10],
    }
