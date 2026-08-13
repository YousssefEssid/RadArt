from app.services.war_room_service import _opportunity_gaps


def test_classic_convenience_gap():
    dossiers = [
        {"name": "Competitor A", "themes_owned": ["price"]},
        {"name": "Competitor B", "themes_owned": ["premium"]},
    ]
    gaps = _opportunity_gaps(dossiers, "Boga")
    themes = {g["theme"] for g in gaps}
    assert "convenience" in themes
    classic = next(g for g in gaps if g["theme"] == "convenience")
    assert "Convenience" in classic["opportunity"] or "convenience" in classic["opportunity"].lower()


def test_white_space_when_nobody_owns():
    dossiers = [
        {"name": "A", "themes_owned": ["price"]},
        {"name": "B", "themes_owned": ["price"]},
    ]
    gaps = _opportunity_gaps(dossiers, "X")
    assert any(g["theme"] == "premium" and g["gap_type"] == "white_space" for g in gaps)
