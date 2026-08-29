import csv
import json
import math

import torch

from backend.python.canonical_gnn_graph import load_canonical_gnn_graph
from backend.python.config import (
    GNN_METRICS,
    GNN_MODEL,
    GNN_PREDICTIONS,
    TEST_FILE,
)
from backend.python.gnn_model import RippleGCN
from backend.python.scenario_graph import build_scenario_graph
from backend.python.train_gnn import build_targets, get_scenario_info, load_rows


def main():
    nodes, relationships = load_canonical_gnn_graph()
    node_mapping = {
        node["properties"]["id"]: index for index, node in enumerate(nodes)
    }
    rows = load_rows(TEST_FILE)
    targets = build_targets(rows, node_mapping)
    scenarios = get_scenario_info(rows)

    missing_scenarios = sorted(set(scenarios) - set(targets))
    if missing_scenarios:
        raise RuntimeError(
            "Evaluation data is incompatible with the canonical graph. "
            f"No mapped targets for {len(missing_scenarios)} of "
            f"{len(scenarios)} scenarios. Examples: {missing_scenarios[:5]}"
        )

    model = RippleGCN(input_features=23)
    model.load_state_dict(torch.load(GNN_MODEL, map_location="cpu"))
    model.eval()

    absolute_errors = []
    squared_errors = []
    results = []

    with torch.no_grad():
        for scenario_id, scenario in scenarios.items():
            x, edge_index, _ = build_scenario_graph(
                nodes=nodes,
                relationships=relationships,
                disrupted_port_id=scenario["port_id"],
                disruption_type=scenario["disruption_type"],
                severity=scenario["severity"],
            )
            predictions = model(x, edge_index)

            for node_index, actual in targets[scenario_id].items():
                predicted = predictions[node_index].item()
                error = predicted - actual
                absolute_errors.append(abs(error))
                squared_errors.append(error**2)
                node = nodes[node_index]
                results.append(
                    {
                        "scenario_id": scenario_id,
                        "node_id": node["properties"]["id"],
                        "node_name": node["properties"]["name"],
                        "actual": round(actual, 6),
                        "predicted": round(predicted, 6),
                        "absolute_error": round(abs(error), 6),
                    }
                )

    if not results:
        raise RuntimeError("Evaluation produced no predictions")

    mae = sum(absolute_errors) / len(absolute_errors)
    rmse = math.sqrt(sum(squared_errors) / len(squared_errors))
    metrics = {
        "test_scenarios": len(scenarios),
        "test_predictions": len(results),
        "mae": round(mae, 6),
        "rmse": round(rmse, 6),
        "model": str(GNN_MODEL.name),
        "graph_nodes": len(nodes),
        "graph_relationships": len(relationships),
    }

    GNN_METRICS.parent.mkdir(parents=True, exist_ok=True)
    GNN_METRICS.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    with open(GNN_PREDICTIONS, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("\n========== TEST RESULTS ==========")
    print("Test scenarios:", metrics["test_scenarios"])
    print("Test predictions:", metrics["test_predictions"])
    print("MAE:", metrics["mae"])
    print("RMSE:", metrics["rmse"])
    print("Metrics saved to:", GNN_METRICS)
    print("Predictions saved to:", GNN_PREDICTIONS)

    print("\n========== SAMPLE PREDICTIONS ==========")
    for result in results[:10]:
        print(
            f"Scenario {result['scenario_id']} | {result['node_id']} | "
            f"{result['node_name']} | Actual: {result['actual']:.4f} | "
            f"Predicted: {result['predicted']:.4f} | "
            f"Error: {result['absolute_error']:.4f}"
        )


if __name__ == "__main__":
    main()
