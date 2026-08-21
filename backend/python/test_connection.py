from backend.python.db import Neo4jConnection


def main():
    db = Neo4jConnection()

    try:
        with db.driver.session() as session:
            result = session.run(
                "MATCH (n) RETURN count(n) AS node_count"
            )

            record = result.single()

            print("Node count:", record["node_count"])

    finally:
        db.close()


if __name__ == "__main__":
    main()