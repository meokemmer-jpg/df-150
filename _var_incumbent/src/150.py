from __future__ import annotations

from typing import Any, Dict, Iterable, List


def summarize_insurance_status(
    assets: Iterable[Dict[str, Any]], claims: Iterable[Dict[str, Any]] | None = None
) -> Dict[str, Any]:
    """
    Summarize per-asset insurance status for KPM coverage tracking.

    Expected asset fields:
    - name: str
    - value_eur: number >= 0
    - insured_value_eur: number >= 0 (optional, default 0)
    - premium_eur: number >= 0 (optional, default 0)
    - coverage_required: bool (optional, default True)

    Expected claim fields:
    - status: str, counted as open when equal to "open" (case-insensitive)
    """
    asset_rows: List[Dict[str, Any]] = []
    insured_total = 0.0
    uninsured_total = 0.0
    premium_total = 0.0
    coverage_gaps: List[Dict[str, Any]] = []

    for asset in assets:
        name = str(asset["name"])
        value = _as_non_negative_float(asset.get("value_eur", 0), "value_eur")
        insured_value = _as_non_negative_float(
            asset.get("insured_value_eur", 0), "insured_value_eur"
        )
        premium = _as_non_negative_float(asset.get("premium_eur", 0), "premium_eur")
        coverage_required = bool(asset.get("coverage_required", True))

        covered = min(value, insured_value)
        uninsured = max(0.0, value - covered)

        insured_total += covered
        uninsured_total += uninsured
        premium_total += premium

        gap = coverage_required and uninsured > 0
        if gap:
            coverage_gaps.append(
                {
                    "asset": name,
                    "uninsured_value_eur": round(uninsured, 2),
                }
            )

        asset_rows.append(
            {
                "asset": name,
                "value_eur": round(value, 2),
                "insured_value_eur": round(covered, 2),
                "uninsured_value_eur": round(uninsured, 2),
                "premium_eur": round(premium, 2),
                "has_coverage_gap": gap,
            }
        )

    open_claims_count = 0
    for claim in claims or ():
        if str(claim.get("status", "")).strip().lower() == "open":
            open_claims_count += 1

    return {
        "insured_asset_value_eur": round(insured_total, 2),
        "uninsured_asset_value_eur": round(uninsured_total, 2),
        "premium_total_eur": round(premium_total, 2),
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "assets": asset_rows,
        "auto_policy_actions": [],
    }


def _as_non_negative_float(value: Any, field_name: str) -> float:
    number = float(value)
    if number < 0:
        raise ValueError(f"{field_name} must be >= 0")
    return number
# [CRUX-MK]
