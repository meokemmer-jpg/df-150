from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping, Optional


@dataclass(frozen=True)
class AssetInsuranceStatus:
    asset_id: str
    name: str
    asset_value_eur: float
    insured_value_eur: float
    premium_eur: float
    is_insured: bool
    coverage_gap_eur: float


def _to_non_negative_float(value: object, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number") from exc
    if number < 0:
        raise ValueError(f"{field_name} must be >= 0")
    return number


def evaluate_asset_insurance_status(asset: Mapping[str, object]) -> AssetInsuranceStatus:
    asset_id = str(asset.get("asset_id") or "").strip()
    name = str(asset.get("name") or "").strip()

    if not asset_id:
        raise ValueError("asset_id is required")
    if not name:
        raise ValueError("name is required")

    asset_value_eur = _to_non_negative_float(asset.get("asset_value_eur", 0), "asset_value_eur")
    insured_value_eur = _to_non_negative_float(asset.get("insured_value_eur", 0), "insured_value_eur")
    premium_eur = _to_non_negative_float(asset.get("premium_eur", 0), "premium_eur")

    if insured_value_eur > asset_value_eur:
        raise ValueError("insured_value_eur must not exceed asset_value_eur")

    policy_active = bool(asset.get("policy_active", False))
    is_insured = policy_active and insured_value_eur > 0
    coverage_gap_eur = max(asset_value_eur - insured_value_eur, 0.0)

    return AssetInsuranceStatus(
        asset_id=asset_id,
        name=name,
        asset_value_eur=asset_value_eur,
        insured_value_eur=insured_value_eur,
        premium_eur=premium_eur,
        is_insured=is_insured,
        coverage_gap_eur=coverage_gap_eur,
    )


def summarize_portfolio_coverage(
    assets: Iterable[Mapping[str, object]],
    claims: Optional[Iterable[Mapping[str, object]]] = None,
) -> Mapping[str, object]:
    evaluated_assets: List[AssetInsuranceStatus] = [
        evaluate_asset_insurance_status(asset) for asset in assets
    ]

    open_claims_count = 0
    for claim in claims or ():
        status = str(claim.get("status") or "").strip().lower()
        if status == "open":
            open_claims_count += 1

    insured_asset_value_eur = sum(
        asset.insured_value_eur for asset in evaluated_assets if asset.is_insured
    )
    uninsured_asset_value_eur = sum(asset.coverage_gap_eur for asset in evaluated_assets)
    premium_total_eur = sum(asset.premium_eur for asset in evaluated_assets if asset.is_insured)
    coverage_gaps = [
        {
            "asset_id": asset.asset_id,
            "name": asset.name,
            "gap_eur": asset.coverage_gap_eur,
        }
        for asset in evaluated_assets
        if asset.coverage_gap_eur > 0
    ]

    return {
        "insured_asset_value_eur": insured_asset_value_eur,
        "uninsured_asset_value_eur": uninsured_asset_value_eur,
        "premium_total_eur": premium_total_eur,
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "asset_statuses": evaluated_assets,
    }
# [CRUX-MK]
