from app.services.data_coverage_service import build_signal_coverage


def test_coverage_has_forbidden_and_live():
    cov = build_signal_coverage()
    tiers = {layer["tier"] for layer in cov["layers"]}
    assert "live" in str(cov["layers"][0]["tier"]) or "public_feeds" in {l["id"] for l in cov["layers"]}
    assert "forbidden" in tiers
    assert cov["tunisia_market"]["facebook_users_m"] >= 9
    assert "compliance" in cov["principle"].lower() or "Compliance" in cov["principle"] or "Don't" in cov["principle"]


def test_customer_owned_normalize(tmp_path, monkeypatch):
    from app.collectors import customer_owned_collector as coc

    monkeypatch.setattr(coc, "_CUSTOMER_DIR", tmp_path)
    n = coc.save_customer_owned_payload(
        [{"title": "Hello TN", "platform": "instagram", "engagement": 10}],
        "t.json",
    )
    assert n == 1
    items, status = coc.fetch_customer_owned_items()
    assert len(items) == 1
    assert status[-1]["status"] == "ok"
