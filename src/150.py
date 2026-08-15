"""df-150 KPM insurance coverage tracking.

This module is deliberately read-only with respect to insurance policies:
it NEVER buys or cancels a policy. It only derives aggregate status from
the supplied assets, policies, and claims.
"""

from dataclasses import dataclass
from typing import List, Sequence, Set, Tuple

AUTO_POLICY_BUY_OR_CANCEL_ENABLED = False


@dataclass(frozen=True)
class Asset:
    asset_id: str
    value_eur: float


@dataclass(frozen=True)
class Policy:
    policy_id: str
    asset_id: str
    premium_eur: float
    active: bool = True


@dataclass(frozen=True)
class Claim:
    claim_id: str
    asset_id: str
    status: str = "OPEN"


@dataclass(frozen=True)
class InsuranceStatusReport:
    insured_value_eur: float
    uninsured_value_eur: float
    premium_total_eur: float
    open_claims_count: int
    coverage_gaps: List[Asset]


def _active_policies(policies: Sequence[Policy]) -> List[Policy]:
    return [p for p in policies if p.active]


def insured_asset_ids(policies: Sequence[Policy]) -> Set[str]:
    return {p.asset_id for p in _active_policies(policies)}


def compute_insured_uninsured(
    assets: Sequence[Asset], policies: Sequence[Policy]
) -> Tuple[float, float]:
    insured_ids = insured_asset_ids(policies)
    insured_value = 0.0
    uninsured_value = 0.0

    for asset in assets:
        if asset.asset_id in insured_ids:
            insured_value += asset.value_eur
        else:
            uninsured_value += asset.value_eur

    return insured_value, uninsured_value


def compute_premium_total(policies: Sequence[Policy]) -> float:
    return float(sum(p.premium_eur for p in _active_policies(policies)))


def count_open_claims(claims: Sequence[Claim]) -> int:
    return sum(1 for claim in claims if str(claim.status).upper() == "OPEN")


def find_coverage_gaps(
    assets: Sequence[Asset], policies: Sequence[Policy]
) -> List[Asset]:
    insured_ids = insured_asset_ids(policies)
    return [asset for asset in assets if asset.asset_id not in insured_ids]


def build_status_report(
    assets: Sequence[Asset],
    policies: Sequence[Policy],
    claims: Sequence[Claim],
) -> InsuranceStatusReport:
    insured_value, uninsured_value = compute_insured_uninsured(assets, policies)

    return InsuranceStatusReport(
        insured_value_eur=insured_value,
        uninsured_value_eur=uninsured_value,
        premium_total_eur=compute_premium_total(policies),
        open_claims_count=count_open_claims(claims),
        coverage_gaps=find_coverage_gaps(assets, policies),
    )
# [CRUX-MK]
