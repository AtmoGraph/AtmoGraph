import json
from pathlib import Path

import pytest

from backend.nlp.disruption_classifier import classify_disruption
from backend.nlp.entity_extractor import extract_entities


DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "nlp_review_dataset.json"
)


def load_review_cases():
    with DATASET_PATH.open(encoding="utf-8") as dataset_file:
        return json.load(dataset_file)


REVIEW_CASES = load_review_cases()


@pytest.mark.parametrize(
    "case",
    REVIEW_CASES,
    ids=lambda case: case["id"],
)
def test_review_case_classification(case):
    result = classify_disruption(case["text"])

    assert result["type"] == case["expected_disruption_type"]
    assert result["risk_level"] == case["expected_risk_level"]


@pytest.mark.parametrize(
    "case",
    REVIEW_CASES,
    ids=lambda case: case["id"],
)
def test_review_case_canonical_entities(case):
    entities = extract_entities(case["text"])

    actual_ids = {
        entity["canonical_id"]
        for entity in entities
        if entity["canonical_id"] is not None
    }
    expected_ids = set(case["expected_entity_ids"])

    assert actual_ids == expected_ids


def test_canonical_entity_micro_metrics():
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for case in REVIEW_CASES:
        expected_ids = set(case["expected_entity_ids"])
        actual_ids = {
            entity["canonical_id"]
            for entity in extract_entities(case["text"])
            if entity["canonical_id"] is not None
        }

        true_positives += len(actual_ids & expected_ids)
        false_positives += len(actual_ids - expected_ids)
        false_negatives += len(expected_ids - actual_ids)

    precision = true_positives / (
        true_positives + false_positives
    )
    recall = true_positives / (
        true_positives + false_negatives
    )
    f1_score = 2 * precision * recall / (
        precision + recall
    )

    assert precision >= 0.90
    assert recall >= 0.90
    assert f1_score >= 0.90