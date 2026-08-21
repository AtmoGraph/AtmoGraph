import torch

from backend.python.gnn_model import RippleGCN
from backend.python.scenario_graph import build_scenario_graph

from backend.python.db import Neo4jConnection
from backend.python.graph_loader import load_nodes, load_relationships


def main():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            nodes = load_nodes(session)

            relationships = load_relationships(
                session
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

            model = RippleGCN(
                input_features=x.shape[1]
            )

            predictions = model(
                x,
                edge_index,
            )

            print(
                "\n========== GNN TEST =========="
            )

            print(
                "Input shape:",
                x.shape,
            )

            print(
                "Edge shape:",
                edge_index.shape,
            )

            print(
                "Prediction shape:",
                predictions.shape,
            )

            print(
                "\n========== SAMPLE PREDICTIONS =========="
            )

            for index in range(10):

                node_id = nodes[index][
                    "properties"
                ].get("id")

                node_name = nodes[index][
                    "properties"
                ].get("name")

                print(
                    index,
                    node_id,
                    node_name,
                    "->",
                    round(
                        predictions[index].item(),
                        4,
                    ),
                )

    finally:

        db.close()


if __name__ == "__main__":
    main()