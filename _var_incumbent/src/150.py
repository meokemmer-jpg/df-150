from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List, Optional


CENT = Decimal("0.01")


def _money(value: object) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Asset:
    asset_id: str
    name: str
    value_eur: Decimal
    required_coverage: bool = True


@dataclass(frozen=True)
class Policy:
    policy_id: str
    asset_id: str
    premium_eur: Decimal
    active: bool = True
    coverage_limit_eur: Optional[Decimal] = None


@dataclass(frozen=True)
class Claim:
    claim_id: str
    asset_id: str
    status: str


def make_asset(asset_id: str, name: str, value_eur: object, required_coverage: bool = True) -> Asset:
    return Asset(
        asset_id=asset_id,
        name=name,
        value_eur=_money(value_eur),
        required_coverage=required_coverage,
    )


def make_policy(
    policy_id: str,
    asset_id: str,
    premium_eur: object,
    active: bool = True,
    coverage_limit_eur: Optional[object] = None,
) -> Policy:
    limit = None if coverage_limit_eur is None else _money(coverage_limit_eur)
    return Policy(
        policy_id=policy_id,
        asset_id=asset_id,
        premium_eur=_money(premium_eur),
        active=active,
        coverage_limit_eur=limit,
    )


def make_claim(claim_id: str, asset_id: str, status: str) -> Claim:
    return Claim(claim_id=claim_id, asset_id=asset_id, status=status)


def compute_insurance_status(
    assets: Iterable[Asset],
    policies: Iterable[Policy],
    claims: Iterable[Claim],
) -> dict:
    assets = list(assets)
    active_policies_by_asset = {}
    premium_total = Decimal("0.00")

    for policy in policies:
        if not policy.active:
            continue
        premium_total += policy.premium_eur
        active_policies_by_asset.setdefault(policy.asset_id, []).append(policy)

    insured_value = Decimal("0.00")
    uninsured_value = Decimal("0.00")
    coverage_gaps: List[dict] = []

    for asset in assets:
        active_policies = active_policies_by_asset.get(asset.asset_id, [])
        if not asset.required_coverage:
            continue

        if not active_policies:
            uninsured_value += asset.value_eur
            coverage_gaps.append(
                {
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "gap_type": "missing_policy",
                    "uncovered_value_eur": str(asset.value_eur),
                    "action": "manual_review_only",
                }
            )
            continue

        covered_amount = max(
            (
                asset.value_eur
                if policy.coverage_limit_eur is None
                else min(asset.value_eur, policy.coverage_limit_eur)
            )
            for policy in active_policies
        )
        uncovered_amount = asset.value_eur - covered_amount
        insured_value += covered_amount
        uninsured_value += uncovered_amount

        if uncovered_amount > Decimal("0.00"):
            coverage_gaps.append(
                {
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "gap_type": "underinsured",
                    "uncovered_value_eur": str(uncovered_amount),
                    "action": "manual_review_only",
                }
            )

    open_claims_count = sum(1 for claim in claims if claim.status.strip().lower() == "open")

    return {
        "insured_asset_value_eur": str(insured_value.quantize(CENT)),
        "uninsured_asset_value_eur": str(uninsured_value.quantize(CENT)),
        "premium_total_eur": str(premium_total.quantize(CENT)),
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "auto_policy_actions": [],
    }
# [CRUX-MK]
