import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

m150 = importlib.import_module("150")
summarize_insurance_status = m150.summarize_insurance_status
evaluate_asset = m150.evaluate_asset


def test_summarize_insurance_status_tracks_values_claims_and_gaps():
    assets = [
        {
            "asset_id": "house-1",
            "name": "Family House",
            "value_eur": 500000,
            "insured": True,
            "premium_eur": 1200,
            "coverage_limit_eur": 500000,
        },
        {
            "asset_id": "art-1",
            "name": "Art Collection",
            "value_eur": 75000,
            "insured": False,
            "premium_eur": 0,
        },
        {
            "asset_id": "watch-1",
            "name": "Watch",
            "value_eur": 10000,
            "insured": True,
            "premium_eur": 150,
            "coverage_limit_eur": 6000,
        },
    ]
    claims = [
        {"claim_id": "c1", "status": "open"},
        {"claim_id": "c2", "status": "closed"},
        {"claim_id": "c3", "status": "open"},
    ]

    summary = summarize_insurance_status(assets, claims)

    assert summary["insured_asset_value_eur"] == 510000.0
    assert summary["uninsured_asset_value_eur"] == 75000.0
    assert summary["premium_total_eur"] == 1350.0
    assert summary["open_claims_count"] == 2
    assert summary["auto_policy_actions"] == []

    assert summary["coverage_gaps"] == [
        {
            "asset_id": "art-1",
            "name": "Art Collection",
            "reason": "uninsured",
            "value_eur": 75000.0,
        },
        {
            "asset_id": "watch-1",
            "name": "Watch",
            "reason": "underinsured",
            "value_eur": 10000.0,
        },
    ]


def test_evaluate_asset_marks_underinsurance():
    asset = evaluate_asset(
        {
            "asset_id": "car-1",
            "name": "Car",
            "value_eur": 20000,
            "insured": True,
            "premium_eur": 500,
            "coverage_limit_eur": 15000,
        }
    )

    assert asset.insured is True
    assert asset.has_gap is True
    assert asset.gap_reason == "underinsured"
    assert asset.premium_eur == 500.0

