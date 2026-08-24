import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

insurance_module = importlib.import_module("150")
build_insurance_report = insurance_module.build_insurance_report
evaluate_asset_coverage = insurance_module.evaluate_asset_coverage
report_to_json = insurance_module.report_to_json


def test_evaluate_asset_coverage_caps_and_detects_gap():
    result = evaluate_asset_coverage(
        {
            "asset_id": "A-1",
            "asset_name": "Family Home",
            "asset_value_eur": 500000,
            "insured_value_eur": 550000,
            "premium_eur": 1200.456,
            "open_claims_count": 1,
        }
    )

    assert result.asset_value_eur == 500000.0
    assert result.insured_value_eur == 500000.0
    assert result.coverage_gap_eur == 0.0
    assert result.insured is True
    assert result.premium_eur == 1200.46
    assert result.open_claims_count == 1


def test_build_insurance_report_aggregates_totals_and_gaps():
    report = build_insurance_report(
        [
            {
                "asset_id": "A-1",
                "asset_name": "Family Home",
                "asset_value_eur": 500000,
                "insured_value_eur": 500000,
                "premium_eur": 1200,
                "open_claims_count": 1,
            },
            {
                "asset_id": "A-2",
                "asset_name": "Art Collection",
                "asset_value_eur": 80000,
                "insured_value_eur": 30000,
                "premium_eur": 250,
                "open_claims_count": 0,
            },
            {
                "asset_id": "A-3",
                "asset_name": "Jewelry",
                "asset_value_eur": 20000,
                "insured_value_eur": 0,
                "premium_eur": 0,
                "open_claims_count": 2,
            },
        ],
        report_date="2026-08-23",
    )

    assert report["report_date"] == "2026-08-23"
    assert report["totals"] == {
        "asset_value_eur": 600000.0,
        "insured_value_eur": 530000.0,
        "uninsured_value_eur": 70000.0,
        "premium_total_eur": 1450.0,
        "open_claims_count": 3,
    }
    assert report["coverage_gaps"] == [
        {"asset_id": "A-2", "asset_name": "Art Collection", "gap_eur": 50000.0},
        {"asset_id": "A-3", "asset_name": "Jewelry", "gap_eur": 20000.0},
    ]
    assert report["policy_actions"] == {
        "auto_policy_buy": False,
        "auto_policy_cancel": False,
    }

    payload = report_to_json(report)
    assert '"report_date": "2026-08-23"' in payload
    assert '"auto_policy_buy": false' in payload

