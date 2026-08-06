import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

m150 = importlib.import_module("150")
summarize_insurance_coverage = m150.summarize_insurance_coverage
calculate_asset_statuses = m150.calculate_asset_statuses


def test_summarize_insurance_coverage_tracks_values_premiums_claims_and_gaps():
    assets = [
        {"asset_id": "house", "value_eur": 500000},
        {"asset_id": "car", "value_eur": 20000},
        {"asset_id": "art", "value_eur": 10000},
    ]
    policies = [
        {"asset_id": "house", "coverage_amount_eur": 500000, "premium_eur": 1200, "active": True},
        {"asset_id": "car", "coverage_amount_eur": 15000, "premium_eur": 300, "active": True},
        {"asset_id": "art", "coverage_amount_eur": 10000, "premium_eur": 50, "active": False},
    ]
    claims = [
        {"claim_id": "c1", "status": "open"},
        {"claim_id": "c2", "status": "closed"},
        {"claim_id": "c3", "status": "pending"},
    ]

    result = summarize_insurance_coverage(assets, policies, claims)

    assert result["insured_value_eur"] == 515000.0
    assert result["uninsured_value_eur"] == 15000.0
    assert result["premium_total_eur"] == 1500.0
    assert result["open_claims_count"] == 2
    assert result["auto_policy_action"] is None
    assert result["coverage_gaps"] == [
        {"asset_id": "car", "gap_eur": 5000.0, "reason": "uninsured_value"},
        {"asset_id": "art", "gap_eur": 10000.0, "reason": "uninsured_value"},
    ]

    statuses = calculate_asset_statuses(assets, policies)
    assert [s.asset_id for s in statuses] == ["house", "car", "art"]
    assert statuses[0].is_fully_insured is True
    assert statuses[1].insured_value_eur == 15000.0
    assert statuses[1].uninsured_value_eur == 5000.0
    assert statuses[2].insured_value_eur == 0.0
    assert statuses[2].uninsured_value_eur == 10000.0
