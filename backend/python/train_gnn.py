import csv
from collections import defaultdict

import torch
import torch.nn.functional as F

from backend.python.canonical_gnn_graph import load_canonical_gnn_graph
from backend.python.config import GNN_MODEL, TRAIN_FILE, VALIDATION_FILE
from backend.python.gnn_model import RippleGCN
from backend.python.scenario_graph import build_scenario_graph


EPOCHS = 200
LEARNING_RATE = 0.005
RANDOM_SEED = 42


def load_rows(path):
    with open(path, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def build_targets(rows, node_mapping):
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        scenario_id = int(row["scenario_id"])
        impact = float(row["impact_score"])
        for node_id in (
            row["manufacturer_id"],
            row["product_id"],
            row["warehouse_id"],
            row["market_id"],
        ):
            node_index = node_mapping.get(node_id)
            if node_index is not None:
                grouped[scenario_id][node_index].append(impact)

    return {
        scenario_id: {
            node_index: sum(values) / len(values)
            for node_index, values in nodes.items()
        }
        for scenario_id, nodes in grouped.items()
    }


def get_scenario_info(rows):
    scenarios = {}
    for row in rows:
        scenario_id = int(row["scenario_id"])
        scenarios.setdefault(
            scenario_id,
            {
                "port_id": row["disrupted_port_id"],
                "disruption_type": row["disruption_type"],
                "severity": float(row["severity"]),
            },
        )
    return scenarios


def prepare_split(path, node_mapping, split_name):
    rows = load_rows(path)
    targets = build_targets(rows, node_mapping)
    scenarios = get_scenario_info(rows)
    missing_scenarios = sorted(set(scenarios) - set(targets))
    if missing_scenarios:
        raise RuntimeError(
            f"{split_name} data is incompatible with the canonical graph. "
            f"No mapped targets for {len(missing_scenarios)} of "
            f"{len(scenarios)} scenarios. Examples: {missing_scenarios[:5]}"
        )
    return scenarios, targets


def scenario_loss(model, nodes, relationships, scenario, target_nodes):
    x, edge_index, _ = build_scenario_graph(
        nodes=nodes,
        relationships=relationships,
        disrupted_port_id=scenario["port_id"],
        disruption_type=scenario["disruption_type"],
        severity=scenario["severity"],
    )
    predictions = model(x, edge_index)
    target_indices = torch.tensor(list(target_nodes), dtype=torch.long)
    target_values = torch.tensor(list(target_nodes.values()), dtype=torch.float)
    return F.mse_loss(predictions[target_indices], target_values)


def mean_split_loss(model, nodes, relationships, scenarios, targets):
    losses = []
    with torch.no_grad():
        for scenario_id, scenario in scenarios.items():
            losses.append(
                scenario_loss(
                    model,
                    nodes,
                    relationships,
                    scenario,
                    targets[scenario_id],
                ).item()
            )
    return sum(losses) / len(losses)


def train():
    torch.manual_seed(RANDOM_SEED)
    nodes, relationships = load_canonical_gnn_graph()
    node_mapping = {
        node["properties"]["id"]: index for index, node in enumerate(nodes)
    }

    training_scenarios, training_targets = prepare_split(
        TRAIN_FILE, node_mapping, "Training"
    )
    validation_scenarios, validation_targets = prepare_split(
        VALIDATION_FILE, node_mapping, "Validation"
    )

    model = RippleGCN(input_features=23)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    best_validation_loss = float("inf")
    best_state = None

    print("\n========== TRAINING ==========")
    print("Canonical graph nodes:", len(nodes))
    print("Canonical graph relationships:", len(relationships))
    print("Training scenarios:", len(training_scenarios))
    print("Validation scenarios:", len(validation_scenarios))

    for epoch in range(1, EPOCHS + 1):
        model.train()
        epoch_losses = []

        for scenario_id, scenario in training_scenarios.items():
            loss = scenario_loss(
                model,
                nodes,
                relationships,
                scenario,
                training_targets[scenario_id],
            )
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())

        training_loss = sum(epoch_losses) / len(epoch_losses)
        model.eval()
        validation_loss = mean_split_loss(
            model,
            nodes,
            relationships,
            validation_scenarios,
            validation_targets,
        )

        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss
            best_state = {
                name: value.detach().cpu().clone()
                for name, value in model.state_dict().items()
            }

        if epoch == 1 or epoch % 10 == 0:
            print(
                f"Epoch {epoch:03d} "
                f"Train MSE: {training_loss:.6f} "
                f"Validation MSE: {validation_loss:.6f}"
            )

    if best_state is None:
        raise RuntimeError("Training completed without producing a checkpoint")

    model.load_state_dict(best_state)
    GNN_MODEL.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), GNN_MODEL)

    print("\nBest validation MSE:", round(best_validation_loss, 6))
    print("Model saved to:", GNN_MODEL)


if __name__ == "__main__":
    train()
