import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# `from 150 import ...` is invalid Python syntax because module names cannot start with a digit.
# For a real green pytest run against `150.py`, use importlib.
import importlib

mod = importlib.import_module("150")
calculate_insurance_status = mod.calculate_insurance_status


def test_calculate_insurance_status_tracks_core_kpm_metrics():
    assets = [
        {
            "asset_id": "house",
            "value_eur": 500000,
            "insured": True,
            "premium_eur": 1200,
            "coverage_limit_eur": 500000,
        },
        {
            "asset_id": "art",
            "value_eur": 75000,
            "insured": False,
            "premium_eur": 0,
        },
        {
            "asset_id": "boat",
            "value_eur": 90000,
            "insured": True,
            "premium_eur": 450,
            "coverage_limit_eur": 60000,
        },
        {
            "asset_id": "jewelry",
            "value_eur": 15000,
            "insured": True,
            "premium_eur": 80,
            "coverage_limit_eur": 15000,
            "excluded": True,
        },
    ]
    claims = [
        {"claim_id": "c1", "status": "open"},
        {"claim_id": "c2", "status": "closed"},
        {"claim_id": "c3", "status": "OPEN"},
    ]

    result = calculate_insurance_status(assets, claims)

    assert result["insured_value_eur"] == 605000.0
    assert result["uninsured_value_eur"] == 75000.0
    assert result["premium_total_eur"] == 1730.0
    assert result["open_claims_count"] == 2
    assert result["coverage_gaps"] == ["art", "boat", "jewelry"]


def test_negative_values_are_rejected():
    assets = [{"asset_id": "bad", "value_eur": -1, "insured": True, "premium_eur": 10}]

    import pytest

    with pytest.raises(ValueError):
        calculate_insurance_status(assets)

