import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib
import json

m150 = importlib.import_module("150")
calculate_insurance_status = m150.calculate_insurance_status
build_report = m150.build_report
write_report = m150.write_report


def test_kpm_insurance_status_and_report_output(tmp_path):
    assets = [
        {
            "name": "Primary Residence",
            "value_eur": 100000,
            "insured_value_eur": 80000,
            "premium_eur": 500,
            "open_claims_count": 1,
            "coverage_required": True,
        },
        {
            "name": "Art Collection",
            "value_eur": 40000,
            "insured_value_eur": 0,
            "premium_eur": 0,
            "open_claims_count": 0,
            "coverage_required": True,
        },
        {
            "name": "Family Car",
            "value_eur": 25000,
            "insured_value_eur": 25000,
            "premium_eur": 900,
            "open_claims_count": 2,
            "coverage_required": True,
        },
    ]

    status = calculate_insurance_status(assets)

    assert status["insured_asset_value_eur"] == 105000.0
    assert status["uninsured_asset_value_eur"] == 60000.0
    assert status["premium_total_eur"] == 1400.0
    assert status["open_claims_count"] == 3
    assert len(status["coverage_gaps"]) == 2
    assert status["coverage_gaps"][0]["asset"] == "Primary Residence"
    assert status["coverage_gaps"][0]["reason"] == "underinsured"
    assert status["coverage_gaps"][0]["gap_value_eur"] == 20000.0
    assert status["coverage_gaps"][1]["asset"] == "Art Collection"
    assert status["coverage_gaps"][1]["reason"] == "uninsured"
    assert status["coverage_gaps"][1]["gap_value_eur"] == 40000.0

    report = build_report(assets, report_date="2026-08-22", stop_flag_path=tmp_path / "df-150.stop")
    assert report["report_date"] == "2026-08-22"
    assert report["stop_requested"] is False

    written = write_report(
        assets,
        report_dir=tmp_path / "reports",
        report_date="2026-08-22",
        stop_flag_path=tmp_path / "df-150.stop",
    )
    assert written.name == "df-150-2026-08-22.json"

    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload == report
