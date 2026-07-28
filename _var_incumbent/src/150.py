from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict, Any


@dataclass(frozen=True)
class AssetCoverage:
    asset_id: str
    name: str
    value_eur: float
    insured: bool
    premium_eur: float
    has_gap: bool
    gap_reason: str | None


def evaluate_asset(asset: Dict[str, Any]) -> AssetCoverage:
    asset_id = str(asset["asset_id"])
    name = str(asset.get("name", asset_id))
    value_eur = float(asset["value_eur"])
    insured = bool(asset.get("insured", False))
    premium_eur = float(asset.get("premium_eur", 0.0))
    coverage_limit_eur = asset.get("coverage_limit_eur")

    has_gap = False
    gap_reason = None

    if not insured:
        has_gap = True
        gap_reason = "uninsured"
    elif coverage_limit_eur is not None and float(coverage_limit_eur) < value_eur:
        has_gap = True
        gap_reason = "underinsured"

    return AssetCoverage(
        asset_id=asset_id,
        name=name,
        value_eur=round(value_eur, 2),
        insured=insured,
        premium_eur=round(premium_eur, 2),
        has_gap=has_gap,
        gap_reason=gap_reason,
    )


def summarize_insurance_status(
    assets: Iterable[Dict[str, Any]],
    claims: Iterable[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    evaluated: List[AssetCoverage] = [evaluate_asset(asset) for asset in assets]
    claims = list(claims or [])

    insured_value = sum(a.value_eur for a in evaluated if a.insured)
    uninsured_value = sum(a.value_eur for a in evaluated if not a.insured)
    premium_total = sum(a.premium_eur for a in evaluated)
    coverage_gaps = [
        {
            "asset_id": a.asset_id,
            "name": a.name,
            "reason": a.gap_reason,
            "value_eur": a.value_eur,
        }
        for a in evaluated
        if a.has_gap
    ]

    return {
        "insured_asset_value_eur": round(insured_value, 2),
        "uninsured_asset_value_eur": round(uninsured_value, 2),
        "premium_total_eur": round(premium_total, 2),
        "open_claims_count": sum(1 for claim in claims if claim.get("status") == "open"),
        "coverage_gaps": coverage_gaps,
        "auto_policy_actions": [],
    }
# [CRUX-MK]
