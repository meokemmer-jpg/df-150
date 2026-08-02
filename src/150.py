from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any


@dataclass(frozen=True)
class AssetStatus:
    asset_id: str
    value_eur: float
    insured: bool
    premium_eur: float
    has_coverage_gap: bool


def _to_asset_status(asset: Mapping[str, Any]) -> AssetStatus:
    asset_id = str(asset["asset_id"])
    value_eur = float(asset.get("value_eur", 0.0))
    insured = bool(asset.get("insured", False))
    premium_eur = float(asset.get("premium_eur", 0.0))

    if value_eur < 0 or premium_eur < 0:
        raise ValueError("value_eur and premium_eur must be non-negative")

    coverage_limit = asset.get("coverage_limit_eur")
    excluded = bool(asset.get("excluded", False))
    missing_policy = not insured
    underinsured = insured and coverage_limit is not None and float(coverage_limit) < value_eur
    has_coverage_gap = missing_policy or excluded or underinsured

    return AssetStatus(
        asset_id=asset_id,
        value_eur=value_eur,
        insured=insured,
        premium_eur=premium_eur,
        has_coverage_gap=has_coverage_gap,
    )


def calculate_insurance_status(
    assets: Iterable[Mapping[str, Any]],
    claims: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    asset_statuses = [_to_asset_status(asset) for asset in assets]

    insured_value = sum(a.value_eur for a in asset_statuses if a.insured)
    uninsured_value = sum(a.value_eur for a in asset_statuses if not a.insured)
    premium_total = sum(a.premium_eur for a in asset_statuses)

    open_claims_count = sum(
        1 for claim in claims if str(claim.get("status", "")).lower() == "open"
    )

    coverage_gaps = [a.asset_id for a in asset_statuses if a.has_coverage_gap]

    return {
        "insured_value_eur": round(insured_value, 2),
        "uninsured_value_eur": round(uninsured_value, 2),
        "premium_total_eur": round(premium_total, 2),
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
    }
# [CRUX-MK]
