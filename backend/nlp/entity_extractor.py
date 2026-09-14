from functools import lru_cache

import spacy

from backend.python.canonical_gnn_graph import load_canonical_gnn_graph

def build_supply_chain_patterns():
    nodes, _ = load_canonical_gnn_graph()

    canonical_patterns = [
        {
            "label": "SUPPLY_CHAIN_ENTITY",
            "pattern": node["properties"]["name"],
            "id": node["properties"]["id"],
        }
        for node in nodes
    ]

    canonical_patterns.extend([
        {
            "label": "SUPPLY_CHAIN_ENTITY",
            "pattern": "Port of Rotterdam",
            "id": "PORT003",
        },
        {
            "label": "SUPPLY_CHAIN_ENTITY",
            "pattern": "Rotterdam Port",
            "id": "PORT003",
        },
    ])

    canonical_names = {
        item["pattern"].casefold()
        for item in canonical_patterns
    }

    legacy_patterns = [
        item
        for item in SUPPLY_CHAIN_PATTERNS
        if item["pattern"].casefold() not in canonical_names
    ]

    return legacy_patterns + canonical_patterns


SUPPLY_CHAIN_PATTERNS = [
    {
        "label": "SUPPLY_CHAIN_ENTITY",
        "pattern": "Nordic Minerals",
        "id": "supplier-sweden",
    },
    {
        "label": "SUPPLY_CHAIN_ENTITY",
        "pattern": "Nordic Metals",
        "id": "supplier-sweden",
    },
    {
        "label": "SUPPLY_CHAIN_ENTITY",
        "pattern": "Port of Rotterdam",
        "id": "port-rotterdam",
    },
    {
        "label": "SUPPLY_CHAIN_ENTITY",
        "pattern": "Rotterdam Port",
        "id": "port-rotterdam",
    },
    {
        "label": "SUPPLY_CHAIN_ENTITY",
        "pattern": "Silica Systems",
        "id": "supplier-taiwan",
    },
    {
        "label": "SUPPLY_CHAIN_ENTITY",
        "pattern": "Atlas Assembly",
        "id": "factory-india",
    },
    {
        "label": "SUPPLY_CHAIN_ENTITY",
        "pattern": "Port of Singapore",
        "id": "port-singapore",
    },
    {
        "label": "SUPPLY_CHAIN_ENTITY",
        "pattern": "Singapore Port",
        "id": "port-singapore",
    },
    {
        "label": "SUPPLY_CHAIN_ENTITY",
        "pattern": "North America DC",
        "id": "distribution-usa",
    },
    {
        "label": "SUPPLY_CHAIN_ENTITY",
        "pattern": "European Market",
        "id": "market-europe",
    },
]


@lru_cache(maxsize=1)
def get_nlp():
    nlp = spacy.load("en_core_web_sm")

    ruler = nlp.add_pipe(
        "entity_ruler",
        before="ner",
        config={"overwrite_ents": True},
    )
    ruler.add_patterns(build_supply_chain_patterns())

    return nlp


def extract_entities(text: str) -> list[dict]:
    if not text or not text.strip():
        return []

    document = get_nlp()(text.strip())
    entities = []
    seen = set()

    for entity in document.ents:
        if entity.label_ not in {
            "SUPPLY_CHAIN_ENTITY",
            "ORG",
            "GPE",
            "LOC",
            "EVENT",
        }:
            continue

        canonical_id = (
            entity.ent_id_
            if entity.label_ == "SUPPLY_CHAIN_ENTITY"
            else None
        )

        identity = (
            entity.text.lower(),
            entity.label_,
            canonical_id,
        )

        if identity in seen:
            continue

        seen.add(identity)

        entities.append(
            {
                "text": entity.text,
                "label": entity.label_,
                "canonical_id": canonical_id,
                "start": entity.start_char,
                "end": entity.end_char,
            }
        )

    return entities