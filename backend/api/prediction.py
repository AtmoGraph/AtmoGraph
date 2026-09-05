from functools import lru_cache
from typing import Literal

import torch
from pydantic import BaseModel, Field

from backend.python.canonical_gnn_graph import load_canonical_gnn_graph
from backend.python.scenario_graph import (
    build_scenario_graph,
)
from backend.python.gnn_model import RippleGCN
from backend.python.config import GNN_MODEL


class PredictionRequest(BaseModel):
    disrupted_port_id: str
    disruption_type: str
    severity: float = Field(ge=0.0, le=1.0)
    horizon_days: Literal[30, 60, 90] = 30


HORIZON_FACTORS = {
    30: 1.0,
    60: 0.82,
    90: 0.68,
}
PROJECTION_METHOD = "gnn_recovery_curve_v1"


@lru_cache(maxsize=1)
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


def project_predictions(predictions, horizon_days):
    """Project the validated 30-day GNN impact through a recovery curve.

    The committed model was not trained with a horizon feature.  These values
    therefore remain transparent operational projections rather than separate
    learned forecasts.
    """
    try:
        factor = HORIZON_FACTORS[horizon_days]
    except KeyError as error:
        raise ValueError(
            "horizon_days must be one of: 30, 60, 90"
        ) from error

    projected = []
    for item in predictions:
        base_prediction = float(item["prediction"])
        projected.append(
            {
                **item,
                "base_prediction": round(base_prediction, 4),
                "prediction": round(base_prediction * factor, 4),
                "horizon_days": horizon_days,
            }
        )

    projected.sort(
        key=lambda item: item["prediction"],
        reverse=True,
    )
    return projected


def predict_scenario(
    request: PredictionRequest,
):
    base_predictions = generate_predictions(
        disrupted_port_id=(
            request.disrupted_port_id
        ),
        disruption_type=(
            request.disruption_type
        ),
        severity=request.severity,
    )
    predictions = project_predictions(
        base_predictions,
        request.horizon_days,
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
            "horizon_days": request.horizon_days,
        },
        "projection_method": PROJECTION_METHOD,
        "projection_note": (
            "The GNN supplies the validated baseline impact; 60/90-day "
            "values apply a transparent operational recovery curve."
        ),
        "total_nodes": len(predictions),
        "predictions": predictions,
        "top_impacted_nodes": predictions[:10],
    }
