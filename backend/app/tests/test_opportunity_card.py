from app.services.opportunity_card_service import (
    _audience,
    _campaign_name,
    _fit_reasons,
    _lifecycle,
    _momentum,
    _saturation,
)


def test_momentum_rapid_when_growth_high():
    m = _momentum(
        {
            "growth_score": 80,
            "trend_score": 70,
            "volume_score": 40,
            "diversity_score": 40,
            "recency_score": 80,
            "risk_score": 20,
            "engagement_score": 40,
        }
    )
    assert m["arrow"] == "up_fast"
    assert m["score"] >= 70


def test_lifecycle_early_growth():
    life = _lifecycle(
        {
            "growth_score": 70,
            "volume_score": 20,
            "diversity_score": 30,
            "recency_score": 90,
            "trend_score": 60,
            "risk_score": 25,
            "engagement_score": 20,
        },
        first_seen=None,
    )
    assert life["key"] == "early_growth"


def test_beverage_fit_reasons():
    reasons = _fit_reasons(
        {"sector": "food/beverage", "target": "Gen Z students"},
        {"category": "weather", "label": "Summer heat nostalgia", "summary": "music outdoor"},
        85,
    )
    assert any("consommation" in r or "jeune" in r or "outdoor" in r for r in reasons)


def test_summer_campaign_derja():
    assert "صيف" in _campaign_name("Mediterranean Summer Nostalgia", {"sector": "beverage"})


def test_saturation_bounded():
    s = _saturation(
        {
            "growth_score": 30,
            "volume_score": 90,
            "diversity_score": 40,
            "recency_score": 20,
            "trend_score": 40,
            "risk_score": 20,
            "engagement_score": 40,
        }
    )
    assert 0 <= s <= 100


def test_audience_label():
    a = _audience("lifestyle", "18-30 fashion")
    assert "18–35" in a["label"] or "lifestyle" in a["label"]
