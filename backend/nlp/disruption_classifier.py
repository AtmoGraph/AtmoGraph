import re


DISRUPTION_RULES = [
    {
        "type": "fire_or_explosion",
        "keywords": ["fire", "explosion", "blast"],
        "risk_level": "high",
        "risk_score": 1.0,
    },
    {
        "type": "labour_strike",
        "keywords": ["strike", "walkout", "labour action", "labor action"],
        "risk_level": "high",
        "risk_score": 0.9,
    },
    {
        "type": "port_congestion",
        "keywords": ["port congestion", "congestion", "vessel backlog", "backlog"],
        "risk_level": "high",
        "risk_score": 0.85,
    },
    {
        "type": "extreme_weather",
        "keywords": ["flood", "hurricane", "cyclone", "typhoon", "storm"],
        "risk_level": "high",
        "risk_score": 0.8,
    },
    {
        "type": "sanctions",
        "keywords": ["sanction", "embargo", "trade restriction"],
        "risk_level": "high",
        "risk_score": 0.8,
    },
    {
        "type": "capacity_reduction",
        "keywords": [
            "capacity reduced",
            "reduced capacity",
            "capacity shortage",
            "shortage",
        ],
        "risk_level": "medium",
        "risk_score": 0.65,
    },
    {
        "type": "transport_delay",
        "keywords": ["delay", "delayed", "disruption", "disrupted"],
        "risk_level": "medium",
        "risk_score": 0.55,
    },
]


def _contains_keyword(text: str, keyword: str) -> bool:
    pattern = rf"\b{re.escape(keyword)}\b"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def classify_disruption(text: str) -> dict:
    if not text or not text.strip():
        return {
            "detected": False,
            "type": "unknown",
            "risk_level": "low",
            "risk_score": 0.0,
            "matched_keywords": [],
        }

    matches = []

    for rule in DISRUPTION_RULES:
        matched_keywords = [
            keyword
            for keyword in rule["keywords"]
            if _contains_keyword(text, keyword)
        ]

        if matched_keywords:
            matches.append(
                {
                    **rule,
                    "matched_keywords": matched_keywords,
                }
            )

    if not matches:
        return {
            "detected": False,
            "type": "unknown",
            "risk_level": "low",
            "risk_score": 0.0,
            "matched_keywords": [],
        }

    strongest_match = max(
        matches,
        key=lambda match: match["risk_score"],
    )

    return {
        "detected": True,
        "type": strongest_match["type"],
        "risk_level": strongest_match["risk_level"],
        "risk_score": strongest_match["risk_score"],
        "matched_keywords": strongest_match["matched_keywords"],
    }