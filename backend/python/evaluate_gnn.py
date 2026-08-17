import csv
import math
from collections import defaultdict

import torch

from backend.python.db import Neo4jConnection

from backend.python.graph_loader import (
    load_nodes,
    load_relationships,
)

from backend.python.scenario_graph import (
    build_scenario_graph,
)

from backend.python.gnn_model import RippleGCN


from backend.python.config import TEST_FILE, GNN_MODEL


def load_rows():

    with open(
        TEST_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return list(
            csv.DictReader(file)
        )


def build_targets(
    rows,
    node_mapping,
):

    grouped = defaultdict(
        lambda: defaultdict(list)
    )

    for row in rows:

        scenario_id = int(
            row["scenario_id"]
        )

        node_ids = [
            row["manufacturer_id"],
            row["product_id"],
            row["warehouse_id"],
            row["market_id"],
        ]

        impact = float(
            row["impact_score"]
        )

        for node_id in node_ids:

            node_index = node_mapping.get(
                node_id
            )

            if node_index is not None:

                grouped[
                    scenario_id
                ][node_index].append(
                    impact
                )

    targets = {}

    for scenario_id, nodes in grouped.items():

        targets[scenario_id] = {}

        for node_index, values in nodes.items():

            targets[
                scenario_id
            ][node_index] = (
                sum(values)
                / len(values)
            )

    return targets


def get_scenarios(rows):

    scenarios = {}

    for row in rows:

        scenario_id = int(
            row["scenario_id"]
        )

        if scenario_id not in scenarios:

            scenarios[scenario_id] = {
                "port_id":
                    row[
                        "disrupted_port_id"
                    ],

                "disruption_type":
                    row[
                        "disruption_type"
                    ],

                "severity":
                    float(
                        row["severity"]
                    ),
            }

    return scenarios


def main():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            nodes = load_nodes(session)

            relationships = (
                load_relationships(session)
            )

            node_mapping = {
                node["properties"]["id"]: index
                for index, node
                in enumerate(nodes)
                if node["properties"].get("id")
            }

            rows = load_rows()

            targets = build_targets(
                rows,
                node_mapping,
            )

            scenarios = get_scenarios(
                rows
            )

            # -----------------------------
            # Load trained model
            # -----------------------------

            model = RippleGCN(
                input_features=23
            )

            model.load_state_dict(
                torch.load(
                    GNN_MODEL,
                    map_location="cpu",
                )
            )

            model.eval()

            absolute_errors = []
            squared_errors = []

            results = []

            with torch.no_grad():

                for scenario_id, scenario in (
                    scenarios.items()
                ):

                    x, edge_index, edge_type = (
                        build_scenario_graph(
                            nodes=nodes,
                            relationships=(
                                relationships
                            ),
                            disrupted_port_id=(
                                scenario[
                                    "port_id"
                                ]
                            ),
                            disruption_type=(
                                scenario[
                                    "disruption_type"
                                ]
                            ),
                            severity=(
                                scenario[
                                    "severity"
                                ]
                            ),
                        )
                    )

                    predictions = model(
                        x,
                        edge_index,
                    )

                    target_nodes = targets[
                        scenario_id
                    ]

                    for node_index, actual in (
                        target_nodes.items()
                    ):

                        predicted = (
                            predictions[
                                node_index
                            ].item()
                        )

                        error = abs(
                            predicted
                            - actual
                        )

                        squared_error = (
                            predicted
                            - actual
                        ) ** 2

                        absolute_errors.append(
                            error
                        )

                        squared_errors.append(
                            squared_error
                        )

                        results.append({
                            "scenario_id":
                                scenario_id,

                            "node_index":
                                node_index,

                            "actual":
                                actual,

                            "predicted":
                                predicted,

                            "error":
                                error,
                        })

            # -----------------------------
            # Metrics
            # -----------------------------

            mae = (
                sum(absolute_errors)
                / len(absolute_errors)
            )

            rmse = math.sqrt(
                sum(squared_errors)
                / len(squared_errors)
            )

            print(
                "\n========== TEST RESULTS =========="
            )

            print(
                "Test scenarios:",
                len(scenarios)
            )

            print(
                "Test predictions:",
                len(results)
            )

            print(
                "MAE:",
                round(mae, 6)
            )

            print(
                "RMSE:",
                round(rmse, 6)
            )

            # -----------------------------
            # Sample predictions
            # -----------------------------

            print(
                "\n========== SAMPLE PREDICTIONS =========="
            )

            for result in results[:10]:

                node_index = result[
                    "node_index"
                ]

                node = nodes[
                    node_index
                ]

                node_id = node[
                    "properties"
                ].get("id")

                node_name = node[
                    "properties"
                ].get("name")

                print(
                    f"Scenario "
                    f"{result['scenario_id']} | "
                    f"{node_id} | "
                    f"{node_name} | "
                    f"Actual: "
                    f"{result['actual']:.4f} | "
                    f"Predicted: "
                    f"{result['predicted']:.4f} | "
                    f"Error: "
                    f"{result['error']:.4f}"
                )

    finally:

        db.close()


if __name__ == "__main__":
    main()