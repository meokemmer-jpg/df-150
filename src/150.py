"""DF-150 KPM insurance coverage tracking core.

Pure functions only: no policy purchase or cancellation side effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Union

__all__ = ["Asset", "Policy", "Claim", "is_policy_active", "is_claim_open", "compute_report"]


@dataclass(frozen=True)
class Asset:
    asset_id: str
    value_eur: float


@dataclass(frozen=True)
class Policy:
    policy_id: str
    asset_id: str
    premium_eur: float
    coverage_eur: float
    status: str = "active"


@dataclass(frozen=True)
class Claim:
    claim_id: str
    policy_id: str
    status: str = "open"


def _normalize_status(status: str) -> str:
    return status.strip().lower()


def is_policy_active(policy: Policy) -> bool:
    return _normalize_status(policy.status) == "active"


def is_claim_open(claim: Claim) -> bool:
    return _normalize_status(claim.status) == "open"


def compute_report(
    assets: Sequence[Asset],
    policies: Sequence[Policy],
    claims: Sequence[Claim],
) -> Dict[str, Union[float, int, List[Dict]]]:
    active_policies = [p for p in policies if is_policy_active(p)]

    active_by_asset: Dict[str, List[Policy]] = {}
    for policy in active_policies:
        active_by_asset.setdefault(policy.asset_id, []).append(policy)

    open_claims = [c for c in claims if is_claim_open(c)]
    open_claims_by_policy: Dict[str, int] = {}
    for claim in open_claims:
        open_claims_by_policy[claim.policy_id] = (
            open_claims_by_policy.get(claim.policy_id, 0) + 1
        )

    per_asset: List[Dict] = []
    coverage_gaps: List[Dict] = []
    insured_value_eur = 0.0
    uninsured_value_eur = 0.0
    premium_total_eur = 0.0

    for asset in sorted(assets, key=lambda a: a.asset_id):
        asset_policies = active_by_asset.get(asset.asset_id, [])
        total_coverage_eur = sum(p.coverage_eur for p in asset_policies)
        premium_eur = sum(p.premium_eur for p in asset_policies)
        asset_open_claims = sum(
            open_claims_by_policy.get(p.policy_id, 0) for p in asset_policies
        )

        insured = bool(asset_policies)
        gap = (not insured) or total_coverage_eur < asset.value_eur

        if gap:
            coverage_gaps.append(
                {
                    "asset_id": asset.asset_id,
                    "value_eur": asset.value_eur,
                    "total_coverage_eur": total_coverage_eur,
                    "gap_eur": max(asset.value_eur - total_coverage_eur, 0.0),
                    "reason": "uninsured" if not insured else "underinsured",
                }
            )

        if insured:
            insured_value_eur += asset.value_eur
        else:
            uninsured_value_eur += asset.value_eur

        premium_total_eur += premium_eur

        per_asset.append(
            {
                "asset_id": asset.asset_id,
                "value_eur": asset.value_eur,
                "insured": insured,
                "active_policies": len(asset_policies),
                "total_coverage_eur": total_coverage_eur,
                "premium_eur": premium_eur,
                "open_claims_count": asset_open_claims,
                "coverage_gap": gap,
            }
        )

    return {
        "insured_value_eur": insured_value_eur,
        "uninsured_value_eur": uninsured_value_eur,
        "premium_total_eur": premium_total_eur,
        "open_claims_count": len(open_claims),
        "coverage_gaps": coverage_gaps,
        "per_asset": per_asset,
    }
# [CRUX-MK]
