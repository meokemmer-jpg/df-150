import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib.util
from pathlib import Path

module_path = Path(__file__).resolve().parent / "150.py"
spec = importlib.util.spec_from_file_location("150", module_path)
module_150 = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(module_150)

summarize_portfolio_coverage = module_150.summarize_portfolio_coverage
evaluate_asset_insurance_status = module_150.evaluate_asset_insurance_status


def test_summarize_portfolio_coverage_tracks_values_claims_and_gaps():
    assets = [
        {
            "asset_id": "house-1",
            "name": "Family Home",
            "asset_value_eur": 500000,
            "insured_value_eur": 500000,
            "premium_eur": 1200,
            "policy_active": True,
        },
        {
            "asset_id": "art-1",
            "name": "Art Collection",
            "asset_value_eur": 100000,
            "insured_value_eur": 25000,
            "premium_eur": 300,
            "policy_active": True,
        },
        {
            "asset_id": "boat-1",
            "name": "Boat",
            "asset_value_eur": 40000,
            "insured_value_eur": 0,
            "premium_eur": 0,
            "policy_active": False,
        },
    ]
    claims = [
        {"claim_id": "c-1", "status": "open"},
        {"claim_id": "c-2", "status": "closed"},
        {"claim_id": "c-3", "status": "open"},
    ]

    summary = summarize_portfolio_coverage(assets, claims)

    assert summary["insured_asset_value_eur"] == 525000
    assert summary["uninsured_asset_value_eur"] == 115000
    assert summary["premium_total_eur"] == 1500
    assert summary["open_claims_count"] == 2
    assert summary["coverage_gaps"] == [
        {"asset_id": "art-1", "name": "Art Collection", "gap_eur": 75000.0},
        {"asset_id": "boat-1", "name": "Boat", "gap_eur": 40000.0},
    ]


def test_evaluate_asset_insurance_status_rejects_overinsured_asset():
    try:
        evaluate_asset_insurance_status(
            {
                "asset_id": "bad-1",
                "name": "Broken Input",
                "asset_value_eur": 1000,
                "insured_value_eur": 1500,
                "premium_eur": 50,
                "policy_active": True,
            }
        )
    except ValueError as exc:
        assert "insured_value_eur must not exceed asset_value_eur" in str(exc)
    else:
        raise AssertionError("ValueError was not raised")
