from app.collectors.base import (
    SOURCE_CONFIDENCE,
    CollectedItem,
    CollectionContext,
    SourceMethod,
    confidence_for,
)
from app.collectors.legacy_adapter import legacy_dict_to_collected
from app.collectors.search.social_discovery import build_discovery_queries, detect_platform_from_url, parse_serpapi_organic
from app.services.trend_confirmation_service import confirm_topic
from app.services.trend_seed_service import expand_seed
from app.core.database import get_connection, init_db
from app.repositories import watchlist_repository as wl


def test_source_confidence_table():
    assert SOURCE_CONFIDENCE["official_api"] == 1.0
    assert SOURCE_CONFIDENCE["search_discovery"] == 0.55
    assert SOURCE_CONFIDENCE["mock"] == 0.20
    assert confidence_for(SourceMethod.RSS) == 0.80


def test_collected_item_normalization():
    item = CollectedItem(
        platform="tiktok",
        source_type="search_discovery",
        source_method=SourceMethod.SEARCH_DISCOVERY.value,
        provider="search",
        title="Labubu Tunisia",
        text="snippet",
        url="https://www.tiktok.com/@x/video/1",
        likes=10,
        comments=2,
        confidence=0.55,
    )
    d = item.to_ingest_dict()
    assert d["platform"] == "tiktok"
    assert d["source_method"] == "search_discovery"
    assert d["confidence"] == 0.55
    assert d["engagement"] == 12


def test_legacy_dict_to_collected():
    c = legacy_dict_to_collected(
        {"title": "Hello", "platform": "rss", "source": "Webdo", "url": "https://x"},
        source_method="rss",
        provider="rss",
    )
    assert c is not None
    assert c.source_method == "rss"
    assert c.confidence == 0.80


def test_discovery_query_builder():
    ctx = CollectionContext(brands=["Boga"], topics=["Ramadan"], hashtags=["tunisia"])
    qs = build_discovery_queries(ctx, max_queries=9)
    assert any("site:tiktok.com" in q for q, _ in qs)
    assert any("Boga" in q for q, _ in qs)
    assert detect_platform_from_url("https://www.instagram.com/p/abc/") == "instagram"


def test_parse_serpapi_organic():
    rows = parse_serpapi_organic(
        {
            "organic_results": [
                {"title": "A", "link": "https://www.tiktok.com/@a/video/1", "snippet": "hi"},
                {"title": "B", "url": "https://instagram.com/p/x", "snippet": "yo"},
            ]
        }
    )
    assert len(rows) == 2
    assert rows[0]["url"].startswith("https://")


def test_trend_seed_derja():
    variants = expand_seed("barsha")
    assert any("برشا" in v or "barcha" in v.lower() for v in variants)
    assert any(v.startswith("#") for v in variants)


def test_watchlists_crud():
    init_db()
    with get_connection() as conn:
        default = wl.ensure_default_watchlist(conn)
        wid = int(default["id"])
        term = wl.add_term(conn, wid, "topic", "gaming")
        assert term["value"] == "gaming"
        bundle = wl.watchlist_bundle(conn, wid)
        assert "gaming" in bundle["by_type"]["topic"]
        ctx = wl.default_collection_context(conn)
        assert "Boga" in ctx.brands or len(ctx.all_terms()) > 0
        wl.delete_term(conn, int(term["id"]))


def test_cross_confirm_emptyish():
    init_db()
    with get_connection() as conn:
        report = confirm_topic(conn, "zzzznonexistenttopic999", hours=48)
        assert report["tier"] in ("NONE", "LOW")
        assert "confirmation_score" in report
