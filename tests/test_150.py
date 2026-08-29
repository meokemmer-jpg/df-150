import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

mod = importlib.import_module("150")

compute_insurance_status = mod.compute_insurance_status
make_asset = mod.make_asset
make_policy = mod.make_policy
make_claim = mod.make_claim


def test_compute_insurance_status_tracks_core_kpm_metrics():
    assets = [
        make_asset("house", "Family House", "500000"),
        make_asset("art", "Art Collection", "100000"),
        make_asset("boat", "Boat", "50000"),
        make_asset("bike", "Vintage Bike", "7000", required_coverage=False),
    ]
    policies = [
        make_policy("p-house", "house", "1200", coverage_limit_eur="500000"),
        make_policy("p-art", "art", "300", coverage_limit_eur="60000"),
        make_policy("p-old", "boat", "100", active=False, coverage_limit_eur="50000"),
    ]
    claims = [
        make_claim("c1", "house", "open"),
        make_claim("c2", "art", "closed"),
        make_claim("c3", "boat", "OPEN"),
    ]

    result = compute_insurance_status(assets, policies, claims)

    assert result["insured_asset_value_eur"] == "560000.00"
    assert result["uninsured_asset_value_eur"] == "90000.00"
    assert result["premium_total_eur"] == "1500.00"
    assert result["open_claims_count"] == 2
    assert result["auto_policy_actions"] == []

    assert result["coverage_gaps"] == [
        {
            "asset_id": "art",
            "name": "Art Collection",
            "gap_type": "underinsured",
            "uncovered_value_eur": "40000.00",
            "action": "manual_review_only",
        },
        {
            "asset_id": "boat",
            "name": "Boat",
            "gap_type": "missing_policy",
            "uncovered_value_eur": "50000.00",
            "action": "manual_review_only",
        },
    ]
