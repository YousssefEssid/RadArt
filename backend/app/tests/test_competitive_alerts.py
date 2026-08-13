from app.services.competitive_alerts_service import _acceleration_pct, _build_alert, _response_angle


def test_acceleration_positive():
    assert _acceleration_pct(12, 9) == round(100 * 3 / 9, 1)


def test_back_to_school_alert_copy():
    a = _build_alert(
        competitor="Coca-Cola",
        theme="back_to_school",
        recent_count=12,
        previous_count=9,
        window_hours=48,
        brand_name="Boga",
        sample_titles=["promo rentrée"],
    )
    assert "Competitor movement" in a["headline"]
    assert "12 pieces" in a["summary"]
    assert "Parents vs Students" in a["recommendation"]
    assert a["acceleration_pct"] > 0


def test_diff_angle_price():
    assert "convenience" in _response_angle("price", "Boga").lower() or "Don’t" in _response_angle("price", None)
