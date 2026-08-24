# AtmoGraph Mid-Project Backend Review

## Review objective

Demonstrate that the Week 2 NLP pipeline can:

1. Extract known supply-chain entities from news text.
2. Classify disruption type and risk level.
3. Insert disruption information into Neo4j.
4. Update the correct supply-chain nodes.
5. Avoid duplicate disruption nodes and relationships when the same article is ingested repeatedly.

## Evaluation scope

The controlled evaluation dataset contains 10 labelled news samples covering:

- Labour strikes
- Port congestion
- Extreme weather
- Capacity reduction
- Transport delays
- Fire or explosion
- Sanctions
- Normal non-disruption news
- Alternative known entity names
- Text containing no known supply-chain entity

The evaluation measures canonical matching for entities already represented in the demonstration Neo4j graph. It does not claim recognition of every possible company, port or location worldwide.

## Entity extraction evaluation

The expected canonical entity IDs were compared with the IDs returned by the NLP entity extractor.

Metrics used:

- Precision
- Recall
- F1 score

Required threshold:

- Precision >= 0.90
- Recall >= 0.90
- F1 >= 0.90

All labelled canonical-entity cases passed the required thresholds.

## Disruption classification evaluation

Each review article defines an expected:

- Disruption type
- Risk level

All 10 disruption-classification cases passed.

## Neo4j ingestion validation

A controlled article affecting the Port of Rotterdam and Nordic Minerals was ingested twice.

Validated conditions:

- Exactly one `Disruption` node existed after repeated ingestion.
- Exactly two `AFFECTS` relationships existed.
- Both expected supply-chain nodes were updated.
- The original node risk values were restored after the test.
- The temporary review disruption was deleted after the test.

The ingestion test passed.

## Verification commands

From the repository root:

```powershell
python -m json.tool `
    ".\backend\data\nlp_review_dataset.json"

python -m pytest `
    ".\backend\tests\test_nlp_accuracy.py" -v

python -m pytest `
    ".\backend\tests\test_neo4j_ingestion.py" -v

python -m pytest ".\backend\tests" -q