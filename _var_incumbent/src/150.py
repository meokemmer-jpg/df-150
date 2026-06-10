from __future__ import annotations

from typing import Any, Dict, Iterable, List


def evaluate_insurance_status(
    assets: Iterable[Dict[str, Any]],
    claims: Iterable[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Compute per-asset and portfolio-level insurance status for KPM.

    Expected asset fields:
    - asset_id: str
    - name: str (optional)
    - value_eur: number
    - insured: bool
    - premium_eur: number (optional, defaults to 0)
    - insured_value_eur: number (optional, defaults to value_eur if insured else 0)
    - coverage_required_eur: number (optional, defaults to value_eur)
    - policy_active: bool (optional, defaults to insured)

    Expected claim fields:
    - status: e.g. "open", "closed"
    """
    claims = list(claims or [])
    asset_reports: List[Dict[str, Any]] = []

    insured_asset_value = 0.0
    uninsured_asset_value = 0.0
    premium_total = 0.0
    coverage_gaps: List[Dict[str, Any]] = []

    for raw_asset in assets:
        asset_id = str(raw_asset["asset_id"])
        name = str(raw_asset.get("name", asset_id))
        value_eur = float(raw_asset["value_eur"])
        insured = bool(raw_asset.get("insured", False))
        policy_active = bool(raw_asset.get("policy_active", insured))
        premium_eur = float(raw_asset.get("premium_eur", 0.0))
        required_eur = float(raw_asset.get("coverage_required_eur", value_eur))

        if insured and policy_active:
            insured_value_eur = float(raw_asset.get("insured_value_eur", value_eur))
            insured_asset_value += value_eur
            effective_insured_value = max(0.0, min(insured_value_eur, value_eur))
            gap_eur = max(0.0, required_eur - effective_insured_value)
            status = "insured" if gap_eur == 0 else "underinsured"
        else:
            insured_value_eur = 0.0
            effective_insured_value = 0.0
            uninsured_asset_value += value_eur
            gap_eur = max(0.0, required_eur)
            status = "uninsured"

        premium_total += premium_eur

        asset_report = {
            "asset_id": asset_id,
            "name": name,
            "status": status,
            "value_eur": round(value_eur, 2),
            "insured_value_eur": round(effective_insured_value, 2),
            "premium_eur": round(premium_eur, 2),
            "coverage_gap_eur": round(gap_eur, 2),
            "policy_active": policy_active,
            "auto_policy_action": None,
        }
        asset_reports.append(asset_report)

        if gap_eur > 0:
            coverage_gaps.append(
                {
                    "asset_id": asset_id,
                    "name": name,
                    "gap_eur": round(gap_eur, 2),
                    "reason": status,
                }
            )

    open_claims_count = sum(
        1 for claim in claims if str(claim.get("status", "")).lower() == "open"
    )

    return {
        "insured_asset_value_eur": round(insured_asset_value, 2),
        "uninsured_asset_value_eur": round(uninsured_asset_value, 2),
        "premium_total_eur": round(premium_total, 2),
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "assets": asset_reports,
        "auto_policy_actions": [],
    }
# [CRUX-MK]
