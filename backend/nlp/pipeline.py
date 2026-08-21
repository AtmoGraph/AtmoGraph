import hashlib
from datetime import datetime, timezone

from backend.nlp.disruption_classifier import classify_disruption
from backend.nlp.entity_extractor import extract_entities


def create_disruption_id(text: str) -> str:
    normalized_text = " ".join(text.lower().split())
    digest = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    return f"disruption-{digest[:16]}"


def analyze_news(
    text: str,
    title: str | None = None,
    source: str | None = None,
    url: str | None = None,
) -> dict:
    cleaned_text = " ".join(text.split())

    if not cleaned_text:
        raise ValueError("News text cannot be empty")

    entities = extract_entities(cleaned_text)
    classification = classify_disruption(cleaned_text)

    affected_node_ids = list(
        dict.fromkeys(
            entity["canonical_id"]
            for entity in entities
            if entity["canonical_id"] is not None
        )
    )

    return {
        "disruption_id": create_disruption_id(cleaned_text),
        "title": title or cleaned_text[:100],
        "text": cleaned_text,
        "source": source,
        "url": url,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "classification": classification,
        "entities": entities,
        "affected_node_ids": affected_node_ids,
    }