import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
from importlib import import_module

m150 = import_module("150")
build_report = m150.build_report
evaluate_asset = m150.evaluate_asset


def test_evaluate_asset_and_build_report():
    assets = [
        {"asset_id": "villa", "category": "real_estate", "value_eur": 750000},
        {"asset_id": "watch", "category": "luxury_goods", "value_eur": 40000},
        {"asset_id": "boat", "category": "vehicles", "value_eur": 90000},
    ]
    policies = [
        {"policy_id": "pol-1", "asset_id": "villa", "coverage_eur": 750000, "premium_eur": 2500, "active": True},
        {"policy_id": "pol-2", "asset_id": "watch", "coverage_eur": 10000, "premium_eur": 150, "active": True},
        {"policy_id": "pol-3", "asset_id": "boat", "coverage_eur": 20000, "premium_eur": 300, "active": False},
    ]
    claims = [
        {"claim_id": "cl-1", "asset_id": "villa", "status": "open"},
        {"claim_id": "cl-2", "asset_id": "villa", "status": "closed"},
        {"claim_id": "cl-3", "asset_id": "watch", "status": "open"},
    ]

    watch_status = evaluate_asset(assets[1], policies, claims)
    assert watch_status.insured_value_eur == 10000.0
    assert watch_status.uninsured_value_eur == 30000.0
    assert watch_status.premium_eur == 150.0
    assert watch_status.open_claims_count == 1
    assert watch_status.coverage_gap is True

    report = build_report(assets, policies, claims)
    assert report["insured_value_eur"] == 760000.0
    assert report["uninsured_value_eur"] == 120000.0
    assert report["premium_total_eur"] == 2650.0
    assert report["open_claims_count"] == 2
    assert report["coverage_gaps"]["count"] == 2
    assert report["coverage_gaps"]["asset_ids"] == ["watch", "boat"]
    assert report["coverage_gaps"]["by_category_eur"] == {
        "luxury_goods": 30000.0,
        "vehicles": 90000.0,
    }
    assert report["auto_policy_actions"] == []
