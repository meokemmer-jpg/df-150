import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
try:
    exec("from 150 import Asset, Policy, Claim, compute_report")
except SyntaxError:
    from importlib import import_module as _import_module
    _mod = _import_module("150")
    Asset, Policy, Claim, compute_report = (
        _mod.Asset,
        _mod.Policy,
        _mod.Claim,
        _mod.compute_report,
    )


def test_compute_report_tracks_insurance_status():
    assets = [
        Asset("a1", 100.0),
        Asset("a2", 200.0),
        Asset("a3", 300.0),
    ]
    policies = [
        Policy("p1", "a1", 10.0, 100.0),
        Policy("p2", "a2", 20.0, 150.0),
        Policy("p3", "a3", 30.0, 300.0, status="cancelled"),
    ]
    claims = [
        Claim("c1", "p1", "open"),
        Claim("c2", "p1", "closed"),
        Claim("c3", "p2", "open"),
    ]

    report = compute_report(assets, policies, claims)

    assert report["insured_value_eur"] == 300.0
    assert report["uninsured_value_eur"] == 300.0
    assert report["premium_total_eur"] == 30.0
    assert report["open_claims_count"] == 2

    per_asset = {item["asset_id"]: item for item in report["per_asset"]}
    assert per_asset["a1"]["insured"] is True
    assert per_asset["a1"]["coverage_gap"] is False
    assert per_asset["a2"]["insured"] is True
    assert per_asset["a2"]["coverage_gap"] is True
    assert per_asset["a3"]["insured"] is False
    assert per_asset["a3"]["coverage_gap"] is True
    assert per_asset["a1"]["open_claims_count"] == 1
    assert per_asset["a2"]["open_claims_count"] == 1
    assert per_asset["a3"]["open_claims_count"] == 0

    gaps = {gap["asset_id"]: gap for gap in report["coverage_gaps"]}
    assert set(gaps) == {"a2", "a3"}
    assert gaps["a2"]["reason"] == "underinsured"
    assert gaps["a2"]["gap_eur"] == 50.0
    assert gaps["a3"]["reason"] == "uninsured"
    assert gaps["a3"]["gap_eur"] == 300.0

    # No auto-policy-buy/cancel: inputs remain untouched.
    assert len(policies) == 3
    assert policies[0].status == "active"
    assert policies[1].status == "active"
    assert policies[2].status == "cancelled"
