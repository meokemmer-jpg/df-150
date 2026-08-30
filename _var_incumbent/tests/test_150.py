import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
"""pytest suite for df-150 (module file: 150.py).

NOTE on the required `from 150 import ...`: that statement is a SyntaxError
in Python — module names are identifiers and may not start with a digit.
`importlib.import_module("150")` performs exactly that import; the name
bindings below are the literal equivalents of `from 150 import <name>`.
"""

import json
from datetime import date
from importlib import import_module

import pytest

_150 = import_module("150")  # imports module "150" (file 150.py)

Asset = _150.Asset
AssetAssessment = _150.AssetAssessment
AutoPolicyActionForbidden = _150.AutoPolicyActionForbidden
assess_asset = _150.assess_asset
assert_no_auto_policy_actions = _150.assert_no_auto_policy_actions
build_coverage_report = _150.build_coverage_report
run_engine = _150.run_engine
stop_requested = _150.stop_requested

FIXED_DAY = date(2025, 1, 15)


def _portfolio():
    return [
        Asset("house", 100_000.0, insured_value_eur=60_000.0, premium_eur=1_200.0, open_claims=2),
        Asset("depot", 50_000.0, insured_value_eur=50_000.0, premium_eur=0.0, open_claims=0),
        Asset("car", 20_000.0, insured_value_eur=0.0, premium_eur=300.0, open_claims=1),
    ]


def test_assess_asset_splits_insured_and_uninsured():
    a = assess_asset(Asset("house", 100_000.0, 60_000.0, 1_200.0, 2))
    assert isinstance(a, AssetAssessment)
    assert a.insured_value_eur == 60_000.0
    assert a.uninsured_value_eur == 40_000.0
    assert a.coverage_ratio == 0.6
    assert a.has_coverage_gap is True
    assert a.open_claims == 2


def test_assess_fully_insured_has_no_gap():
    a = assess_asset(Asset("depot", 50_000.0, 50_000.0))
    assert a.uninsured_value_eur == 0.0
    assert a.coverage_ratio == 1.0
    assert a.has_coverage_gap is False


def test_asset_validation_rejects_bad_values():
    with pytest.raises(ValueError):
        Asset("bad", -1.0)
    with pytest.raises(ValueError):
        Asset("bad", 10.0, insured_value_eur=-5.0)
    with pytest.raises(ValueError):
        Asset("bad", 10.0, premium_eur=-0.01)
    with pytest.raises(ValueError):
        Asset("bad", 10.0, open_claims=-1)
    with pytest.raises(ValueError):
        Asset("", 10.0)


def test_build_coverage_report_totals_and_gaps():
    report = build_coverage_report(_portfolio(), report_date=FIXED_DAY)
    assert report["module"] == "df-150"
    assert report["domain"] == "K_0"
    assert report["date"] == "2025-01-15"
    assert report["asset_count"] == 3
    assert report["total_value_eur"] == 170_000.0
    assert report["insured_value_eur"] == 110_000.0
    assert report["uninsured_value_eur"] == 60_000.0
    assert report["premium_total_eur"] == 1_500.0
    assert report["open_claims_count"] == 3
    assert report["coverage_gaps"] == ["house", "car"]
    assert report["coverage_gap_count"] == 2
    assert report["coverage_ratio"] == round(110_000.0 / 170_000.0, 4)
    assert report["auto_policy_buy"] == "DISABLED"
    assert report["auto_policy_cancel"] == "DISABLED"


def test_build_coverage_report_accepts_plain_dicts():
    report = build_coverage_report(
        [{"asset_id": "x", "value_eur": 10.0}], report_date=FIXED_DAY
    )
    assert report["uninsured_value_eur"] == 10.0
    assert report["coverage_gaps"] == ["x"]


def test_empty_portfolio_is_fully_covered():
    report = build_coverage_report([], report_date=FIXED_DAY)
    assert report["total_value_eur"] == 0.0
    assert report["coverage_ratio"] == 1.0
    assert report["coverage_gaps"] == []
    assert report["open_claims_count"] == 0


def test_run_engine_writes_json_report(tmp_path):
    result = run_engine(
        _portfolio(),
        reports_dir=tmp_path,
        stop_path=tmp_path / "df-150.stop",
        report_date=FIXED_DAY,
    )
    assert result["status"] == "OK"
    assert result["mode"] == "mock"
    path = tmp_path / "df-150-2025-01-15.json"
    assert result["report_path"] == str(path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["total_value_eur"] == 170_000.0
    assert data["uninsured_value_eur"] == 60_000.0
    assert data["premium_total_eur"] == 1_500.0
    assert data["coverage_gaps"] == ["house", "car"]


def test_stop_flag_halts_engine_and_writes_nothing(tmp_path):
    flag = tmp_path / "df-150.stop"
    flag.write_text("halt", encoding="utf-8")
    result = run_engine(
        _portfolio(),
        reports_dir=tmp_path,
        stop_path=flag,
        report_date=FIXED_DAY,
    )
    assert result["status"] == "STOPPED"
    assert result["report"] is None
    assert result["report_path"] is None
    assert not (tmp_path / "df-150-2025-01-15.json").exists()


def test_stop_requested(tmp_path):
    flag = tmp_path / "df-150.stop"
    assert stop_requested(flag) is False
    flag.write_text("x", encoding="utf-8")
    assert stop_requested(flag) is True


def test_auto_policy_buy_and_cancel_are_never_executed():
    with pytest.raises(AutoPolicyActionForbidden):
        assert_no_auto_policy_actions(["auto_buy"])
    with pytest.raises(AutoPolicyActionForbidden):
        assert_no_auto_policy_actions(["review", "cancel"])
    with pytest.raises(AutoPolicyActionForbidden):
        assert_no_auto_policy_actions(["AUTO-CANCEL"])
    assert assert_no_auto_policy_actions(["review", "alert"]) is True


def test_report_is_json_serializable():
    report = build_coverage_report(_portfolio(), report_date=FIXED_DAY)
    assert json.loads(json.dumps(report))["open_claims_count"] == 3

