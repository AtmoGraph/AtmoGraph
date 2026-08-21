import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.nlp.disruption_classifier import classify_disruption
from backend.nlp.entity_extractor import extract_entities
from backend.nlp.pipeline import analyze_news, create_disruption_id
from backend.nlp.feed_ingestor import parse_feed_content


SAMPLE_NEWS = (
    "A port strike at the Port of Rotterdam is delaying shipments "
    "from Nordic Minerals to the European Market."
)


def test_extracts_known_supply_chain_entities():
    entities = extract_entities(SAMPLE_NEWS)

    canonical_ids = {
        entity["canonical_id"]
        for entity in entities
        if entity["canonical_id"] is not None
    }

    assert canonical_ids == {
        "port-rotterdam",
        "supplier-sweden",
        "market-europe",
    }


def test_classifies_labour_strike_as_high_risk():
    result = classify_disruption(SAMPLE_NEWS)

    assert result["detected"] is True
    assert result["type"] == "labour_strike"
    assert result["risk_level"] == "high"
    assert result["risk_score"] == 0.9
    assert "strike" in result["matched_keywords"]


def test_disruption_id_is_stable():
    first_id = create_disruption_id(SAMPLE_NEWS)
    second_id = create_disruption_id(
        "  A PORT STRIKE at the Port of Rotterdam "
        "is delaying shipments from Nordic Minerals "
        "to the European Market.  "
    )

    assert first_id == second_id


def test_pipeline_rejects_empty_text():
    with pytest.raises(ValueError, match="cannot be empty"):
        analyze_news("   ")


def test_analyze_endpoint():
    client = TestClient(app)

    response = client.post(
        "/api/nlp/analyze",
        json={
            "text": SAMPLE_NEWS,
            "title": "Rotterdam strike disrupts shipments",
            "source": "Test News",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["classification"]["type"] == "labour_strike"
    assert payload["classification"]["risk_level"] == "high"
    assert payload["affected_node_ids"] == [
        "port-rotterdam",
        "supplier-sweden",
        "market-europe",
    ]

def test_parses_rss_content_without_network():
    rss_content = b"""
    <rss version="2.0">
      <channel>
        <title>Test Supply Chain Feed</title>
        <item>
          <title>Rotterdam port strike</title>
          <description>
            <![CDATA[
              <p>Shipments from Nordic Minerals are delayed.</p>
            ]]>
          </description>
          <link>https://example.com/story</link>
          <pubDate>Fri, 21 Aug 2026 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    articles = parse_feed_content(
        content=rss_content,
        source_name="Test Feed",
        limit=5,
    )

    assert len(articles) == 1
    assert articles[0]["title"] == "Rotterdam port strike"
    assert "<p>" not in articles[0]["text"]
    assert "Nordic Minerals are delayed" in articles[0]["text"]
    assert articles[0]["url"] == "https://example.com/story"