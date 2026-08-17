from backend.python.db import Neo4jConnection
from backend.python.graph_loader import load_nodes, load_relationships
from backend.python.feature_builder import build_feature_vector


def normalize_column(values):
    """
    Min-max normalization.

    Converts values into the range [0, 1].
    """

    if not values:
        return []

    minimum = min(values)
    maximum = max(values)

    if maximum == minimum:
        return [0.0 for _ in values]

    return [
        (value - minimum) / (maximum - minimum)
        for value in values
    ]


def build_graph_features(nodes):
    """
    Build feature vectors for every node.

    Returns:
        node_ids
        feature_matrix
    """

    node_ids = []
    raw_features = []

    for node in nodes:

        node_ids.append(node["neo4j_id"])

        vector = build_feature_vector(node)

        raw_features.append(vector)

    # --------------------------------
    # Separate categorical + numerical
    # --------------------------------

    type_feature_count = 8

    type_features = [
        vector[:type_feature_count]
        for vector in raw_features
    ]

    numerical_features = [
        vector[type_feature_count:]
        for vector in raw_features
    ]

    # --------------------------------
    # Normalize each numerical column
    # --------------------------------

    number_of_numeric_features = len(
        numerical_features[0]
    )

    normalized_columns = []

    for column_index in range(
        number_of_numeric_features
    ):

        column = [
            vector[column_index]
            for vector in numerical_features
        ]

        normalized_columns.append(
            normalize_column(column)
        )

    # --------------------------------
    # Rebuild feature matrix
    # --------------------------------

    feature_matrix = []

    for row_index in range(len(nodes)):

        normalized_numeric = [
            normalized_columns[column_index][row_index]
            for column_index in range(
                number_of_numeric_features
            )
        ]

        feature_vector = (
            type_features[row_index]
            + normalized_numeric
        )

        feature_matrix.append(feature_vector)

    return node_ids, feature_matrix


def main():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            nodes = load_nodes(session)
            relationships = load_relationships(session)

            node_ids, feature_matrix = (
                build_graph_features(nodes)
            )

            print("\n========== FEATURE MATRIX ==========")

            print(
                "Number of nodes:",
                len(feature_matrix)
            )

            print(
                "Features per node:",
                len(feature_matrix[0])
            )

            print("\n========== SAMPLE FEATURES ==========")

            for index in range(
                min(10, len(nodes))
            ):

                properties = nodes[index]["properties"]

                print(
                    index,
                    "->",
                    properties.get("id"),
                    "->",
                    feature_matrix[index]
                )

    finally:

        db.close()


if __name__ == "__main__":
    main()