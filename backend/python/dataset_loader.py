import csv

from backend.python.db import Neo4jConnection
from backend.python.graph_loader import load_nodes


def load_csv(filename):

    with open(
        filename,
        "r",
        encoding="utf-8",
    ) as file:

        return list(
            csv.DictReader(file)
        )


def create_node_mapping(nodes):

    mapping = {}

    for index, node in enumerate(nodes):

        node_id = node["properties"].get("id")

        if node_id:
            mapping[node_id] = index

    return mapping


def convert_rows_to_targets(
    rows,
    node_mapping,
):

    targets = []

    for row in rows:

        # --------------------------------
        # Manufacturer
        # --------------------------------

        manufacturer_id = (
            row["manufacturer_id"]
        )

        manufacturer_node = node_mapping.get(
            manufacturer_id
        )

        # --------------------------------
        # Product
        # --------------------------------

        product_id = row["product_id"]

        product_node = node_mapping.get(
            product_id
        )

        # --------------------------------
        # Warehouse
        # --------------------------------

        warehouse_id = row["warehouse_id"]

        warehouse_node = node_mapping.get(
            warehouse_id
        )

        # --------------------------------
        # Market
        # --------------------------------

        market_id = row["market_id"]

        market_node = node_mapping.get(
            market_id
        )

        targets.append({

            "scenario_id":
                int(row["scenario_id"]),

            "disruption_type":
                row["disruption_type"],

            "severity":
                float(row["severity"]),

            "manufacturer_node":
                manufacturer_node,

            "product_node":
                product_node,

            "warehouse_node":
                warehouse_node,

            "market_node":
                market_node,

            "impact_score":
                float(row["impact_score"]),

            "delay_days":
                float(row["delay_days"]),
        })

    return targets


def main():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            nodes = load_nodes(session)

            node_mapping = (
                create_node_mapping(nodes)
            )

            rows = load_csv(
                "train.csv"
            )

            targets = (
                convert_rows_to_targets(
                    rows,
                    node_mapping,
                )
            )

            print(
                "\n========== TARGET MAPPING =========="
            )

            print(
                "Total training rows:",
                len(targets),
            )

            print(
                "\n========== SAMPLE =========="
            )

            for target in targets[:10]:

                print(target)

    finally:

        db.close()


if __name__ == "__main__":
    main()