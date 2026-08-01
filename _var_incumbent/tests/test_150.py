import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

m150 = importlib.import_module("150")
build_insurance_report = m150.build_insurance_report
evaluate_asset = m150.evaluate_asset
write_report = m150.write_report


def test_build_insurance_report_tracks_totals_gaps_and_open_claims(tmp_path):
    assets = [
        {
            "asset_id": "home-main",
            "asset_value_eur": 500000,
            "insured_value_eur": 500000,
            "premium_eur": 1200,
        },
        {
            "asset_id": "art-collection",
            "asset_value_eur": 150000,
            "insured_value_eur": 50000,
            "premium_eur": 300,
        },
        {
            "asset_id": "jewelry",
            "asset_value_eur": 20000,
            "insured_value_eur": 0,
            "premium_eur": 0,
        },
    ]
    claims = [
        {"claim_id": "c1", "status": "open"},
        {"claim_id": "c2", "status": "closed"},
        {"claim_id": "c3", "status": "open"},
    ]

    report = build_insurance_report(assets, claims)

    assert report["insured_asset_value_eur"] == 550000.0
    assert report["uninsured_asset_value_eur"] == 120000.0
    assert report["premium_total_eur"] == 1500.0
    assert report["open_claims_count"] == 2
    assert report["auto_policy_actions"] == []
    assert report["coverage_gaps"] == [
        {"asset_id": "art-collection", "gap_value_eur": 100000.0},
        {"asset_id": "jewelry", "gap_value_eur": 20000.0},
    ]

    path = write_report(assets, claims, output_dir=tmp_path, report_date=__import__("datetime").date(2026, 8, 1))
    assert path.name == "df-150-2026-08-01.json"
    assert path.exists()


def test_evaluate_asset_rejects_overinsured_asset():
    try:
        evaluate_asset(
            {
                "asset_id": "bad-asset",
                "asset_value_eur": 1000,
                "insured_value_eur": 1001,
                "premium_eur": 10,
            }
        )
    except ValueError as exc:
        assert "cannot exceed" in str(exc)
    else:
        raise AssertionError("Expected ValueError for overinsured asset")

