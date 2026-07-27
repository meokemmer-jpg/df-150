import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

coverage = importlib.import_module("150")
build_coverage_report = coverage.build_coverage_report


def test_build_coverage_report_tracks_totals_claims_and_gaps():
    assets = [
        {
            "asset_id": "house",
            "value_eur": 500000,
            "insured_value_eur": 500000,
            "premium_eur": 1200,
        },
        {
            "asset_id": "art",
            "value_eur": 80000,
            "insured_value_eur": 30000,
            "premium_eur": 250,
        },
        {
            "asset_id": "boat",
            "value_eur": 40000,
            "insured_value_eur": 0,
            "premium_eur": 0,
        },
    ]
    claims = [
        {"claim_id": "c1", "status": "open"},
        {"claim_id": "c2", "status": "closed"},
        {"claim_id": "c3", "status": "OPEN"},
    ]

    report = build_coverage_report(assets, claims)

    assert report["total_asset_value_eur"] == 620000.0
    assert report["insured_asset_value_eur"] == 530000.0
    assert report["uninsured_asset_value_eur"] == 90000.0
    assert report["premium_total_eur"] == 1450.0
    assert report["open_claims_count"] == 2
    assert report["fully_insured"] is False
    assert report["coverage_gaps"] == [
        {
            "asset_id": "art",
            "asset_value_eur": 80000.0,
            "insured_value_eur": 30000.0,
            "gap_value_eur": 50000.0,
            "status": "underinsured",
        },
        {
            "asset_id": "boat",
            "asset_value_eur": 40000.0,
            "insured_value_eur": 0.0,
            "gap_value_eur": 40000.0,
            "status": "uninsured",
        },
    ]


def test_build_coverage_report_rejects_negative_values():
    try:
        build_coverage_report([{"asset_id": "x", "value_eur": -1}])
    except ValueError as exc:
        assert str(exc) == "value_eur must be non-negative"
    else:
        raise AssertionError("ValueError was not raised for a negative asset value")

