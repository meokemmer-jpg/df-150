import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# Because module filename "150" starts with a digit, normal import syntax is invalid.
# Use importlib to load the module.
import importlib

m = importlib.import_module("150")
track_insurance_status = m.track_insurance_status
coverage_gap_for_asset = m.coverage_gap_for_asset


def test_track_insurance_status_aggregates():
    assets = [
        {
            "id": "A1",
            "value_eur": 100_000,
            "insured": True,
            "premium_eur": 500,
            "claims_open": 1,
            "insured_value_eur": 100_000,
        },
        {
            "id": "A2",
            "value_eur": 50_000,
            "insured": False,
            "premium_eur": 0,
            "claims_open": 0,
            "insured_value_eur": 0,
        },
        {
            "id": "A3",
            "value_eur": 200_000,
            "insured": True,
            "premium_eur": 1200,
            "claims_open": 2,
            "insured_value_eur": 150_000,  # underinsured
        },
    ]

    result = track_insurance_status(assets)

    assert result["insured_value_eur"] == 300_000.0
    assert result["uninsured_value_eur"] == 50_000.0
    assert result["total_premium_eur"] == 1700.0
    assert result["open_claims_count"] == 3

    assert len(result["coverage_gaps"]) == 2
    assert result["coverage_gaps"][0] == {"asset_id": "A2", "gap_eur": 50_000.0}
    assert result["coverage_gaps"][1] == {"asset_id": "A3", "gap_eur": 50_000.0}
    assert result["total_coverage_gap_eur"] == 100_000.0


def test_track_insurance_status_empty_list():
    result = track_insurance_status([])
    assert result == {
        "insured_value_eur": 0.0,
        "uninsured_value_eur": 0.0,
        "total_premium_eur": 0.0,
        "open_claims_count": 0,
        "coverage_gaps": [],
        "total_coverage_gap_eur": 0.0,
    }


def test_track_insurance_status_does_not_mutate_assets():
    assets = [
        {
            "id": "A1",
            "value_eur": 100_000,
            "insured": True,
            "premium_eur": 500,
            "claims_open": 1,
            "insured_value_eur": 100_000,
        },
        {
            "id": "A2",
            "value_eur": 50_000,
            "insured": False,
            "premium_eur": 0,
            "claims_open": 0,
            "insured_value_eur": 0,
        },
    ]
    assets_snapshot = [dict(a) for a in assets]

    track_insurance_status(assets)

    assert assets == assets_snapshot


def test_coverage_gap_for_asset_full_cover_no_gap():
    asset = {"id": "B1", "value_eur": 10_000, "insured": True, "insured_value_eur": 10_000}
    assert coverage_gap_for_asset(asset) == 0.0


def test_coverage_gap_for_asset_uninsured_equals_value():
    asset = {"id": "B2", "value_eur": 25_000, "insured": False}
    assert coverage_gap_for_asset(asset) == 25_000.0


def test_coverage_gap_for_asset_underinsured_returns_difference():
    asset = {"id": "B3", "value_eur": 40_000, "insured": True, "insured_value_eur": 25_000}
    assert coverage_gap_for_asset(asset) == 15_000.0

