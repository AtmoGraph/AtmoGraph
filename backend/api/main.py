from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.python.db import Neo4jConnection
from backend.python.graph_loader import (
    load_nodes,
    load_relationships,
    create_node_mapping,
    create_graph_edges,
)

from backend.api.nlp_routes import router as nlp_router

app = FastAPI(
    title="AtmoGraph Backend API",
    version="0.1.0",
)

app.include_router(nlp_router)

# React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/predictions")
def get_predictions(request: dict):
    from backend.api.prediction import (
        PredictionRequest,
        predict_scenario,
    )

    prediction_request = PredictionRequest(**request)
    return predict_scenario(prediction_request)

@app.get("/api/health")
def health_check():

    return {
        "status": "ok",
        "service": "AtmoGraph Backend",
        "version": "0.1.0",
    }


@app.get("/api/graph")
def get_graph():

    db = Neo4jConnection()

    try:

        with db.driver.session() as session:

            # Load nodes and relationships from Neo4j
            nodes = load_nodes(session)
            relationships = load_relationships(session)

            # Neo4j element ID -> integer index
            node_mapping = create_node_mapping(nodes)

            # Convert relationships to integer IDs
            edges = create_graph_edges(
                relationships,
                node_mapping,
            )

            # --------------------------------
            # Build frontend nodes
            # --------------------------------

            graph_nodes = []

            for index, node in enumerate(nodes):

                properties = node["properties"]

                graph_nodes.append({
                    "id": properties.get(
                        "id",
                        str(index),
                    ),
                    "name": properties.get(
                        "name",
                        "Unknown",
                    ),
                    "type": (
                        node["labels"][0]
                        if node["labels"]
                        else "Unknown"
                    ),
                    "properties": properties,
                })

            # --------------------------------
            # Build frontend edges
            # --------------------------------

            graph_edges = []

            # Integer node index -> frontend node ID
            index_to_node_id = {
                index: node["properties"].get(
                    "id",
                    str(index),
                )
                for index, node in enumerate(nodes)
            }

            for edge in edges:

                source_index = edge["source"]
                target_index = edge["target"]

                graph_edges.append({
                    "source": index_to_node_id[
                        source_index
                    ],
                    "target": index_to_node_id[
                        target_index
                    ],
                    "type": edge[
                        "relationship_type"
                    ],
                    "properties": edge[
                        "properties"
                    ],
                })

            return {
                "nodes": graph_nodes,
                "edges": graph_edges,
                "total_nodes": len(graph_nodes),
                "total_edges": len(graph_edges),
            }

    finally:

        db.close()
        
@app.get("/api/disruptions")
def get_disruptions():
    db = Neo4jConnection()

    try:
        with db.driver.session() as session:
            query = """
            MATCH (d:Disruption)-[:AFFECTS]->(p:Port)
            RETURN
                d.id AS id,
                d.name AS name,
                d.type AS type,
                d.severity AS severity,
                d.expected_delay_days AS expected_delay_days,
                d.status AS status,
                p.id AS port_id,
                p.name AS port_name
            """

            result = session.run(query)

            disruptions = []

            for record in result:
                disruptions.append({
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"],
                    "severity": record["severity"],
                    "expected_delay_days": record["expected_delay_days"],
                    "status": record["status"],
                    "port_id": record["port_id"],
                    "port_name": record["port_name"],
                })

            return {
                "total": len(disruptions),
                "disruptions": disruptions,
            }

    finally:
        db.close()