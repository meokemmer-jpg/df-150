import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# NOTE: the literal statement ``from 150 import ...`` is a SyntaxError --
# Python module names may not start with a digit. Loading the module named
# "150" therefore requires importlib.import_module("150"), used below.
import copy
import importlib
from datetime import date

m150 = importlib.import_module("150")
Asset = m150.Asset
summarize = m150.summarize
coverage_gaps = m150.coverage_gaps
build_report = m150.build_report

PORTFOLIO = [
    {"name": "Villa Am See",    "value_eur": 2_000_000,
     "insured_value_eur": 2_000_000, "premium_eur": 8_000, "open_claims": 1},
    {"name": "Yacht Nordlicht", "value_eur": 500_000,
     "insured_value_eur": 0, "premium_eur": 0, "open_claims": 0},
    {"name": "Goya-Sammlung",   "value_eur": 300_000,
     "insured_value_eur": 180_000, "premium_eur": 2_500, "open_claims": 2},
]


def test_summary_totals_and_metrics():
    s = summarize(PORTFOLIO)
    assert s["asset_count"] == 3
    assert s["total_value_eur"] == 2_800_000
    assert s["insured_value_eur"] == 2_180_000
    assert s["uninsured_value_eur"] == 620_000
    assert s["premium_total_eur"] == 10_500
    assert s["open_claims"] == 3
    assert s["coverage_gap_count"] == 2
    assert s["coverage_gaps_eur"] == 620_000
    assert s["coverage_ratio"] == 0.7786


def test_gaps_ranked_biggest_first_with_severity():
    gaps = summarize(PORTFOLIO)["gaps"]
    assert [g["asset"] for g in gaps] == ["Yacht Nordlicht", "Goya-Sammlung"]
    assert gaps[0]["gap_eur"] == 500_000 and gaps[0]["severity"] == 1.0
    assert gaps[1]["gap_eur"] == 120_000 and gaps[1]["severity"] == 0.4


def test_asset_objects_mixed_with_dicts_and_alias_keys():
    records = [
        Asset(name="Uhr", value_eur=50_000, insured_value_eur=50_000),
        {"name": "Auto", "value": 90_000, "insured_value": 60_000,
         "premium": 700, "claims": 1},
    ]
    s = summarize(records)
    assert s["asset_count"] == 2
    assert s["coverage_gap_count"] == 1
    assert s["gaps"][0]["asset"] == "Auto"
    assert s["gaps"][0]["gap_eur"] == 30_000


def test_fully_insured_portfolio_has_no_gap():
    s = summarize([Asset(name="Watch", value_eur=50_000,
                         insured_value_eur=50_000)])
    assert s["coverage_gap_count"] == 0
    assert s["coverage_ratio"] == 1.0


def test_empty_portfolio_is_safe():
    s = summarize([])
    assert s["asset_count"] == 0
    assert s["coverage_gap_count"] == 0
    assert s["coverage_ratio"] == 1.0
    assert s["gaps"] == []


def test_report_payload_shape():
    rpt = build_report(PORTFOLIO, report_date=date(2025, 1, 15))
    assert rpt["mission"] == "df-150-kpm-insurance-coverage"
    assert rpt["date"] == "2025-01-15"
    assert rpt["policy_action"] == "none-read-only"
    assert rpt["summary"]["uninsured_value_eur"] == 620_000


def test_inputs_are_never_mutated():
    frozen = copy.deepcopy(PORTFOLIO)
    summarize(PORTFOLIO)
    build_report(PORTFOLIO)
    assert PORTFOLIO == frozen

