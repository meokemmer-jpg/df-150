import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE if (HERE / "150.py").exists() else HERE.parent
sys.path.insert(0, str(ROOT))
sys.modules["_150"] = importlib.import_module("150")

# `from 150 import ...` is invalid as literal syntax; the replace makes it valid.
exec("from 150 import Asset, Policy, Claim, per_asset_status, coverage_summary".replace("150", "_150"), globals())


def test_per_asset_status_tracks_coverage_gap_and_open_claims():
    haus = Asset("haus", 500_000.0)
    policy = Policy("p-haus", "haus", 400_000.0, premium=1_200.0)
    claim = Claim("c-haus", "haus", "open")

    status = per_asset_status(haus, [policy], [claim])

    assert status["insured_value"] == 400_000.0
    assert status["uninsured_value"] == 100_000.0
    assert status["premium_total"] == 1_200.0
    assert status["open_claims_count"] == 1
    assert status["coverage_gap"] == 100_000.0
    assert status["coverage_status"] == "partial"


def test_coverage_summary_counts_only_active_policies_and_does_not_mutate_inputs():
    assets = [
        Asset("haus", 500_000.0),
        Asset("auto", 30_000.0),
        Asset("boot", 50_000.0),
    ]
    policies = [
        Policy("p-haus", "haus", 400_000.0, premium=1_200.0),
        Policy("p-auto", "auto", 30_000.0, premium=300.0),
        Policy("p-boot-lapsed", "boot", 50_000.0, premium=500.0, active=False),
    ]
    claims = [
        Claim("c-haus", "haus", "open"),
        Claim("c-boot", "boot", "open"),
        Claim("c-auto", "auto", "closed"),
    ]

    original = [(p.policy_id, p.active, p.premium) for p in policies]
    summary = coverage_summary(assets, policies, claims)
    unchanged = [(p.policy_id, p.active, p.premium) for p in policies]

    assert unchanged == original
    assert summary["total_asset_value"] == 580_000.0
    assert summary["total_insured_value"] == 430_000.0
    assert summary["total_uninsured_value"] == 150_000.0
    assert summary["premium_total"] == 1_500.0
    assert summary["open_claims_count"] == 2
    assert summary["coverage_gap_total"] == 150_000.0
    assert set(summary["coverage_gap_asset_ids"]) == {"haus", "boot"}
    assert {g["asset_id"] for g in summary["coverage_gap_assets"]} == {"haus", "boot"}

    auto_status = per_asset_status(assets[1], policies, claims)
    assert auto_status["coverage_status"] == "insured"
    assert auto_status["coverage_gap"] == 0.0
    assert auto_status["open_claims_count"] == 0

    boot_status = per_asset_status(assets[2], policies, claims)
    assert boot_status["coverage_status"] == "uninsured"
    assert boot_status["insured_value"] == 0.0

