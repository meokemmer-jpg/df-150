from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


OPEN_CLAIM_STATUSES = {"open", "pending", "in_review"}


@dataclass(frozen=True)
class AssetStatus:
    asset_id: str
    insured_value_eur: float
    uninsured_value_eur: float
    is_fully_insured: bool
    gap_eur: float


def _is_active(policy: Dict[str, Any]) -> bool:
    return bool(policy.get("active", True))


def _coverage_for_asset(asset_id: str, policies: Iterable[Dict[str, Any]]) -> float:
    total = 0.0
    for policy in policies:
        if not _is_active(policy):
            continue
        if policy.get("asset_id") != asset_id:
            continue
        total += float(policy.get("coverage_amount_eur", 0.0))
    return total


def calculate_asset_statuses(
    assets: Iterable[Dict[str, Any]],
    policies: Iterable[Dict[str, Any]],
) -> List[AssetStatus]:
    policy_list = list(policies)
    statuses: List[AssetStatus] = []

    for asset in assets:
        asset_id = str(asset["asset_id"])
        asset_value = float(asset.get("value_eur", 0.0))
        covered = min(asset_value, _coverage_for_asset(asset_id, policy_list))
        uninsured = max(0.0, asset_value - covered)
        statuses.append(
            AssetStatus(
                asset_id=asset_id,
                insured_value_eur=covered,
                uninsured_value_eur=uninsured,
                is_fully_insured=uninsured == 0.0,
                gap_eur=uninsured,
            )
        )

    return statuses


def summarize_insurance_coverage(
    assets: Iterable[Dict[str, Any]],
    policies: Iterable[Dict[str, Any]],
    claims: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    asset_statuses = calculate_asset_statuses(assets, policies)
    active_policies = [p for p in policies if _is_active(p)]

    insured_total = round(sum(item.insured_value_eur for item in asset_statuses), 2)
    uninsured_total = round(sum(item.uninsured_value_eur for item in asset_statuses), 2)
    premium_total = round(sum(float(p.get("premium_eur", 0.0)) for p in active_policies), 2)
    open_claims_count = sum(
        1 for claim in claims if str(claim.get("status", "")).lower() in OPEN_CLAIM_STATUSES
    )

    coverage_gaps = [
        {
            "asset_id": item.asset_id,
            "gap_eur": round(item.gap_eur, 2),
            "reason": "uninsured_value" if item.gap_eur > 0 else "none",
        }
        for item in asset_statuses
        if item.gap_eur > 0
    ]

    return {
        "insured_value_eur": insured_total,
        "uninsured_value_eur": uninsured_total,
        "premium_total_eur": premium_total,
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "asset_statuses": [
            {
                "asset_id": item.asset_id,
                "insured_value_eur": round(item.insured_value_eur, 2),
                "uninsured_value_eur": round(item.uninsured_value_eur, 2),
                "is_fully_insured": item.is_fully_insured,
            }
            for item in asset_statuses
        ],
        "auto_policy_action": None,
    }
# [CRUX-MK]
