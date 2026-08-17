import csv
import random


from backend.python.config import (
    FULL_RIPPLE_DATASET,
    TRAIN_FILE,
    VALIDATION_FILE,
    TEST_FILE,
)


TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15


def load_dataset():

    with open(
        FULL_RIPPLE_DATASET,
        "r",
        encoding="utf-8",
    ) as file:

        return list(
            csv.DictReader(file)
        )


def save_dataset(rows, filename):

    if not rows:
        return

    fieldnames = rows[0].keys()

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
        writer.writerows(rows)


def main():

    rows = load_dataset()

    # ---------------------------------
    # Get unique scenarios
    # ---------------------------------

    scenario_ids = sorted(
        {
            row["scenario_id"]
            for row in rows
        }
    )

    print(
        "Total scenarios:",
        len(scenario_ids)
    )

    # ---------------------------------
    # Shuffle scenarios
    # ---------------------------------

    random.seed(42)

    random.shuffle(
        scenario_ids
    )

    # ---------------------------------
    # Calculate split sizes
    # ---------------------------------

    total = len(scenario_ids)

    train_end = int(
        total * TRAIN_RATIO
    )

    validation_end = (
        train_end
        + int(
            total
            * VALIDATION_RATIO
        )
    )

    train_scenarios = set(
        scenario_ids[:train_end]
    )

    validation_scenarios = set(
        scenario_ids[
            train_end:validation_end
        ]
    )

    test_scenarios = set(
        scenario_ids[
            validation_end:
        ]
    )

    # ---------------------------------
    # Split rows
    # ---------------------------------

    train_rows = []
    validation_rows = []
    test_rows = []

    for row in rows:

        scenario_id = row[
            "scenario_id"
        ]

        if scenario_id in train_scenarios:
            train_rows.append(row)

        elif scenario_id in validation_scenarios:
            validation_rows.append(row)

        elif scenario_id in test_scenarios:
            test_rows.append(row)

    # ---------------------------------
    # Save
    # ---------------------------------

    save_dataset(
        train_rows,
        TRAIN_FILE
    )

    save_dataset(
        validation_rows,
        VALIDATION_FILE
    )

    save_dataset(
        test_rows,
        TEST_FILE
    )

    # ---------------------------------
    # Summary
    # ---------------------------------

    print(
        "\n========== DATASET SPLIT =========="
    )

    print(
        "Training scenarios:",
        len(train_scenarios)
    )

    print(
        "Validation scenarios:",
        len(validation_scenarios)
    )

    print(
        "Test scenarios:",
        len(test_scenarios)
    )

    print(
        "\nTraining rows:",
        len(train_rows)
    )

    print(
        "Validation rows:",
        len(validation_rows)
    )

    print(
        "Test rows:",
        len(test_rows)
    )

    print(
        "\nFiles created:"
    )

    print(
        TRAIN_FILE
    )

    print(
        VALIDATION_FILE
    )

    print(
        TEST_FILE
    )


if __name__ == "__main__":
    main()