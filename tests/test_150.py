import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
for _P in (_HERE, os.path.abspath(os.path.join(_HERE, os.pardir))):
    if _P not in sys.path:
        sys.path.insert(0, _P)

# Python grammar prevents literal `from 150 import ...`; importlib is the
# valid workaround for a numeric module filename like 150.py.
df150 = importlib.import_module("150")
DF150Tracker = df150.DF150Tracker
InsuranceError = df150.InsuranceError


def test_tracks_insured_uninsured_premium_and_claims():
    t = DF150Tracker()
    t.add_asset("A1", value_eur=10_000.0, insured_value_eur=7_500.0, premium_eur=120.0)
    t.add_asset("A2", value_eur=50_000.0, insured_value_eur=50_000.0, premium_eur=640.0)
    t.add_asset("A3", value_eur=20_000.0, insured_value_eur=0.0, premium_eur=0.0)

    assert t.total_asset_value() == 80_000.0
    assert t.insured_value_total() == 57_500.0
    assert t.uninsured_value_total() == 22_500.0
    assert t.premium_total() == 760.0
    assert t.open_claims_count() == 0

    gaps = t.coverage_gaps()
    assert {a.asset_id for a in gaps} == {"A1", "A3"}

    t.open_claim("A1")
    t.open_claim("A1")
    t.open_claim("A2")
    assert t.open_claims_count() == 3

    t.settle_claim("A1")
    assert t.open_claims_count() == 2
    assert t.get_asset("A1").open_claims == 1

    t.update_asset("A3", insured_value_eur=15_000.0, premium_eur=200.0)
    assert t.get_asset("A3").insured_value_eur == 15_000.0
    assert t.get_asset("A3").premium_eur == 200.0
    assert t.uninsured_value_total() == 7_500.0
    assert t.premium_total() == 960.0
    assert {a.asset_id for a in t.coverage_gaps()} == {"A1", "A3"}

    report = t.report()
    assert report["insured_total_eur"] == 72_500.0
    assert report["uninsured_total_eur"] == 7_500.0
    assert report["total_asset_value_eur"] == 80_000.0
    assert report["premium_total_eur"] == 960.0
    assert report["open_claims_count"] == 2
    assert report["coverage_gaps"] == ["A1", "A3"]
    assert len(report["assets"]) == 3


def test_invalid_operations_raise_and_do_not_autobuy():
    t = DF150Tracker()
    t.add_asset("B1", value_eur=30_000.0)
    t.update_asset("B1", insured_value_eur=10_000.0, premium_eur=99.0)
    assert t.get_asset("B1").insured_value_eur == 10_000.0

    with pytest.raises(InsuranceError):
        t.update_asset("B1", insured_value_eur=40_000.0)
    assert t.get_asset("B1").insured_value_eur == 10_000.0

    with pytest.raises(InsuranceError):
        t.open_claim("MISSING")

    with pytest.raises(InsuranceError):
        t.settle_claim("B1")

    with pytest.raises(InsuranceError):
        t.add_asset("B1", value_eur=100.0)


def test_write_report_json(tmp_path):
    t = DF150Tracker()
    t.add_asset("C1", value_eur=1_000.0, insured_value_eur=500.0, premium_eur=10.0)

    path = t.write_report(str(tmp_path / "report.json"))
    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    assert payload["insured_total_eur"] == 500.0
    assert payload["uninsured_total_eur"] == 500.0
    assert payload["premium_total_eur"] == 10.0
    assert payload["open_claims_count"] == 0
    assert payload["coverage_gaps"] == ["C1"]
    assert payload["assets"][0]["asset_id"] == "C1"
