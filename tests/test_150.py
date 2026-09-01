import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

m150 = importlib.import_module("150")
Asset = m150.Asset
Claim = m150.Claim
evaluate_insurance_status = m150.evaluate_insurance_status


def test_evaluate_insurance_status_tracks_core_kpis_and_gaps():
    assets = [
        Asset(name="Haus", value_eur=500000, insured=True, premium_eur=1200),
        Asset(name="Depot", value_eur=150000, insured=False, premium_eur=0),
        Asset(name="Schmuck", value_eur=20000, insured=False, premium_eur=0, coverage_required=False),
        Asset(name="Auto", value_eur=30000, insured=True, premium_eur=800),
    ]
    claims = [
        Claim(asset_name="Haus", status="open"),
        Claim(asset_name="Auto", status="closed"),
        Claim(asset_name="Depot", status="OPEN"),
    ]

    result = evaluate_insurance_status(assets, claims)

    assert result["insured_value_eur"] == 530000.0
    assert result["uninsured_value_eur"] == 170000.0
    assert result["premium_total_eur"] == 2000.0
    assert result["open_claims_count"] == 2
    assert result["policy_actions"] == []

    assert result["coverage_gaps"] == [
        {
            "asset_name": "Depot",
            "gap_type": "missing_coverage",
            "uninsured_value_eur": 150000.0,
        }
    ]
