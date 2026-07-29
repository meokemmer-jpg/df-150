import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

insurance = importlib.import_module("150")
analyze_insurance_coverage = insurance.analyze_insurance_coverage


def test_analyze_insurance_coverage_tracks_totals_and_gaps():
    result = analyze_insurance_coverage(
        assets=[
            {
                "asset_id": "home-1",
                "name": "Family Home",
                "value_eur": 500000,
                "required_coverages": ["fire", "flood"],
            },
            {
                "asset_id": "art-1",
                "name": "Art Collection",
                "value_eur": 100000,
                "required_coverages": ["theft"],
            },
            {
                "asset_id": "boat-1",
                "name": "Sailboat",
                "value_eur": 80000,
                "required_coverages": ["storm"],
            },
        ],
        policies=[
            {
                "policy_id": "pol-home",
                "asset_id": "home-1",
                "covered_value_eur": 500000,
                "premium_eur": 1200,
                "status": "active",
                "coverages": ["fire", "flood"],
            },
            {
                "policy_id": "pol-art",
                "asset_id": "art-1",
                "covered_value_eur": 60000,
                "premium_eur": 500,
                "status": "active",
                "coverages": [],
            },
            {
                "policy_id": "pol-boat-old",
                "asset_id": "boat-1",
                "covered_value_eur": 80000,
                "premium_eur": 300,
                "status": "cancelled",
                "coverages": ["storm"],
            },
        ],
        claims=[
            {"claim_id": "cl-1", "asset_id": "home-1", "status": "closed"},
            {"claim_id": "cl-2", "asset_id": "art-1", "status": "open"},
            {"claim_id": "cl-3", "asset_id": "boat-1", "status": "open"},
        ],
    )

    assert result["insured_value_eur"] == 560000
    assert result["uninsured_value_eur"] == 120000
    assert result["premium_total_eur"] == 1700
    assert result["open_claims_count"] == 2
    assert sorted(result["coverage_gaps"]) == ["art-1", "boat-1"]

    by_asset = {row["asset_id"]: row for row in result["assets"]}

    assert by_asset["home-1"]["is_fully_insured"] is True
    assert by_asset["home-1"]["coverage_gaps"] == []

    assert by_asset["art-1"]["insured_value_eur"] == 60000
    assert by_asset["art-1"]["uninsured_value_eur"] == 40000
    assert by_asset["art-1"]["open_claims_count"] == 1
    assert by_asset["art-1"]["coverage_gaps"] == ["underinsured_value", "missing_required_coverages"]
    assert by_asset["art-1"]["missing_coverages"] == ["theft"]

    assert by_asset["boat-1"]["insured_value_eur"] == 0
    assert by_asset["boat-1"]["uninsured_value_eur"] == 80000
    assert by_asset["boat-1"]["coverage_gaps"] == ["no_active_policy", "underinsured_value", "missing_required_coverages"]
    assert by_asset["boat-1"]["missing_coverages"] == ["storm"]

