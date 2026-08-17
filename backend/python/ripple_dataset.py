import csv
import random

from backend.python.db import Neo4jConnection


DISRUPTION_TYPES = [
    "PORT_STRIKE",
    "PORT_CLOSURE",
    "SEVERE_WEATHER",
    "INFRASTRUCTURE_FAILURE",
]


TYPE_MULTIPLIER = {
    "PORT_STRIKE": 1.00,
    "PORT_CLOSURE": 1.30,
    "SEVERE_WEATHER": 1.15,
    "INFRASTRUCTURE_FAILURE": 1.10,
}


def calculate_impact(
    severity,
    port_risk,
    congestion,
    transit_days,
    production_capacity,
    route_capacity,
    hop_distance,
    disruption_type,
):
    """
    Synthetic ripple-impact simulator.

    This generates development labels.
    It is NOT a real-world prediction model.
    """

    type_factor = TYPE_MULTIPLIER[
        disruption_type
    ]

    route_utilization = (
        production_capacity / route_capacity
        if route_capacity > 0
        else 0
    )

    route_utilization = min(
        route_utilization,
        1.0,
    )

    transit_factor = min(
        transit_days / 30.0,
        1.0,
    )

    # Impact decreases as the disruption
    # propagates farther through the graph.

    propagation_factor = 1.0 / (
        1.0 + hop_distance * 0.15
    )

    impact = (
        severity * 0.30
        + port_risk * 0.15
        + congestion * 0.15
        + transit_factor * 0.15
        + route_utilization * 0.15
    )

    impact *= type_factor
    impact *= propagation_factor

    return round(
        min(impact, 1.0),
        4,
    )


def generate_dataset(
    session,
    number_of_scenarios=100,
):

    query = """
    MATCH (port:Port)

    MATCH (manufacturer:Manufacturer)
          -[:USES_PORT]->
          (origin:Port)
          <-[:FROM]-
          (route:ShippingRoute)
          -[:TO]->
          (port)

    MATCH (manufacturer)
          -[:PRODUCES]->
          (product:Product)

    MATCH (port)
          -[:SERVES]->
          (warehouse:Warehouse)
          -[:DISTRIBUTES_TO]->
          (market:Market)

    RETURN
        port.id AS port_id,
        port.name AS port_name,

        port.risk_score AS port_risk,
        port.congestion_level AS congestion,

        manufacturer.id AS manufacturer_id,
        manufacturer.name AS manufacturer_name,
        manufacturer.production_capacity
            AS production_capacity,

        product.id AS product_id,
        product.name AS product_name,

        route.id AS route_id,
        route.name AS route_name,
        route.transit_days AS transit_days,
        route.capacity AS route_capacity,

        warehouse.id AS warehouse_id,
        warehouse.name AS warehouse_name,

        market.id AS market_id,
        market.name AS market_name
    """

    routes = list(
        session.run(query)
    )

    if not routes:
        return []

    dataset = []

    for scenario_id in range(
        1,
        number_of_scenarios + 1,
    ):

        disruption_type = random.choice(
            DISRUPTION_TYPES
        )

        severity = round(
            random.uniform(
                0.4,
                1.0,
            ),
            2,
        )

        selected_port = random.choice(
            routes
        )

        affected_rows = [
            row
            for row in routes
            if row["port_id"]
            == selected_port["port_id"]
        ]

        for row in affected_rows:

            # Manufacturer = hop 1
            # Product = hop 2
            # Warehouse = hop 3
            # Market = hop 4

            impact_score = calculate_impact(
                severity=severity,
                port_risk=(
                    row["port_risk"] or 0
                ),
                congestion=(
                    row["congestion"] or 0
                ),
                transit_days=(
                    row["transit_days"] or 0
                ),
                production_capacity=(
                    row["production_capacity"]
                    or 0
                ),
                route_capacity=(
                    row["route_capacity"]
                    or 1
                ),
                hop_distance=4,
                disruption_type=(
                    disruption_type
                ),
            )

            delay_days = round(
                impact_score * 45,
                2,
            )

            dataset.append({
                "scenario_id": scenario_id,

                "disruption_type":
                    disruption_type,

                "severity":
                    severity,

                "disrupted_port_id":
                    row["port_id"],

                "disrupted_port":
                    row["port_name"],

                "manufacturer_id":
                    row["manufacturer_id"],

                "manufacturer":
                    row["manufacturer_name"],

                "product_id":
                    row["product_id"],

                "product":
                    row["product_name"],

                "route":
                    row["route_name"],

                "warehouse_id":
                    row["warehouse_id"],

                "warehouse":
                    row["warehouse_name"],

                "market_id":
                    row["market_id"],

                "market":
                    row["market_name"],

                "impact_score":
                    impact_score,

                "delay_days":
                    delay_days,
            })

    return dataset


def save_dataset(
    dataset,
    filename="full_ripple_dataset.csv",
):

    if not dataset:
        print("No data generated.")
        return

    fieldnames = dataset[0].keys()

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(dataset)


def main():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            dataset = generate_dataset(
                session,
                number_of_scenarios=100,
            )

            save_dataset(dataset)

            print(
                "\n========== FULL RIPPLE DATASET =========="
            )

            print(
                "Total rows:",
                len(dataset),
            )

            print(
                "Saved to:",
                "full_ripple_dataset.csv",
            )

            print(
                "\n========== SAMPLE =========="
            )

            for row in dataset[:10]:
                print(row)

    finally:
        db.close()


if __name__ == "__main__":
    main()