# AtmoGraph Backend

The AtmoGraph backend provides:

- Neo4j supply-chain graph storage
- FastAPI endpoints for graph and disruption data
- spaCy-based named entity recognition
- Rule-based disruption classification
- RSS news-feed ingestion
- Neo4j risk-state updates

## Requirements

- Python 3.12
- Neo4j Desktop
- Neo4j instance running on port `7687`

## Environment setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\backend\requirements.txt
python -m spacy download en_core_web_sm
```

Copy `.env.example` to `.env` and add your own Neo4j password:

```env
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_private_password
NEO4J_DATABASE=neo4j
```

Never commit `.env`.

## Seed the graph

Start Neo4j, then run:

```powershell
python -m backend.python.seed_graph
```

Expected output:

```text
Graph seeded successfully: 7 nodes, 7 relationships
```

The seed operation is idempotent and can safely be run again.

## Start the API

```powershell
python -m uvicorn backend.api.main:app --reload --port 8001
```

API documentation:

```text
http://127.0.0.1:8001/docs
```

## NLP endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/nlp/analyze` | Analyze supplied news text without database writes |
| POST | `/api/nlp/ingest` | Analyze news and update affected Neo4j nodes |
| GET | `/api/nlp/feeds` | List allowlisted RSS feeds |
| POST | `/api/nlp/feeds/{feed_key}/analyze` | Retrieve and analyze current RSS articles |

Example request:

```json
{
  "text": "A port strike at the Port of Rotterdam is delaying shipments from Nordic Minerals.",
  "title": "Rotterdam strike disrupts shipments",
  "source": "Demo News"
}
```

## Tests

From the repository root:

```powershell
python -m pytest .\backend\tests -v
```

The tests cover:

- Known supply-chain entity extraction
- Disruption classification
- Stable disruption IDs
- Input validation
- FastAPI analysis endpoint
- Offline RSS parsing