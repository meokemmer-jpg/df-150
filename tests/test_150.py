import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

# `from 150 import ...` is not valid Python syntax because module names in import
# statements must be identifiers. Load `150.py` via importlib instead.
m150 = importlib.import_module("150")
summarize_insurance_status = m150.summarize_insurance_status


def test_summarize_insurance_status_tracks_values_claims_and_gaps():
    assets = [
        {
            "asset_id": "house-1",
            "name": "Family House",
            "value_eur": 500000,
            "insured": True,
            "premium_eur": 1200,
            "coverage_required": True,
        },
        {
            "asset_id": "car-1",
            "name": "Car",
            "value_eur": 30000,
            "insured": False,
            "premium_eur": 0,
            "coverage_required": True,
        },
        {
            "asset_id": "art-1",
            "name": "Artwork",
            "value_eur": 20000,
            "insured": False,
            "premium_eur": 0,
            "coverage_required": False,
        },
    ]
    claims = [
        {"status": "open"},
        {"status": "closed"},
        {"status": "pending"},
    ]

    result = summarize_insurance_status(assets, claims)

    assert result["insured_value_eur"] == 500000.0
    assert result["uninsured_value_eur"] == 50000.0
    assert result["premium_total_eur"] == 1200.0
    assert result["open_claims_count"] == 2
    assert result["coverage_gaps"] == [
        {
            "asset_id": "car-1",
            "name": "Car",
            "uninsured_value_eur": 30000.0,
            "reason": "required_asset_uninsured",
        }
    ]
