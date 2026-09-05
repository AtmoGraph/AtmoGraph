from fastapi import APIRouter, HTTPException , Query
from pydantic import BaseModel, Field

from backend.nlp.neo4j_writer import write_analysis
from backend.nlp.pipeline import analyze_news

from backend.nlp.feed_ingestor import FEED_SOURCES, fetch_feed
from backend.api.prediction import PredictionRequest, predict_scenario
from backend.api.realtime import publish_event

router = APIRouter(
    prefix="/api/nlp",
    tags=["NLP"],
)


PORT_ALIASES = {
    "port-rotterdam": "PORT003",
}

MODEL_DISRUPTION_TYPES = {
    "labour_strike": "PORT_STRIKE",
    "extreme_weather": "SEVERE_WEATHER",
    "fire_or_explosion": "INFRASTRUCTURE_FAILURE",
    "port_congestion": "PORT_CLOSURE",
    "capacity_reduction": "PORT_CLOSURE",
    "transport_delay": "PORT_CLOSURE",
    "sanctions": "PORT_CLOSURE",
}


def _prediction_for_analysis(analysis, horizon_days=30):
    live_port_id = next(
        (
            node_id
            for node_id in analysis["affected_node_ids"]
            if node_id in PORT_ALIASES
        ),
        None,
    )
    if live_port_id is None:
        return None

    classification = analysis["classification"]
    model_type = MODEL_DISRUPTION_TYPES.get(classification["type"])
    if model_type is None:
        return None

    return predict_scenario(
        PredictionRequest(
            disrupted_port_id=PORT_ALIASES[live_port_id],
            disruption_type=model_type,
            severity=classification["risk_score"],
            horizon_days=horizon_days,
        )
    )


class NewsRequest(BaseModel):
    text: str = Field(min_length=1)
    title: str | None = None
    source: str | None = None
    url: str | None = None


@router.post("/analyze")
def analyze_news_text(request: NewsRequest):
    try:
        return analyze_news(
            text=request.text,
            title=request.title,
            source=request.source,
            url=request.url,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.post("/ingest")
def ingest_news_text(request: NewsRequest):
    try:
        analysis = analyze_news(
            text=request.text,
            title=request.title,
            source=request.source,
            url=request.url,
        )

        database_result = write_analysis(analysis)

        prediction = _prediction_for_analysis(analysis)
        publish_event(
            "disruption.ingested",
            {
                "analysis": analysis,
                "database": database_result,
                "prediction": prediction,
            },
        )

        return {
            "analysis": analysis,
            "database": database_result,
            "prediction": prediction,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

@router.get("/feeds")
def list_feed_sources():
    return {
        "feeds": [
            {
                "key": key,
                "name": source["name"],
            }
            for key, source in FEED_SOURCES.items()
        ]
    }


@router.post("/feeds/{feed_key}/analyze")
def analyze_feed(
    feed_key: str,
    limit: int = Query(default=5, ge=1, le=50),
):
    try:
        articles = fetch_feed(
            feed_key=feed_key,
            limit=limit,
        )

        results = []

        for article in articles:
            analysis = analyze_news(
                text=article["text"],
                title=article["title"],
                source=article["source"],
                url=article["url"],
            )

            results.append(
                {
                    "published": article["published"],
                    "analysis": analysis,
                }
            )

        return {
            "feed": feed_key,
            "article_count": len(results),
            "articles": results,
        }
    except (ValueError, RuntimeError) as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error
