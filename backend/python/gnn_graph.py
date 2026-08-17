import torch
from torch_geometric.data import Data

from backend.python.db import Neo4jConnection
from backend.python.graph_loader import load_nodes, load_relationships
from backend.python.feature_pipeline import build_graph_features
from backend.python.edge_builder import create_node_mapping, build_edges


def build_pyg_graph(nodes, relationships):

    # ---------------------------------
    # Node mapping
    # ---------------------------------

    node_mapping = create_node_mapping(nodes)

    # ---------------------------------
    # Node features
    # ---------------------------------

    _, feature_matrix = build_graph_features(nodes)

    x = torch.tensor(
        feature_matrix,
        dtype=torch.float
    )

    # ---------------------------------
    # Edges
    # ---------------------------------

    edges = build_edges(
        relationships,
        node_mapping
    )

    edge_index = torch.tensor(
        [
            [edge["source"] for edge in edges],
            [edge["target"] for edge in edges],
        ],
        dtype=torch.long
    )

    # ---------------------------------
    # Relationship type
    # ---------------------------------

    edge_type = torch.tensor(
        [
            edge["type"]
            for edge in edges
        ],
        dtype=torch.long
    )

    # ---------------------------------
    # Create PyG graph
    # ---------------------------------

    graph = Data(
        x=x,
        edge_index=edge_index,
        edge_type=edge_type,
    )

    return graph


def main():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            nodes = load_nodes(session)

            relationships = load_relationships(
                session
            )

            graph = build_pyg_graph(
                nodes,
                relationships
            )

            print(
                "\n========== PYTORCH GEOMETRIC GRAPH =========="
            )

            print(graph)

            print(
                "\n========== NODE FEATURES =========="
            )

            print(
                "x shape:",
                graph.x.shape
            )

            print(
                "\n========== EDGE INDEX =========="
            )

            print(
                "edge_index shape:",
                graph.edge_index.shape
            )

            print(
                "\n========== EDGE TYPES =========="
            )

            print(
                "edge_type shape:",
                graph.edge_type.shape
            )

            print(
                "\n========== GRAPH DETAILS =========="
            )

            print(
                "Number of nodes:",
                graph.num_nodes
            )

            print(
                "Number of edges:",
                graph.num_edges
            )

            print(
                "Number of node features:",
                graph.num_node_features
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()