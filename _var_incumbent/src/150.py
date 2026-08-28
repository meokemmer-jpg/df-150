from __future__ import annotations

from typing import Iterable, Mapping, Any, Dict, List


def summarize_insurance_status(
    assets: Iterable[Mapping[str, Any]],
    claims: Iterable[Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Compute per-asset insurance status metrics for KPM.

    Each asset mapping supports:
    - asset_id: str
    - name: str
    - value_eur: int|float
    - insured: bool
    - premium_eur: int|float
    - coverage_required: bool (optional, default True)

    Each claim mapping supports:
    - status: str

    Returns:
    {
        "insured_value_eur": float,
        "uninsured_value_eur": float,
        "premium_total_eur": float,
        "open_claims_count": int,
        "coverage_gaps": [ ... ],
    }
    """
    insured_value = 0.0
    uninsured_value = 0.0
    premium_total = 0.0
    coverage_gaps: List[Dict[str, Any]] = []

    for asset in assets:
        value = float(asset.get("value_eur", 0.0))
        insured = bool(asset.get("insured", False))
        premium = float(asset.get("premium_eur", 0.0))
        coverage_required = bool(asset.get("coverage_required", True))

        premium_total += premium

        if insured:
            insured_value += value
        else:
            uninsured_value += value
            if coverage_required and value > 0:
                coverage_gaps.append(
                    {
                        "asset_id": asset.get("asset_id"),
                        "name": asset.get("name"),
                        "uninsured_value_eur": value,
                        "reason": "required_asset_uninsured",
                    }
                )

    open_claims_count = 0
    for claim in claims or ():
        if str(claim.get("status", "")).strip().lower() in {"open", "pending", "in_progress"}:
            open_claims_count += 1

    return {
        "insured_value_eur": insured_value,
        "uninsured_value_eur": uninsured_value,
        "premium_total_eur": premium_total,
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
    }
# [CRUX-MK]
