import torch

from backend.python.db import Neo4jConnection
from backend.python.graph_loader import (
    load_nodes,
    load_relationships,
)
from backend.python.feature_pipeline import (
    build_graph_features,
)
from backend.python.edge_builder import (
    create_node_mapping,
    build_edges,
)

DISRUPTION_TYPES = [
    "PORT_STRIKE",
    "PORT_CLOSURE",
    "SEVERE_WEATHER",
    "INFRASTRUCTURE_FAILURE",
]


def create_scenario_features(
    nodes,
    disrupted_port_id,
    disruption_type,
    severity,
):
    """
    Add scenario-specific features to the
    base node feature matrix.

    Additional features:

    [is_disrupted,
     severity,
     PORT_STRIKE,
     PORT_CLOSURE,
     SEVERE_WEATHER,
     INFRASTRUCTURE_FAILURE]
    """

    scenario_features = []

    for node in nodes:

        node_id = node["properties"].get("id")

        is_disrupted = (
            1.0
            if node_id == disrupted_port_id
            else 0.0
        )

        node_severity = (
            severity
            if is_disrupted
            else 0.0
        )

        disruption_type_features = [
            (
                1.0
                if (
                    is_disrupted
                    and disruption_type
                    == current_type
                )
                else 0.0
            )
            for current_type in DISRUPTION_TYPES
        ]

        scenario_features.append(
            [
                is_disrupted,
                node_severity,
                *disruption_type_features,
            ]
        )

    return scenario_features


def combine_features(
    base_features,
    scenario_features,
):
    """
    Combine base node features with
    scenario-specific features.
    """

    combined = []

    for base, scenario in zip(
        base_features,
        scenario_features,
    ):

        combined.append(
            base + scenario
        )

    return combined


def build_scenario_graph(
    nodes,
    relationships,
    disrupted_port_id,
    disruption_type,
    severity,
):
    """
    Build a PyTorch Geometric graph
    for one disruption scenario.
    """

    node_mapping = create_node_mapping(
        nodes
    )

    # -------------------------------
    # Base features
    # -------------------------------

    _, base_features = (
        build_graph_features(nodes)
    )

    # -------------------------------
    # Scenario features
    # -------------------------------

    scenario_features = (
        create_scenario_features(
            nodes=nodes,
            disrupted_port_id=(
                disrupted_port_id
            ),
            disruption_type=(
                disruption_type
            ),
            severity=severity,
        )
    )

    # -------------------------------
    # Combined features
    # -------------------------------

    feature_matrix = combine_features(
        base_features,
        scenario_features,
    )

    x = torch.tensor(
        feature_matrix,
        dtype=torch.float,
    )

    # -------------------------------
    # Edges
    # -------------------------------

    edges = build_edges(
        relationships,
        node_mapping,
    )

    edge_index = torch.tensor(
        [
            [edge["source"] for edge in edges],
            [edge["target"] for edge in edges],
        ],
        dtype=torch.long,
    )

    edge_type = torch.tensor(
        [
            edge["type"]
            for edge in edges
        ],
        dtype=torch.long,
    )

    return x, edge_index, edge_type


def main():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            nodes = load_nodes(session)

            relationships = (
                load_relationships(session)
            )

            x, edge_index, edge_type = (
                build_scenario_graph(
                    nodes=nodes,
                    relationships=relationships,
                    disrupted_port_id="PORT003",
                    disruption_type="PORT_CLOSURE",
                    severity=0.95,
                )
            )

            print(
                "\n========== SCENARIO GRAPH =========="
            )

            print(
                "Node feature shape:",
                x.shape,
            )

            print(
                "Edge index shape:",
                edge_index.shape,
            )

            print(
                "Edge type shape:",
                edge_type.shape,
            )

            # Find disrupted node

            for index, node in enumerate(nodes):

                node_id = node[
                    "properties"
                ].get("id")

                if node_id == "PORT003":

                    print(
                        "\n========== DISRUPTED NODE =========="
                    )

                    print(
                        "Node index:",
                        index,
                    )

                    print(
                        "Node ID:",
                        node_id,
                    )

                    print(
                        "Features:",
                        x[index].tolist(),
                    )

    finally:

        db.close()


if __name__ == "__main__":
    main()