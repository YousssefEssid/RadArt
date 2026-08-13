from app.services.morning_radar_service import classify_trend


def test_emerging_beats_fading_when_accelerating():
    trend = {
        "id": 1,
        "label": "Exam memes",
        "summary": "students caffeine",
        "category": "youth",
        "keywords": ["examen"],
        "trend_score": 62,
        "risk_score": 30,
        "source_count": 3,
        "item_count": 5,
        "first_seen_at": None,
        "last_seen_at": None,
        "latest_items": [],
    }
    scores = {
        "growth_score": 80.0,
        "volume_score": 20.0,
        "diversity_score": 40.0,
        "recency_score": 90.0,
    }
    hits = classify_trend(trend, scores, competitors=[], sector="beverage / students")
    assert hits
    assert hits[0][0] == "emerging"


def test_reputation_on_high_risk():
    trend = {
        "id": 2,
        "label": "Scandale politique",
        "summary": "crise gouvernement",
        "category": "politics",
        "keywords": ["politique"],
        "trend_score": 70,
        "risk_score": 85,
        "source_count": 4,
        "item_count": 10,
        "first_seen_at": None,
        "last_seen_at": None,
        "latest_items": [],
    }
    scores = {
        "growth_score": 60.0,
        "volume_score": 50.0,
        "diversity_score": 50.0,
        "recency_score": 80.0,
    }
    hits = classify_trend(trend, scores, competitors=[], sector=None)
    assert hits[0][0] == "reputation"


def test_competitor_match():
    trend = {
        "id": 3,
        "label": "Ooredoo summer push",
        "summary": "campagne ooredoo",
        "category": "telecom",
        "keywords": [],
        "trend_score": 55,
        "risk_score": 25,
        "source_count": 2,
        "item_count": 4,
        "first_seen_at": None,
        "last_seen_at": None,
        "latest_items": [{"title": "Ooredoo offre", "source": "web"}],
    }
    scores = {
        "growth_score": 55.0,
        "volume_score": 40.0,
        "diversity_score": 30.0,
        "recency_score": 70.0,
    }
    hits = classify_trend(trend, scores, competitors=["Ooredoo", "Orange"], sector="telecom")
    assert hits[0][0] == "competitor_move"
    assert hits[0][2].get("competitor") == "Ooredoo"
