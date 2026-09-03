import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# Crux note: "150.py" is a purely numeric module name, therefore the
# literal import form "from 150 import ..." is not legal Python syntax
# (identifiers may not start with a digit; it raises SyntaxError before
# any test runs). The runnable, canonical equivalent of
# "from 150 import ..." is importlib.import_module("150"); the names
# bound below are exactly the names the module exports for the tests.
import importlib
import json
import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_150 = importlib.import_module("150")

Asset = _150.Asset
track_assets = _150.track_assets
coverage_gaps = _150.coverage_gaps
build_report = _150.build_report
write_report = _150.write_report
stop_requested = _150.stop_requested
FORBIDDEN_ACTIONS = _150.FORBIDDEN_ACTIONS


def make_assets():
    return (
        Asset(
            "family-home",
            1_000_000.0,
            insured_value_eur=800_000.0,
            premium_eur=2_400.0,
            claims=({"status": "open"}, {"status": "closed"}),
        ),
        Asset("bonds", 500_000.0, insured_value_eur=500_000.0, premium_eur=1_000.0),
        Asset(
            "art",
            200_000.0,
            insured_value_eur=0.0,
            premium_eur=0.0,
            claims=({"status": "open"},),
        ),
    )


def test_summary_aggregation_is_exact():
    s = track_assets(make_assets())
    assert s.total_asset_value_eur == 1_700_000.0
    assert s.insured_value_eur == 1_300_000.0
    assert s.uninsured_value_eur == 400_000.0  # 200k home + 200k art
    assert s.premium_total_eur == 3_400.0
    assert s.open_claims_count == 2  # one open claim each on home & art
    assert s.coverage_gap_count == 2
    assert s.coverage_gap_value_eur == 400_000.0
    assert s.coverage_ratio == pytest.approx(1_300_000.0 / 1_700_000.0)


def test_coverage_gaps_flags_underinsured_and_uninsured_only():
    gaps = coverage_gaps(make_assets())
    ids = {g["asset_id"] for g in gaps}
    assert ids == {"family-home", "art"}  # fully-insured "bonds" excluded
    for g in gaps:
        assert g["uninsured_value_eur"] > 0
        assert g["recommendation"]["auto"] is False
        assert g["recommendation"]["action"] == "review-manually"


def test_no_auto_policy_buy_or_cancel_anywhere():
    report = build_report(make_assets())
    assert report["auto_policy_actions"] == []
    blob = json.dumps(report)
    for forbidden in FORBIDDEN_ACTIONS:
        assert forbidden not in blob
    for gap in report["coverage_gaps"]:
        assert gap["recommendation"]["auto"] is False


def test_report_is_json_serializable_and_held_together():
    report = build_report(make_assets())
    text = json.dumps(report)  # must not raise
    loaded = json.loads(text)
    assert loaded["factory"] == "df-150"
    assert loaded["domain"] == "K_0"
    assert loaded["welle"] == 25
    assert loaded["summary"]["premium_total_eur"] == 3_400.0
    assert loaded["summary"]["open_claims_count"] == 2
    assert len(loaded["coverage_gaps"]) == 2


def test_write_report_persists_df_150_file(tmp_path):
    report = build_report(make_assets())
    path = write_report(report, reports_dir=str(tmp_path))
    name = os.path.basename(path)
    assert name == f"df-150-{date.today().isoformat()}.json"
    with open(path, encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert loaded["summary"]["uninsured_value_eur"] == 400_000.0
    assert loaded["auto_policy_actions"] == []


def test_stop_flag_detection(tmp_path):
    flag = tmp_path / "df-150.stop"
    assert stop_requested(str(flag)) is False
    flag.touch()
    assert stop_requested(str(flag)) is True


def test_empty_portfolio_is_safe():
    s = track_assets([])
    assert s.total_asset_value_eur == 0.0
    assert s.coverage_ratio == 0.0  # no division-by-zero
    assert s.coverage_gap_count == 0


def test_tracking_never_mutates_assets():
    assets = make_assets()
    track_assets(assets)
    coverage_gaps(assets)
    build_report(assets)
    # frozen dataclasses + read-only aggregation: values unchanged
    assert assets[0].value_eur == 1_000_000.0
    assert assets[0].insured_value_eur == 800_000.0
    assert assets[2].open_claims == 1
