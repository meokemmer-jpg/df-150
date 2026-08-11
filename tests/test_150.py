import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# from 150 import make_asset, assess_asset, compute_insurance_status, write_report, stop_requested, auto_policy_buy, auto_policy_cancel, AutoPolicyForbidden
# ACHTUNG: `from 150 import ...` ist in Python syntaktisch ungueltig (Modulname
# beginnt mit einer Ziffer -> SyntaxError). Der funktional identische Import
# erfolgt daher via importlib - so bleibt der Test echt gruen lauffaehig.
import importlib
import json
import os

import pytest

_m = importlib.import_module("150")  # entspricht exakt: from 150 import ...

make_asset = _m.make_asset
assess_asset = _m.assess_asset
compute_insurance_status = _m.compute_insurance_status
write_report = _m.write_report
stop_requested = _m.stop_requested
auto_policy_buy = _m.auto_policy_buy
auto_policy_cancel = _m.auto_policy_cancel
AutoPolicyForbidden = _m.AutoPolicyForbidden


def _demo_assets():
    return [
        make_asset("A1", 100000.0, coverage_eur=100000.0, premium_eur=500.0, open_claims=1),
        make_asset("A2", 50000.0, coverage_eur=30000.0, premium_eur=200.0, open_claims=2),
        make_asset("A3", 25000.0),  # komplett unversichert
    ]


def test_assess_asset_statuses():
    assert assess_asset(make_asset("X", 100.0, coverage_eur=100.0))["status"] == "insured"
    assert assess_asset(make_asset("X", 100.0, coverage_eur=40.0))["status"] == "underinsured"
    assert assess_asset(make_asset("X", 100.0))["status"] == "uninsured"
    over = assess_asset(make_asset("X", 100.0, coverage_eur=150.0))
    assert over["status"] == "insured"
    assert over["uninsured_value_eur"] == 0.0
    assert over["overinsured_eur"] == 50.0


def test_compute_insurance_status_totals():
    s = compute_insurance_status(_demo_assets())
    assert s["module"] == "df-150"
    assert s["asset_count"] == 3
    assert s["total_asset_value_eur"] == 175000.0
    assert s["insured_value_eur"] == 130000.0
    assert s["uninsured_value_eur"] == 45000.0
    # Invariante: insured + uninsured == total
    assert s["insured_value_eur"] + s["uninsured_value_eur"] == s["total_asset_value_eur"]
    assert s["premium_total_eur"] == 700.0
    assert s["open_claims_count"] == 3
    assert s["coverage_ratio"] == pytest.approx(130000.0 / 175000.0, abs=1e-4)
    assert s["coverage_gap_count"] == 2
    gaps = {g["asset_id"]: g["gap_eur"] for g in s["coverage_gaps"]}
    assert gaps == {"A2": 20000.0, "A3": 25000.0}
    assert s["auto_policy_ops"] == "forbidden"


def test_empty_portfolio_is_consistent():
    s = compute_insurance_status([])
    assert s["asset_count"] == 0
    assert s["total_asset_value_eur"] == 0.0
    assert s["premium_total_eur"] == 0.0
    assert s["open_claims_count"] == 0
    assert s["coverage_ratio"] == 1.0
    assert s["coverage_gaps"] == []


def test_make_asset_validation():
    with pytest.raises(ValueError):
        make_asset("BAD", -1.0)
    with pytest.raises(ValueError):
        make_asset("BAD", 10.0, coverage_eur=-5.0)
    with pytest.raises(ValueError):
        make_asset("BAD", 10.0, premium_eur=-0.01)
    with pytest.raises(ValueError):
        make_asset("BAD", 10.0, open_claims=-1)
    with pytest.raises(ValueError):
        make_asset("BAD", 10.0, open_claims=1.5)
    with pytest.raises(ValueError):
        make_asset("", 10.0)


def test_auto_policy_ops_sind_verboten():
    # Spec: NIEMALS Auto-Policy-Buy oder Auto-Policy-Cancel.
    with pytest.raises(AutoPolicyForbidden):
        auto_policy_buy("A1", 10000.0)
    with pytest.raises(AutoPolicyForbidden):
        auto_policy_cancel("POL-77")


def test_write_report_roundtrip(tmp_path):
    s = compute_insurance_status(_demo_assets())
    path = write_report(s, reports_dir=str(tmp_path), date="2025-01-02")
    assert os.path.basename(path) == "df-150-2025-01-02.json"
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["module"] == "df-150"
    assert data["uninsured_value_eur"] == 45000.0
    assert data["open_claims_count"] == 3
    assert data["coverage_gap_count"] == 2


def test_stop_flag(tmp_path):
    stop = tmp_path / "df-150.stop"
    assert stop_requested(str(stop)) is False
    stop.write_text("halt", encoding="utf-8")
    assert stop_requested(str(stop)) is True


def test_main_mock_run_und_stop(tmp_path):
    stop = tmp_path / "df-150.stop"
    path = _m.main(reports_dir=str(tmp_path / "reports"), stop_path=str(stop))
    assert path is not None and os.path.exists(path)
    stop.write_text("x", encoding="utf-8")
    assert _m.main(reports_dir=str(tmp_path / "reports2"), stop_path=str(stop)) is None
