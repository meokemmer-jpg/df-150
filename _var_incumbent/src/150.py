from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List, Optional


def analyze_insurance_coverage(
    assets: Iterable[Dict[str, Any]],
    claims: Optional[Iterable[Dict[str, Any]]] = None,
    as_of: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Compute core KPM insurance coverage metrics per asset set.

    Expected asset fields:
    - asset_id: str
    - name: str
    - value_eur: number >= 0
    - insured: bool
    - premium_eur: number >= 0
    - coverage_gap: optional non-empty string

    Expected claim fields:
    - status: e.g. "open", "closed"
    """
    asset_rows: List[Dict[str, Any]] = []
    insured_value = 0.0
    uninsured_value = 0.0
    premium_total = 0.0
    coverage_gaps: List[Dict[str, str]] = []

    for raw_asset in assets:
        asset_id = str(raw_asset["asset_id"])
        name = str(raw_asset["name"])
        value_eur = _as_non_negative_float(raw_asset["value_eur"], "value_eur")
        insured = bool(raw_asset["insured"])
        premium_eur = _as_non_negative_float(raw_asset.get("premium_eur", 0.0), "premium_eur")
        explicit_gap = str(raw_asset.get("coverage_gap", "")).strip()

        premium_total += premium_eur
        if insured:
            insured_value += value_eur
        else:
            uninsured_value += value_eur
            if value_eur > 0:
                coverage_gaps.append(
                    {
                        "asset_id": asset_id,
                        "name": name,
                        "reason": "asset has value but is not insured",
                    }
                )

        if explicit_gap:
            coverage_gaps.append(
                {
                    "asset_id": asset_id,
                    "name": name,
                    "reason": explicit_gap,
                }
            )

        asset_rows.append(
            {
                "asset_id": asset_id,
                "name": name,
                "value_eur": value_eur,
                "insured": insured,
                "premium_eur": premium_eur,
            }
        )

    claim_list = list(claims or [])
    open_claims_count = sum(
        1 for claim in claim_list if str(claim.get("status", "")).strip().lower() == "open"
    )

    snapshot_date = (as_of or date.today()).isoformat()
    return {
        "report_date": snapshot_date,
        "insured_asset_value_eur": round(insured_value, 2),
        "uninsured_asset_value_eur": round(uninsured_value, 2),
        "premium_total_eur": round(premium_total, 2),
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "assets": asset_rows,
        "auto_policy_actions": [],
    }


def build_report_filename(report_date: Optional[date] = None) -> str:
    snapshot_date = (report_date or date.today()).isoformat()
    return f"reports/df-150-{snapshot_date}.json"


def _as_non_negative_float(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if number < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return number
# [CRUX-MK]
