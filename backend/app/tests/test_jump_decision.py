from app.services.jump_decision_service import _recommendation


def test_yes_when_strong():
    rec, label, _ = _recommendation(
        rad=85, brand_fit=91, risk=20, verdict="chase", saturation=30
    )
    assert rec == "YES"
    assert "YES" in label


def test_no_on_skip_verdict():
    rec, label, _ = _recommendation(
        rad=90, brand_fit=20, risk=20, verdict="skip", saturation=20
    )
    assert rec == "NO"


def test_caution_partial():
    rec, _, _ = _recommendation(
        rad=60, brand_fit=55, risk=40, verdict="caution", saturation=50
    )
    assert rec == "CAUTION"
