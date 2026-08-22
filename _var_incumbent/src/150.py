"""DF-150 KPM Insurance Coverage Tracker (stdlib only).

Tracks per-asset insurance status, premium totals, open claims and
coverage gaps. This module intentionally never buys or cancels policies.
"""

from typing import Any, Dict, List


def coverage_gap_for_asset(asset: Dict[str, Any]) -> float:
    """Return the coverage gap (EUR) for a single asset dict.

    The gap is the amount of asset value not covered by insurance.
    Uninsured assets are fully uncovered. Underinsured assets show the
    missing part.
    """
    value = float(asset.get("value_eur", 0.0))
    insured = bool(asset.get("insured", False))
    insured_value = asset.get("insured_value_eur")

    if insured_value is None:
        insured_value = value if insured else 0.0
    else:
        insured_value = float(insured_value)

    gap = value - insured_value
    return max(0.0, gap)


def track_insurance_status(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate insurance tracking data for a list of asset dicts.

    Args:
        assets: List of dicts with keys:
            id (str): asset identifier
            value_eur (float/int): market value in EUR
            insured (bool): True if the asset has an active policy
            premium_eur (float/int): annual premium paid (0 if uninsured)
            claims_open (int): number of open claims for this asset
            insured_value_eur (float/int, optional): insured amount, defaults
                to value_eur for insured assets and 0 for uninsured assets.

    Returns:
        dict with aggregated totals:
            insured_value_eur
            uninsured_value_eur
            total_premium_eur
            open_claims_count
            coverage_gaps (list of dicts for assets with gap > 0)
            total_coverage_gap_eur
    """
    insured_value_total = 0.0
    uninsured_value_total = 0.0
    premium_total = 0.0
    open_claims_total = 0
    gaps = []
    total_gap = 0.0

    for asset in assets:
        value = float(asset.get("value_eur", 0.0))
        insured = bool(asset.get("insured", False))
        premium = float(asset.get("premium_eur", 0.0))
        claims = int(asset.get("claims_open", 0))

        if insured:
            insured_value_total += value
        else:
            uninsured_value_total += value

        premium_total += premium
        open_claims_total += claims

        gap = coverage_gap_for_asset(asset)
        if gap > 0:
            gaps.append({
                "asset_id": asset.get("id", "unknown"),
                "gap_eur": round(gap, 2),
            })
        total_gap += gap

    return {
        "insured_value_eur": round(insured_value_total, 2),
        "uninsured_value_eur": round(uninsured_value_total, 2),
        "total_premium_eur": round(premium_total, 2),
        "open_claims_count": open_claims_total,
        "coverage_gaps": gaps,
        "total_coverage_gap_eur": round(total_gap, 2),
    }
# [CRUX-MK]
