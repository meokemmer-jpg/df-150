import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

coverage_mod = importlib.import_module("150")
analyze_insurance_coverage = coverage_mod.analyze_insurance_coverage
build_report_filename = coverage_mod.build_report_filename


def test_analyze_insurance_coverage_computes_core_metrics_and_gaps():
    assets = [
        {
            "asset_id": "home-1",
            "name": "Family Home",
            "value_eur": 500000,
            "insured": True,
            "premium_eur": 1200,
        },
        {
            "asset_id": "art-1",
            "name": "Artwork",
            "value_eur": 25000,
            "insured": False,
            "premium_eur": 0,
        },
        {
            "asset_id": "boat-1",
            "name": "Boat",
            "value_eur": 15000,
            "insured": True,
            "premium_eur": 300,
            "coverage_gap": "storm damage rider missing",
        },
    ]
    claims = [
        {"claim_id": "c-1", "status": "open"},
        {"claim_id": "c-2", "status": "closed"},
        {"claim_id": "c-3", "status": "OPEN"},
    ]

    report = analyze_insurance_coverage(assets, claims=claims)

    assert report["insured_asset_value_eur"] == 515000.0
    assert report["uninsured_asset_value_eur"] == 25000.0
    assert report["premium_total_eur"] == 1500.0
    assert report["open_claims_count"] == 2
    assert report["auto_policy_actions"] == []
    assert report["coverage_gaps"] == [
        {
            "asset_id": "art-1",
            "name": "Artwork",
            "reason": "asset has value but is not insured",
        },
        {
            "asset_id": "boat-1",
            "name": "Boat",
            "reason": "storm damage rider missing",
        },
    ]


def test_build_report_filename_uses_df_150_convention():
    assert build_report_filename().startswith("reports/df-150-")
    assert build_report_filename().endswith(".json")


def test_negative_asset_value_is_rejected():
    assets = [
        {
            "asset_id": "bad-1",
            "name": "Broken Input",
            "value_eur": -1,
            "insured": False,
            "premium_eur": 0,
        }
    ]

    try:
        analyze_insurance_coverage(assets)
    except ValueError as exc:
        assert "value_eur must be non-negative" in str(exc)
    else:
        raise AssertionError("Expected ValueError for negative asset value")
