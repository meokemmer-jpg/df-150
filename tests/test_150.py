import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import sys
import importlib

# The module is named '150.py' (a number), which is not a valid Python identifier.
# Therefore we use importlib to load it and alias it as '_150' for valid import syntax.
sys.path.insert(0, ".")
sys.modules["_150"] = importlib.import_module("150")

from _150 import (  # noqa: E402
    AssetInsurance,
    create_asset,
    uninsured_value,
    coverage_gap,
    is_fully_insured,
    total_insured,
    total_uninsured,
    total_premium,
    total_open_claims,
    coverage_gaps,
    report,
)


# ---------- Tests ----------

def test_create_asset_defaults():
    asset = create_asset("A1", 1000.0, 800.0, 50.0)
    assert asset.total_value == 1000.0
    assert asset.insured_value == 800.0
    assert asset.premium == 50.0
    assert asset.open_claims == 0
    assert asset.asset_id == "A1"


def test_create_asset_with_claims():
    asset = create_asset("A2", 2000.0, 1500.0, 100.0, 3)
    assert asset.open_claims == 3


def test_uninsured_value():
    asset = create_asset("A1", 1000.0, 800.0, 50.0)
    assert uninsured_value(asset) == 200.0

    # Fully insured
    asset2 = create_asset("A2", 1000.0, 1000.0, 60.0)
    assert uninsured_value(asset2) == 0.0

    # Over insured
    asset3 = create_asset("A3", 1000.0, 1200.0, 70.0)
    assert uninsured_value(asset3) == 0.0


def test_coverage_gap():
    asset = create_asset("A1", 1000.0, 800.0, 50.0)
    assert coverage_gap(asset) == 200.0

    # Fully insured
    asset2 = create_asset("A2", 1000.0, 1000.0, 60.0)
    assert coverage_gap(asset2) == 0.0


def test_is_fully_insured():
    assert is_fully_insured(create_asset("A", 500.0, 500.0, 30.0)) is True
    assert is_fully_insured(create_asset("B", 500.0, 400.0, 30.0)) is False
    assert is_fully_insured(create_asset("C", 500.0, 600.0, 30.0)) is True


def test_aggregates():
    assets = [
        create_asset("A1", 1000.0, 800.0, 50.0, 2),
        create_asset("A2", 2000.0, 1500.0, 100.0, 1),
        create_asset("A3", 500.0, 500.0, 30.0, 0),
    ]
    assert total_insured(assets) == 800.0 + 1500.0 + 500.0 == 2800.0
    assert total_uninsured(assets) == (200.0 + 500.0 + 0.0) == 700.0
    assert total_premium(assets) == 50.0 + 100.0 + 30.0 == 180.0
    assert total_open_claims(assets) == 2 + 1 + 0 == 3


def test_coverage_gaps_list():
    assets = [
        create_asset("A1", 1000.0, 800.0, 50.0),
        create_asset("A2", 2000.0, 2000.0, 100.0),  # no gap
        create_asset("A3", 500.0, 200.0, 30.0),
    ]
    gaps = coverage_gaps(assets)
    assert len(gaps) == 2
    assert gaps[0].asset_id == "A1"
    assert gaps[1].asset_id == "A3"


def test_report():
    assets = [
        create_asset("A1", 1000.0, 800.0, 50.0, 2),
        create_asset("A2", 2000.0, 2000.0, 100.0, 0),
    ]
    rep = report(assets)
    assert rep == {
        "total_insured": 2800.0,
        "total_uninsured": 200.0,
        "total_premium": 150.0,
        "total_open_claims": 2,
        "coverage_gap_count": 1,
    }


def test_empty_assets():
    assert total_insured([]) == 0.0
    assert total_uninsured([]) == 0.0
    assert total_premium([]) == 0.0
    assert total_open_claims([]) == 0
    assert coverage_gaps([]) == []
