from __future__ import annotations

from typing import Any, Iterable, Mapping


def build_coverage_report(
    assets: Iterable[Mapping[str, Any]],
    claims: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Aggregate per-asset insurance status into a single report.

    Required asset keys:
    - asset_id
    - value_eur

    Optional asset keys:
    - insured_value_eur
    - premium_eur
    """
    total_asset_value = 0.0
    insured_asset_value = 0.0
    premium_total = 0.0
    coverage_gaps = []

    for asset in assets:
        asset_id = asset["asset_id"]
        value_eur = _as_non_negative_float(asset["value_eur"], field="value_eur")
        insured_value_eur = _as_non_negative_float(
            asset.get("insured_value_eur", 0.0),
            field="insured_value_eur",
        )
        premium_eur = _as_non_negative_float(
            asset.get("premium_eur", 0.0),
            field="premium_eur",
        )

        covered_value = min(value_eur, insured_value_eur)
        gap_value = round(value_eur - covered_value, 2)

        total_asset_value += value_eur
        insured_asset_value += covered_value
        premium_total += premium_eur

        if gap_value > 0:
            coverage_gaps.append(
                {
                    "asset_id": asset_id,
                    "asset_value_eur": round(value_eur, 2),
                    "insured_value_eur": round(covered_value, 2),
                    "gap_value_eur": gap_value,
                    "status": "uninsured" if covered_value == 0 else "underinsured",
                }
            )

    open_claims_count = 0
    for claim in claims or ():
        if str(claim.get("status", "")).strip().lower() == "open":
            open_claims_count += 1

    uninsured_asset_value = round(total_asset_value - insured_asset_value, 2)

    return {
        "total_asset_value_eur": round(total_asset_value, 2),
        "insured_asset_value_eur": round(insured_asset_value, 2),
        "uninsured_asset_value_eur": uninsured_asset_value,
        "premium_total_eur": round(premium_total, 2),
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "fully_insured": uninsured_asset_value == 0,
    }


def _as_non_negative_float(value: Any, *, field: str) -> float:
    number = float(value)
    if number < 0:
        raise ValueError(f"{field} must be non-negative")
    return number
# [CRUX-MK]
