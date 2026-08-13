from app.services.brand_brain_service import score_trend_for_brand


def _boga():
    return {
        "brand_name": "Boga",
        "industry": "Beverage",
        "country": "Tunisia",
        "audience": "16–35",
        "personality": "funny / Tunisian / accessible",
        "languages": ["derja", "French"],
        "competitors": ["Coca-Cola", "Fanta", "Apla"],
        "channels": ["TikTok", "Instagram", "Facebook"],
        "objectives": ["awareness", "engagement"],
        "forbidden_topics": ["politics", "religion"],
        "tone": "playful",
    }


def test_summer_trend_chase_for_boga():
    trend = {
        "label": "Mediterranean Summer Nostalgia",
        "summary": "Tunisian summer heat music outdoor lifestyle",
        "category": "lifestyle",
        "keywords": ["été", "musique"],
    }
    r = score_trend_for_brand(_boga(), trend, trend_score=87, risk_score=20)
    assert r["verdict"] in ("chase", "caution")
    assert r["fit_percent"] >= 40


def test_politics_forbidden_skip():
    trend = {
        "label": "Débat politique Tunisie",
        "summary": "gouvernement élection parlement",
        "category": "politics",
        "keywords": ["politique"],
    }
    r = score_trend_for_brand(_boga(), trend, trend_score=90, risk_score=80)
    assert r["verdict"] == "skip"
    assert r["fit_percent"] <= 30


def test_global_pop_low_fit_skip_or_low():
    trend = {
        "label": "Taylor Swift Eras Tour buzz",
        "summary": "Taylor Swift Grammy US pop culture",
        "category": "culture",
        "keywords": ["taylor swift"],
    }
    r = score_trend_for_brand(_boga(), trend, trend_score=95, risk_score=15)
    assert r["fit_percent"] < 50
    assert r["verdict"] in ("skip", "caution")
