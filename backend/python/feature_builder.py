NODE_TYPES = [
    "Supplier",
    "Manufacturer",
    "Product",
    "Port",
    "ShippingRoute",
    "Warehouse",
    "Market",
    "Disruption",
]


def get_node_type(labels):
    """
    Return the primary node type.
    """

    for node_type in NODE_TYPES:

        if node_type in labels:
            return node_type

    return "Unknown"


def build_feature_vector(node):
    """
    Convert a Neo4j node into a numerical feature vector.

    Feature structure:

    [node_type_one_hot,
     capacity,
     production_capacity,
     congestion,
     risk,
     transit_days,
     distance,
     cost,
     severity,
     delay]
    """

    properties = node["properties"]

    node_type = get_node_type(node["labels"])

    # --------------------------------
    # Node type one-hot encoding
    # --------------------------------

    type_features = [
        1.0 if node_type == current_type else 0.0
        for current_type in NODE_TYPES
    ]

    # --------------------------------
    # Numerical features
    # --------------------------------

    capacity = float(
        properties.get("capacity", 0)
    )

    production_capacity = float(
        properties.get("production_capacity", 0)
    )

    congestion = float(
        properties.get("congestion_level", 0)
    )

    risk = float(
        properties.get("risk_score", 0)
    )

    transit_days = float(
        properties.get("transit_days", 0)
    )

    distance = float(
        properties.get("distance_km", 0)
    )

    cost = float(
        properties.get("cost", 0)
    )

    severity_value = properties.get("severity", 0)

    severity_mapping = {
        "low": 0.2,
        "medium": 0.5,
        "high": 0.9,
        "critical": 1.0,
    }

    if isinstance(severity_value, str):
        severity = severity_mapping.get(
            severity_value.strip().lower(),
            float(
                properties.get("risk_score", 0)
            ),
        )
    else:
        severity = float(severity_value or 0)

    delay = float(
        properties.get("expected_delay_days", 0)
    )

    numerical_features = [
        capacity,
        production_capacity,
        congestion,
        risk,
        transit_days,
        distance,
        cost,
        severity,
        delay,
    ]

    return type_features + numerical_features

if __name__ == "__main__":

    test_nodes = [
        {
            "labels": ["Port"],
            "properties": {
                "capacity": 6500000,
                "congestion_level": 0.25,
                "risk_score": 0.20,
            },
        },
        {
            "labels": ["Manufacturer"],
            "properties": {
                "production_capacity": 100000,
            },
        },
        {
            "labels": ["Disruption"],
            "properties": {
                "severity": 0.90,
                "expected_delay_days": 21,
            },
        },
    ]

    for node in test_nodes:

        vector = build_feature_vector(node)

        print(
            get_node_type(node["labels"]),
            "->",
            vector
        )