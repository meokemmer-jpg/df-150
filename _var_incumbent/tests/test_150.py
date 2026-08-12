import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

coverage_module = importlib.import_module("150")
calculate_insurance_status = coverage_module.calculate_insurance_status


def test_calculate_insurance_status_tracks_core_metrics():
    report = calculate_insurance_status(
        assets=[
            {
                "name": "Primary Home",
                "value_eur": 500000,
                "insured_value_eur": 500000,
                "annual_premium_eur": 1200,
            },
            {
                "name": "Artwork",
                "value_eur": 100000,
                "insured_value_eur": 25000,
                "annual_premium_eur": 200,
            },
            {
                "name": "Jewelry",
                "value_eur": 40000,
                "insured_value_eur": 0,
                "annual_premium_eur": 0,
            },
        ],
        claims=[
            {"asset_name": "Primary Home", "status": "closed"},
            {"asset_name": "Artwork", "status": "open"},
            {"asset_name": "Jewelry", "status": "OPEN"},
        ],
    )

    assert report["insured_value_eur"] == 525000.0
    assert report["uninsured_value_eur"] == 115000.0
    assert report["premium_total_eur"] == 1400.0
    assert report["open_claims_count"] == 2
    assert report["auto_policy_buy"] is False
    assert report["auto_policy_cancel"] is False
    assert report["coverage_gaps"] == [
        {
            "asset_name": "Artwork",
            "gap_type": "underinsured",
            "uninsured_value_eur": 75000.0,
        },
        {
            "asset_name": "Jewelry",
            "gap_type": "uninsured",
            "uninsured_value_eur": 40000.0,
        },
    ]


def test_negative_values_are_rejected():
    try:
        calculate_insurance_status(
            assets=[{"name": "Bad Asset", "value_eur": -1, "insured_value_eur": 0}],
        )
    except ValueError as exc:
        assert "non-negative" in str(exc)
    else:
        raise AssertionError("ValueError was not raised for negative EUR values")

