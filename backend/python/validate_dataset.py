import csv
from collections import Counter


from backend.python.config import FULL_RIPPLE_DATASET

DATASET_FILE = FULL_RIPPLE_DATASET

def load_dataset():
    with open(
        DATASET_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return list(
            csv.DictReader(file)
        )


def main():

    rows = load_dataset()

    print("\n========== DATASET VALIDATION ==========")

    print("Total rows:", len(rows))

    # -------------------------------
    # Scenario count
    # -------------------------------

    scenarios = {
        row["scenario_id"]
        for row in rows
    }

    print(
        "Unique scenarios:",
        len(scenarios)
    )

    # -------------------------------
    # Disruption types
    # -------------------------------

    disruption_types = Counter(
        row["disruption_type"]
        for row in rows
    )

    print(
        "\nDisruption types:"
    )

    for name, count in sorted(
        disruption_types.items()
    ):
        print(
            f"{name}: {count}"
        )

    # -------------------------------
    # Ports
    # -------------------------------

    ports = Counter(
        row["disrupted_port"]
        for row in rows
    )

    print("\nAffected ports:")

    for port, count in sorted(
        ports.items()
    ):
        print(
            f"{port}: {count}"
        )

    # -------------------------------
    # Target statistics
    # -------------------------------

    impact_scores = [
        float(row["impact_score"])
        for row in rows
    ]

    delay_days = [
        float(row["delay_days"])
        for row in rows
    ]

    print(
        "\n========== TARGET STATISTICS =========="
    )

    print(
        "Minimum impact:",
        min(impact_scores)
    )

    print(
        "Maximum impact:",
        max(impact_scores)
    )

    print(
        "Average impact:",
        round(
            sum(impact_scores)
            / len(impact_scores),
            4,
        )
    )

    print(
        "Minimum delay:",
        min(delay_days)
    )

    print(
        "Maximum delay:",
        max(delay_days)
    )

    print(
        "Average delay:",
        round(
            sum(delay_days)
            / len(delay_days),
            2,
        ),
    )

    # -------------------------------
    # Missing values
    # -------------------------------

    required_columns = [
        "scenario_id",
        "disruption_type",
        "severity",
        "disrupted_port_id",
        "manufacturer_id",
        "product_id",
        "warehouse_id",
        "market_id",
        "impact_score",
        "delay_days",
    ]

    missing_values = 0

    for row in rows:

        for column in required_columns:

            if (
                row.get(column)
                is None
                or row.get(column) == ""
            ):
                missing_values += 1

    print(
        "\nMissing required values:",
        missing_values
    )

    # -------------------------------
    # Sample
    # -------------------------------

    print(
        "\n========== FIRST ROW =========="
    )

    print(rows[0])


if __name__ == "__main__":
    main()