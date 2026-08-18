import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# Hinweis: `from 150 import ...` ist als Python-Syntax nicht gültig,
# weil Modulnamen nicht mit einer Ziffer beginnen dürfen.
# Das Modul "150.py" wird daher per importlib geladen.
import importlib
import sys
from pathlib import Path

import pytest

try:
    m = importlib.import_module("150")
except ModuleNotFoundError:
    # Beim pytest-Lauf aus dem Projektroot ggf. den Root-Pfad ergänzen.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    m = importlib.import_module("150")

InsuranceTracker = m.InsuranceTracker


def test_asset_insurance_status_tracking():
    tracker = InsuranceTracker()
    tracker.add_asset("A1", "Villa", 100_000, insured_value_eur=80_000, premium_eur=1_200)
    tracker.add_asset("A2", "Wertpapiere", 50_000, insured_value_eur=50_000, premium_eur=800)

    status = tracker.status()
    assert status["total_value_eur"] == 150_000
    assert status["insured_value_eur"] == 130_000
    assert status["uninsured_value_eur"] == 20_000
    assert status["premium_total_eur"] == 2_000
    assert status["open_claims_count"] == 0
    assert status["coverage_gaps"] == [{"asset_id": "A1", "gap_eur": 20_000}]

    tracker.update_insurance("A1", insured_value_eur=90_000, premium_eur=1_500)

    status = tracker.status()
    assert status["insured_value_eur"] == 140_000
    assert status["uninsured_value_eur"] == 10_000
    assert status["premium_total_eur"] == 2_300
    assert status["coverage_gaps"] == [{"asset_id": "A1", "gap_eur": 10_000}]

    c1 = tracker.add_claim("A1", 5_000)
    c2 = tracker.add_claim("A2", 3_000)
    assert tracker.status()["open_claims_count"] == 2

    tracker.close_claim(c1)
    assert tracker.status()["open_claims_count"] == 1

    a1 = tracker.get_asset_status("A1")
    assert a1["value_eur"] == 100_000
    assert a1["insured_value_eur"] == 90_000
    assert a1["uninsured_value_eur"] == 10_000
    assert a1["premium_eur"] == 1_500


def test_no_auto_policy_buy_or_cancel_and_validation():
    tracker = InsuranceTracker()
    tracker.add_asset("A3", "Lager", 10_000, insured_value_eur=10_000, premium_eur=100)

    with pytest.raises(ValueError):
        tracker.update_insurance("A3", insured_value_eur=11_000)

    with pytest.raises(ValueError):
        tracker.update_insurance("A3", premium_eur=-1)

    with pytest.raises(KeyError):
        tracker.add_claim("NOPE", 100)

    # Keine automatische Policy-Änderung: Der Bestand bleibt unverändert.
    a3 = tracker.get_asset_status("A3")
    assert a3["insured_value_eur"] == 10_000
    assert a3["premium_eur"] == 100
