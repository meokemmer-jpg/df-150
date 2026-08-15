import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import sys
from pathlib import Path
from importlib import import_module

import pytest

# The literal `from 150 import ...` is invalid Python 3 syntax because module
# names cannot start with a digit.  importlib is the stdlib-compliant equivalent.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))

_150 = import_module("150")

Asset = _150.Asset
Policy = _150.Policy
Claim = _150.Claim
compute_insured_uninsured = _150.compute_insured_uninsured
compute_premium_total = _150.compute_premium_total
count_open_claims = _150.count_open_claims
find_coverage_gaps = _150.find_coverage_gaps
build_status_report = _150.build_status_report


def _sample_data():
    assets = [
        Asset(asset_id="villa", value_eur=500_000.0),
        Asset(asset_id="yacht", value_eur=300_000.0),
        Asset(asset_id="jewelry", value_eur=200_000.0),
    ]
    policies = [
        Policy(policy_id="pol-1", asset_id="villa", premium_eur=1_200.0, active=True),
        Policy(policy_id="pol-2", asset_id="yacht", premium_eur=900.0, active=False),
        Policy(policy_id="pol-3", asset_id="jewelry", premium_eur=650.0, active=True),
    ]
    claims = [
        Claim(claim_id="claim-1", asset_id="villa", status="OPEN"),
        Claim(claim_id="claim-2", asset_id="villa", status="closed"),
        Claim(claim_id="claim-3", asset_id="jewelry", status="Open"),
    ]
    return assets, policies, claims


def test_insured_uninsured_values():
    assets, policies, _ = _sample_data()
    insured_value, uninsured_value = compute_insured_uninsured(assets, policies)

    assert insured_value == pytest.approx(700_000.0)
    assert uninsured_value == pytest.approx(300_000.0)


def test_premium_total_uses_active_policies_only():
    _, policies, _ = _sample_data()

    assert compute_premium_total(policies) == pytest.approx(1_850.0)


def test_open_claims_count_is_case_insensitive():
    _, _, claims = _sample_data()

    assert count_open_claims(claims) == 2


def test_find_coverage_gaps():
    assets, policies, _ = _sample_data()
    gap_ids = [gap.asset_id for gap in find_coverage_gaps(assets, policies)]

    assert gap_ids == ["yacht"]


def test_build_status_report():
    assets, policies, claims = _sample_data()
    report = build_status_report(assets, policies, claims)

    assert report.insured_value_eur == pytest.approx(700_000.0)
    assert report.uninsured_value_eur == pytest.approx(300_000.0)
    assert report.premium_total_eur == pytest.approx(1_850.0)
    assert report.open_claims_count == 2
    assert [gap.asset_id for gap in report.coverage_gaps] == ["yacht"]


def test_no_auto_policy_buy_or_cancel():
    assets, policies, claims = _sample_data()
    active_before = [policy.active for policy in policies]

    build_status_report(assets, policies, claims)

    assert [policy.active for policy in policies] == active_before
    assert _150.AUTO_POLICY_BUY_OR_CANCEL_ENABLED is False
    assert not hasattr(_150, "buy_policy")
    assert not hasattr(_150, "cancel_policy")
