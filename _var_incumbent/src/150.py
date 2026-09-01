from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict, Any


@dataclass(frozen=True)
class Asset:
    name: str
    value_eur: float
    insured: bool
    premium_eur: float = 0.0
    coverage_required: bool = True


@dataclass(frozen=True)
class Claim:
    asset_name: str
    status: str


def evaluate_insurance_status(
    assets: Iterable[Asset],
    claims: Iterable[Claim],
) -> Dict[str, Any]:
    asset_list = list(assets)
    claim_list = list(claims)

    insured_value = 0.0
    uninsured_value = 0.0
    premium_total = 0.0
    coverage_gaps: List[Dict[str, Any]] = []

    for asset in asset_list:
        premium_total += float(asset.premium_eur)

        if asset.insured:
            insured_value += float(asset.value_eur)
        else:
            uninsured_value += float(asset.value_eur)

        if asset.coverage_required and not asset.insured:
            coverage_gaps.append(
                {
                    "asset_name": asset.name,
                    "gap_type": "missing_coverage",
                    "uninsured_value_eur": float(asset.value_eur),
                }
            )

    open_claims_count = sum(1 for claim in claim_list if claim.status.lower() == "open")

    return {
        "insured_value_eur": round(insured_value, 2),
        "uninsured_value_eur": round(uninsured_value, 2),
        "premium_total_eur": round(premium_total, 2),
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "policy_actions": [],  # No auto-buy / auto-cancel.
    }
# [CRUX-MK]
