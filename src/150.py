"""DF-150 KPM insurance coverage tracker.

Read-only per-asset insurance status tracking. This module never buys or
cancels policies.
"""

from dataclasses import dataclass

__all__ = [
    "Asset",
    "Policy",
    "Claim",
    "per_asset_status",
    "coverage_summary",
    "track_status",
]


@dataclass(frozen=True)
class Asset:
    asset_id: str
    value: float


@dataclass(frozen=True)
class Policy:
    policy_id: str
    asset_id: str
    insured_value: float
    premium: float = 0.0
    active: bool = True


@dataclass(frozen=True)
class Claim:
    claim_id: str
    asset_id: str
    status: str = "open"


def _is_open(claim: Claim) -> bool:
    return claim.status.strip().lower() == "open"


def per_asset_status(asset, policies=(), claims=()):
    policies = tuple(policies)
    claims = tuple(claims)

    active_policies = [
        p for p in policies
        if p.asset_id == asset.asset_id and p.active
    ]

    asset_value = float(asset.value)
    insured_value = float(sum(p.insured_value for p in active_policies))
    uninsured_value = max(0.0, asset_value - insured_value)
    open_claims_count = sum(
        1 for c in claims
        if c.asset_id == asset.asset_id and _is_open(c)
    )

    if insured_value <= 0.0:
        coverage_status = "uninsured"
    elif uninsured_value <= 0.0:
        coverage_status = "insured"
    else:
        coverage_status = "partial"

    return {
        "asset_id": asset.asset_id,
        "asset_value": asset_value,
        "insured_value": insured_value,
        "uninsured_value": uninsured_value,
        "premium_total": float(sum(p.premium for p in active_policies)),
        "open_claims_count": open_claims_count,
        "coverage_gap": uninsured_value,
        "coverage_status": coverage_status,
        "policy_ids": [p.policy_id for p in active_policies],
    }


def coverage_summary(assets, policies=(), claims=()):
    policies = tuple(policies)
    claims = tuple(claims)

    rows = [per_asset_status(a, policies, claims) for a in assets]
    gaps = [r for r in rows if r["coverage_gap"] > 0.0]

    return {
        "assets_count": len(rows),
        "total_asset_value": float(sum(r["asset_value"] for r in rows)),
        "total_insured_value": float(sum(r["insured_value"] for r in rows)),
        "total_uninsured_value": float(sum(r["uninsured_value"] for r in rows)),
        "premium_total": float(sum(r["premium_total"] for r in rows)),
        "open_claims_count": sum(r["open_claims_count"] for r in rows),
        "coverage_gap_total": float(sum(r["coverage_gap"] for r in gaps)),
        "coverage_gap_assets": [
            {"asset_id": r["asset_id"], "coverage_gap": r["coverage_gap"]}
            for r in gaps
        ],
        "coverage_gap_asset_ids": [r["asset_id"] for r in gaps],
        "per_asset_status": rows,
    }


track_status = coverage_summary
# [CRUX-MK]
