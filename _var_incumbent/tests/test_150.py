import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

m150 = importlib.import_module("150")
summarize_insurance_status = m150.summarize_insurance_status


def test_summarize_insurance_status_tracks_values_premiums_claims_and_gaps():
    assets = [
        {
            "name": "Family Home",
            "value_eur": 500000,
            "insured_value_eur": 500000,
            "premium_eur": 1200,
            "coverage_required": True,
        },
        {
            "name": "Art Collection",
            "value_eur": 100000,
            "insured_value_eur": 25000,
            "premium_eur": 300,
            "coverage_required": True,
        },
        {
            "name": "Cash Reserve",
            "value_eur": 20000,
            "insured_value_eur": 0,
            "premium_eur": 0,
            "coverage_required": False,
        },
    ]
    claims = [
        {"status": "open"},
        {"status": "OPEN"},
        {"status": "closed"},
    ]

    result = summarize_insurance_status(assets, claims)

    assert result["insured_asset_value_eur"] == 525000.0
    assert result["uninsured_asset_value_eur"] == 95000.0
    assert result["premium_total_eur"] == 1500.0
    assert result["open_claims_count"] == 2
    assert result["auto_policy_actions"] == []

    assert result["coverage_gaps"] == [
        {"asset": "Art Collection", "uninsured_value_eur": 75000.0}
    ]

    assert result["assets"][0]["has_coverage_gap"] is False
    assert result["assets"][1]["has_coverage_gap"] is True
    assert result["assets"][2]["has_coverage_gap"] is False


def test_negative_values_are_rejected():
    try:
        summarize_insurance_status(
            [{"name": "Bad Asset", "value_eur": -1, "insured_value_eur": 0}]
        )
    except ValueError as exc:
        assert "value_eur must be >= 0" in str(exc)
    else:
        raise AssertionError("Expected ValueError for negative asset value")

