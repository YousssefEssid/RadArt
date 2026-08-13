from app.services.rad_score_service import compute_rad_score


def test_high_rad_tier():
    r = compute_rad_score(
        momentum=88,
        freshness=90,
        tunisia_relevance=92,
        audience_overlap=85,
        brand_fit=90,
        source_diversity=80,
        competitive_saturation=25,
        brand_safety_risk=20,
        brand_name="Boga",
    )
    assert r["score_int"] >= 80
    assert r["tier"]["key"] == "high"
    assert "Relevance" in r["why"] or "relevance" in r["why"].lower() or "RAD" in r["why"]


def test_skip_caps_rad():
    r = compute_rad_score(
        momentum=95,
        freshness=95,
        tunisia_relevance=40,
        audience_overlap=30,
        brand_fit=20,
        source_diversity=70,
        competitive_saturation=40,
        brand_safety_risk=80,
        verdict="skip",
    )
    assert r["score"] <= 32
    assert "don’t-chase" in r["why"] or "dont" in r["why"].lower() or "chase" in r["why"].lower()


def test_pillars_present():
    r = compute_rad_score(
        momentum=60,
        freshness=55,
        tunisia_relevance=50,
        audience_overlap=50,
        brand_fit=50,
        source_diversity=50,
        competitive_saturation=50,
        brand_safety_risk=30,
    )
    assert set(r["pillars"]) == {"relevance", "acceleration", "differentiation"}
    assert "momentum" in r["components"]
