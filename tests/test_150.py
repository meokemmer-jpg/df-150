import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# from 150 import evaluate_insurance_status
import importlib

evaluate_insurance_status = importlib.import_module("150").evaluate_insurance_status


def test_evaluate_insurance_status_tracks_values_claims_and_gaps():
    assets = [
        {
            "asset_id": "house-1",
            "name": "Family House",
            "value_eur": 500000,
            "insured": True,
            "policy_active": True,
            "insured_value_eur": 500000,
            "coverage_required_eur": 500000,
            "premium_eur": 1200,
        },
        {
            "asset_id": "art-1",
            "name": "Art Collection",
            "value_eur": 100000,
            "insured": True,
            "policy_active": True,
            "insured_value_eur": 60000,
            "coverage_required_eur": 100000,
            "premium_eur": 300,
        },
        {
            "asset_id": "boat-1",
            "name": "Boat",
            "value_eur": 40000,
            "insured": False,
            "coverage_required_eur": 40000,
            "premium_eur": 0,
        },
    ]
    claims = [
        {"claim_id": "c1", "status": "open"},
        {"claim_id": "c2", "status": "closed"},
        {"claim_id": "c3", "status": "OPEN"},
    ]

    result = evaluate_insurance_status(assets, claims)

    assert result["insured_asset_value_eur"] == 600000.0
    assert result["uninsured_asset_value_eur"] == 40000.0
    assert result["premium_total_eur"] == 1500.0
    assert result["open_claims_count"] == 2
    assert result["auto_policy_actions"] == []

    by_id = {asset["asset_id"]: asset for asset in result["assets"]}

    assert by_id["house-1"]["status"] == "insured"
    assert by_id["house-1"]["coverage_gap_eur"] == 0.0
    assert by_id["house-1"]["auto_policy_action"] is None

    assert by_id["art-1"]["status"] == "underinsured"
    assert by_id["art-1"]["coverage_gap_eur"] == 40000.0

    assert by_id["boat-1"]["status"] == "uninsured"
    assert by_id["boat-1"]["coverage_gap_eur"] == 40000.0

    assert result["coverage_gaps"] == [
        {
            "asset_id": "art-1",
            "name": "Art Collection",
            "gap_eur": 40000.0,
            "reason": "underinsured",
        },
        {
            "asset_id": "boat-1",
            "name": "Boat",
            "gap_eur": 40000.0,
            "reason": "uninsured",
        },
    ]
