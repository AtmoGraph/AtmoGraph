import csv
import random

from backend.python.db import Neo4jConnection


DISRUPTION_TYPES = [
    "PORT_STRIKE",
    "PORT_CLOSURE",
    "SEVERE_WEATHER",
    "INFRASTRUCTURE_FAILURE",
]

PORTS = [
    "Taipei Port",
    "Shanghai Port",
    "Rotterdam Port",
    "Hamburg Port",
    "Los Angeles Port",
    "Vancouver Port",
]


def calculate_impact(
    severity,
    port_risk,
    congestion,
    transit_days,
):
    """
    Synthetic impact formula.

    This is NOT a trained ML model.
    It creates development labels.
    """

    impact_score = (
        severity
        * 0.40
        + port_risk
        * 0.25
        + congestion
        * 0.20
        + min(transit_days / 30.0, 1.0)
        * 0.15
    )

    return round(impact_score, 4)


def calculate_delay(
    severity,
    impact_score,
    transit_days,
):
    """
    Synthetic delay target.
    """

    base_delay = (
        severity * 20
        + impact_score * 15
    )

    route_factor = min(
        transit_days / 30.0,
        1.0
    )

    delay = base_delay + (
        route_factor * 10
    )

    return round(delay, 2)


def generate_scenarios(session, number_of_scenarios=100):

    query = """
    MATCH (p:Port)
    RETURN
        p.id AS port_id,
        p.name AS port_name,
        p.congestion_level AS congestion,
        p.risk_score AS risk
    """

    ports = list(session.run(query))

    scenarios = []

    for scenario_id in range(
        1,
        number_of_scenarios + 1
    ):

        port = random.choice(ports)

        disruption_type = random.choice(
            DISRUPTION_TYPES
        )

        severity = round(
            random.uniform(0.4, 1.0),
            2
        )

        transit_query = """
            MATCH (route:ShippingRoute)
                -[:FROM|TO]->
                (port:Port {id: $port_id})
            RETURN avg(route.transit_days) AS avg_transit
            """

        transit_result = session.run(
            transit_query,
            port_id=port["port_id"]
        ).single()

        avg_transit = (
            transit_result["avg_transit"]
            or 0
        )

        impact_score = calculate_impact(
            severity=severity,
            port_risk=port["risk"] or 0,
            congestion=port["congestion"] or 0,
            transit_days=avg_transit,
        )

        delay_days = calculate_delay(
            severity=severity,
            impact_score=impact_score,
            transit_days=avg_transit,
        )

        scenarios.append({
            "scenario_id": scenario_id,
            "port_id": port["port_id"],
            "port_name": port["port_name"],
            "disruption_type": disruption_type,
            "severity": severity,
            "port_risk": port["risk"] or 0,
            "port_congestion": port["congestion"] or 0,
            "avg_transit_days": round(
                avg_transit,
                2
            ),
            "impact_score": impact_score,
            "delay_days": delay_days,
        })

    return scenarios


def save_scenarios(
    scenarios,
    filename="synthetic_disruptions.csv",
):

    fieldnames = scenarios[0].keys()

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
        writer.writerows(scenarios)


def main():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            scenarios = generate_scenarios(
                session,
                number_of_scenarios=100,
            )

            save_scenarios(
                scenarios
            )

            print(
                "\n========== SCENARIO DATASET =========="
            )

            print(
                "Total scenarios:",
                len(scenarios)
            )

            print(
                "Saved to:",
                "synthetic_disruptions.csv"
            )

            print(
                "\n========== SAMPLE SCENARIOS =========="
            )

            for scenario in scenarios[:10]:
                print(scenario)

    finally:
        db.close()


if __name__ == "__main__":
    main()