from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class Claim:
    claim_id: str
    status: str

    def is_open(self) -> bool:
        return self.status.strip().lower() in {"open", "pending", "in_review"}


@dataclass(frozen=True)
class Asset:
    asset_id: str
    asset_type: str
    value_eur: float
    insured: bool
    covered_value_eur: float = 0.0
    premium_eur: float = 0.0
    claims: List[Claim] = field(default_factory=list)
    required_coverage_eur: Optional[float] = None

    def normalized_required_coverage(self) -> float:
        if self.required_coverage_eur is None:
            return max(self.value_eur, 0.0)
        return max(self.required_coverage_eur, 0.0)


def _money(value: float) -> float:
    return round(float(value), 2)


def asset_coverage_gap(asset: Asset) -> float:
    required = asset.normalized_required_coverage()
    covered = max(asset.covered_value_eur, 0.0) if asset.insured else 0.0
    return _money(max(required - covered, 0.0))


def build_insurance_status_report(assets: Iterable[Asset]) -> dict:
    asset_list = list(assets)

    insured_value_total = 0.0
    uninsured_value_total = 0.0
    premium_total = 0.0
    open_claims_count = 0
    coverage_gaps = []

    for asset in asset_list:
        covered = min(max(asset.covered_value_eur, 0.0), max(asset.value_eur, 0.0)) if asset.insured else 0.0
        uninsured = max(asset.value_eur - covered, 0.0)

        insured_value_total += covered
        uninsured_value_total += uninsured
        premium_total += max(asset.premium_eur, 0.0) if asset.insured else 0.0
        open_claims_count += sum(1 for claim in asset.claims if claim.is_open())

        gap = asset_coverage_gap(asset)
        if gap > 0:
            coverage_gaps.append(
                {
                    "asset_id": asset.asset_id,
                    "asset_type": asset.asset_type,
                    "gap_eur": gap,
                    "required_coverage_eur": _money(asset.normalized_required_coverage()),
                    "covered_value_eur": _money(covered),
                }
            )

    return {
        "insured_value_total_eur": _money(insured_value_total),
        "uninsured_value_total_eur": _money(uninsured_value_total),
        "premium_total_eur": _money(premium_total),
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "recommended_actions": [],
        "policy_automation_permitted": False,
    }
# [CRUX-MK]
