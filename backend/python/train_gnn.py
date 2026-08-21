import csv
from collections import defaultdict

import torch
import torch.nn.functional as F

from backend.python.db import Neo4jConnection

from backend.python.graph_loader import (
    load_nodes,
    load_relationships,
)

from backend.python.scenario_graph import (
    build_scenario_graph,
)

from backend.python.gnn_model import RippleGCN


from backend.python.config import TRAIN_FILE, GNN_MODEL

EPOCHS = 100

LEARNING_RATE = 0.01


def load_training_rows():

    with open(
        TRAIN_FILE,
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
    """
    Aggregate target impact by scenario + node.

    Returns:

        {
            scenario_id: {
                node_id: impact
            }
        }
    """

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


def get_scenario_info(rows):

    scenarios = {}

    for row in rows:

        scenario_id = int(
            row["scenario_id"]
        )

        if scenario_id not in scenarios:

            scenarios[scenario_id] = {
                "port_id": (
                    row[
                        "disrupted_port_id"
                    ]
                ),
                "disruption_type": (
                    row[
                        "disruption_type"
                    ]
                ),
                "severity": float(
                    row["severity"]
                ),
            }

    return scenarios


def train():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            # --------------------------------
            # Load graph
            # --------------------------------

            nodes = load_nodes(session)

            relationships = (
                load_relationships(session)
            )

            # --------------------------------
            # Node mapping
            # --------------------------------

            node_mapping = {
                node["properties"]["id"]: index
                for index, node
                in enumerate(nodes)
                if node["properties"].get("id")
            }

            # --------------------------------
            # Dataset
            # --------------------------------

            rows = load_training_rows()

            targets = build_targets(
                rows,
                node_mapping,
            )

            scenarios = get_scenario_info(
                rows
            )

            print(
                "\n========== TRAINING =========="
            )

            print(
                "Training scenarios:",
                len(scenarios),
            )

            # --------------------------------
            # Model
            # --------------------------------

            model = RippleGCN(
                input_features=23
            )

            optimizer = torch.optim.Adam(
                model.parameters(),
                lr=LEARNING_RATE,
            )

            # --------------------------------
            # Training
            # --------------------------------

            for epoch in range(
                1,
                EPOCHS + 1,
            ):

                total_loss = 0.0

                scenario_count = 0

                for scenario_id in scenarios:

                    scenario = scenarios[
                        scenario_id
                    ]

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

                    target_nodes = targets.get(
                        scenario_id,
                        {}
                    )

                    if not target_nodes:
                        continue

                    target_indices = torch.tensor(
                        list(
                            target_nodes.keys()
                        ),
                        dtype=torch.long,
                    )

                    target_values = torch.tensor(
                        list(
                            target_nodes.values()
                        ),
                        dtype=torch.float,
                    )

                    predicted_values = (
                        predictions[
                            target_indices
                        ]
                    )

                    loss = F.mse_loss(
                        predicted_values,
                        target_values,
                    )

                    optimizer.zero_grad()

                    loss.backward()

                    optimizer.step()

                    total_loss += (
                        loss.item()
                    )

                    scenario_count += 1

                average_loss = (
                    total_loss
                    / max(
                        scenario_count,
                        1,
                    )
                )

                if (
                    epoch == 1
                    or epoch % 10 == 0
                ):

                    print(
                        f"Epoch {epoch:03d} "
                        f"Loss: "
                        f"{average_loss:.6f}"
                    )

            # --------------------------------
            # Save model
            # --------------------------------

            torch.save(
                model.state_dict(),
                GNN_MODEL,
            )

            print(
                "\nModel saved to:",
                "ripple_gnn.pt",
            )

    finally:

        db.close()


if __name__ == "__main__":
    train()