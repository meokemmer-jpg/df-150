import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# NOTE: `from 150 import ...` is not valid Python syntax because module names cannot start with digits.
# This import style is the runnable equivalent for a file named `150.py`.
from importlib import import_module

m150 = import_module("150")

Asset = m150.Asset
Claim = m150.Claim
asset_coverage_gap = m150.asset_coverage_gap
build_insurance_status_report = m150.build_insurance_status_report


def test_build_insurance_status_report_tracks_core_kpis():
    assets = [
        Asset(
            asset_id="house-1",
            asset_type="real_estate",
            value_eur=500_000,
            insured=True,
            covered_value_eur=500_000,
            premium_eur=1_200,
            claims=[Claim("c1", "open"), Claim("c2", "closed")],
        ),
        Asset(
            asset_id="art-1",
            asset_type="art",
            value_eur=100_000,
            insured=True,
            covered_value_eur=60_000,
            premium_eur=250,
            claims=[Claim("c3", "pending")],
        ),
        Asset(
            asset_id="watch-1",
            asset_type="luxury_watch",
            value_eur=20_000,
            insured=False,
            covered_value_eur=0,
            premium_eur=999,  # must not count when uninsured
            claims=[],
        ),
    ]

    report = build_insurance_status_report(assets)

    assert report["insured_value_total_eur"] == 560_000.00
    assert report["uninsured_value_total_eur"] == 60_000.00
    assert report["premium_total_eur"] == 1_450.00
    assert report["open_claims_count"] == 2
    assert report["policy_automation_permitted"] is False
    assert report["recommended_actions"] == []

    assert report["coverage_gaps"] == [
        {
            "asset_id": "art-1",
            "asset_type": "art",
            "gap_eur": 40_000.00,
            "required_coverage_eur": 100_000.00,
            "covered_value_eur": 60_000.00,
        },
        {
            "asset_id": "watch-1",
            "asset_type": "luxury_watch",
            "gap_eur": 20_000.00,
            "required_coverage_eur": 20_000.00,
            "covered_value_eur": 0.00,
        },
    ]


def test_asset_coverage_gap_uses_required_coverage_override():
    asset = Asset(
        asset_id="collector-car",
        asset_type="vehicle",
        value_eur=80_000,
        insured=True,
        covered_value_eur=50_000,
        premium_eur=400,
        required_coverage_eur=70_000,
    )

    assert asset_coverage_gap(asset) == 20_000.00
