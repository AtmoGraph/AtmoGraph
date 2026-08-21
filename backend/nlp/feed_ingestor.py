from html import unescape
from html.parser import HTMLParser
from urllib.request import Request, urlopen

import feedparser


FEED_SOURCES = {
    "supply_chain_crisis": {
        "name": "SupplyChainBrain - Supply Chains in Crisis",
        "url": (
            "https://www.supplychainbrain.com/"
            "rss/topic/1347-supply-chains-in-crisis"
        ),
    },
}


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(" ".join(self.parts).split())


def strip_html(value: str) -> str:
    parser = HTMLTextExtractor()
    parser.feed(unescape(value or ""))
    return parser.get_text()


def parse_feed_content(
    content: bytes,
    source_name: str,
    limit: int = 10,
) -> list[dict]:
    if not 1 <= limit <= 50:
        raise ValueError("Feed limit must be between 1 and 50")

    feed = feedparser.parse(content)
    articles = []

    for entry in feed.entries[:limit]:
        title = strip_html(entry.get("title", "Untitled"))
        summary = strip_html(
            entry.get("summary")
            or entry.get("description")
            or ""
        )

        text = " ".join(
            part
            for part in [title, summary]
            if part
        )

        articles.append(
            {
                "title": title,
                "text": text,
                "source": source_name,
                "url": entry.get("link"),
                "published": entry.get("published"),
            }
        )

    return articles


def fetch_feed(
    feed_key: str,
    limit: int = 10,
) -> list[dict]:
    source = FEED_SOURCES.get(feed_key)

    if source is None:
        raise ValueError(f"Unknown feed source: {feed_key}")

    request = Request(
        source["url"],
        headers={
            "User-Agent": "AtmoGraph/0.1 (+local development)",
            "Accept": (
                "application/rss+xml, application/xml, "
                "text/xml;q=0.9"
            ),
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            content = response.read()
    except OSError as error:
        raise RuntimeError(
            f"Could not retrieve feed '{feed_key}'"
        ) from error

    articles = parse_feed_content(
        content=content,
        source_name=source["name"],
        limit=limit,
    )

    if not articles:
        raise RuntimeError(
            f"Feed '{feed_key}' returned no articles"
        )

    return articles