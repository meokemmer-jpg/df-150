import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

m150 = importlib.import_module("150")
build_report = m150.build_report
evaluate_insurance_status = m150.evaluate_insurance_status
write_report = m150.write_report


def test_evaluate_insurance_status_and_report_write(tmp_path):
    assets = [
        {
            "asset_id": "house",
            "value_eur": "250000.00",
            "insured": True,
            "premium_eur": "1200.50",
            "coverage_required": True,
        },
        {
            "asset_id": "art",
            "value_eur": "10000.00",
            "insured": False,
            "premium_eur": "0.00",
            "coverage_required": True,
        },
        {
            "asset_id": "bike",
            "value_eur": "800.00",
            "insured": True,
            "premium_eur": "0.00",
            "coverage_required": True,
        },
    ]
    claims = [
        {"claim_id": "c1", "status": "open"},
        {"claim_id": "c2", "status": "closed"},
        {"claim_id": "c3", "status": "pending"},
    ]

    summary = evaluate_insurance_status(assets, claims)

    assert summary["insured_value_eur"] == 250800.0
    assert summary["uninsured_value_eur"] == 10000.0
    assert summary["premium_total_eur"] == 1200.5
    assert summary["open_claims_count"] == 2
    assert summary["auto_policy_actions"] == []
    assert summary["stop_flag_path"] == "/tmp/df-150.stop"
    assert summary["coverage_gaps"] == [
        {
            "asset_id": "art",
            "reason": "required_asset_uninsured",
            "value_eur": 10000.0,
        },
        {
            "asset_id": "bike",
            "reason": "insured_asset_missing_premium",
            "value_eur": 800.0,
        },
    ]

    report = build_report(assets, claims)
    assert report["factory"] == "df-150"
    assert report["domain"] == "K_0"
    assert report["report_date"]

    report_path = write_report(assets, claims, report_date=None, reports_dir=tmp_path)
    assert report_path.exists()
    assert report_path.name.startswith("df-150-")
    assert report_path.suffix == ".json"

