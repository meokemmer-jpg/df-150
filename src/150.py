from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class Asset:
    asset_id: str
    name: str
    value_eur: float
    required_coverages: tuple[str, ...] = ()


@dataclass(frozen=True)
class Policy:
    policy_id: str
    asset_id: str
    covered_value_eur: float
    premium_eur: float
    status: str = "active"
    coverages: tuple[str, ...] = ()


@dataclass(frozen=True)
class Claim:
    claim_id: str
    asset_id: str
    status: str = "open"


def _to_asset(item: Dict[str, Any]) -> Asset:
    return Asset(
        asset_id=str(item["asset_id"]),
        name=str(item.get("name", item["asset_id"])),
        value_eur=float(item["value_eur"]),
        required_coverages=tuple(item.get("required_coverages", ())),
    )


def _to_policy(item: Dict[str, Any]) -> Policy:
    return Policy(
        policy_id=str(item["policy_id"]),
        asset_id=str(item["asset_id"]),
        covered_value_eur=float(item["covered_value_eur"]),
        premium_eur=float(item["premium_eur"]),
        status=str(item.get("status", "active")).lower(),
        coverages=tuple(item.get("coverages", ())),
    )


def _to_claim(item: Dict[str, Any]) -> Claim:
    return Claim(
        claim_id=str(item["claim_id"]),
        asset_id=str(item["asset_id"]),
        status=str(item.get("status", "open")).lower(),
    )


def analyze_insurance_coverage(
    assets: Iterable[Dict[str, Any]],
    policies: Iterable[Dict[str, Any]],
    claims: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    asset_rows = [_to_asset(item) for item in assets]
    active_policies = [_to_policy(item) for item in policies if str(item.get("status", "active")).lower() == "active"]
    claim_rows = [_to_claim(item) for item in claims]

    policies_by_asset: Dict[str, List[Policy]] = {}
    for policy in active_policies:
        policies_by_asset.setdefault(policy.asset_id, []).append(policy)

    open_claims_by_asset: Dict[str, int] = {}
    for claim in claim_rows:
        if claim.status == "open":
            open_claims_by_asset[claim.asset_id] = open_claims_by_asset.get(claim.asset_id, 0) + 1

    per_asset = []
    insured_total = 0.0
    uninsured_total = 0.0

    for asset in asset_rows:
        asset_policies = policies_by_asset.get(asset.asset_id, [])
        covered_value = min(asset.value_eur, sum(p.covered_value_eur for p in asset_policies))
        uninsured_value = max(0.0, asset.value_eur - covered_value)

        provided_coverages = {coverage for policy in asset_policies for coverage in policy.coverages}
        missing_coverages = sorted(set(asset.required_coverages) - provided_coverages)

        coverage_gaps = []
        if not asset_policies:
            coverage_gaps.append("no_active_policy")
        if uninsured_value > 0:
            coverage_gaps.append("underinsured_value")
        if missing_coverages:
            coverage_gaps.append("missing_required_coverages")

        insured_total += covered_value
        uninsured_total += uninsured_value

        per_asset.append(
            {
                "asset_id": asset.asset_id,
                "name": asset.name,
                "asset_value_eur": asset.value_eur,
                "insured_value_eur": covered_value,
                "uninsured_value_eur": uninsured_value,
                "premium_total_eur": sum(p.premium_eur for p in asset_policies),
                "open_claims_count": open_claims_by_asset.get(asset.asset_id, 0),
                "coverage_gaps": coverage_gaps,
                "missing_coverages": missing_coverages,
                "is_fully_insured": not coverage_gaps,
            }
        )

    return {
        "insured_value_eur": insured_total,
        "uninsured_value_eur": uninsured_total,
        "premium_total_eur": sum(policy.premium_eur for policy in active_policies),
        "open_claims_count": sum(1 for claim in claim_rows if claim.status == "open"),
        "coverage_gaps": [row["asset_id"] for row in per_asset if row["coverage_gaps"]],
        "assets": per_asset,
    }
# [CRUX-MK]
