"""DF-150 KPM insurance coverage tracker (CRUX-MK)."""

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Asset:
    asset_id: str
    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("asset value must be >= 0")


@dataclass(frozen=True)
class Policy:
    policy_id: str
    asset_id: str
    coverage_amount: float
    premium: float

    def __post_init__(self) -> None:
        if self.coverage_amount < 0:
            raise ValueError("coverage_amount must be >= 0")
        if self.premium < 0:
            raise ValueError("premium must be >= 0")


@dataclass(frozen=True)
class Claim:
    claim_id: str
    asset_id: str
    status: str = "open"

    def __post_init__(self) -> None:
        if not self.status:
            raise ValueError("claim status must not be empty")


@dataclass(frozen=True)
class AssetStatus:
    asset_id: str
    asset_value: float
    covered_value: float
    uncovered_value: float
    coverage_percent: float
    status: str
    policies: Tuple[Tuple[str, float, float], ...] = ()

    @property
    def has_coverage_gap(self) -> bool:
        return self.uncovered_value > 0


def calculate_asset_status(asset: Asset, policies: List[Policy]) -> AssetStatus:
    matching = [p for p in policies if p.asset_id == asset.asset_id]
    coverage = sum(p.coverage_amount for p in matching)
    covered = min(asset.value, coverage)
    uncovered = max(0.0, asset.value - coverage)

    if coverage <= 0:
        status = "uninsured"
    elif uncovered <= 0:
        status = "insured"
    else:
        status = "partial"

    return AssetStatus(
        asset_id=asset.asset_id,
        asset_value=asset.value,
        covered_value=covered,
        uncovered_value=uncovered,
        coverage_percent=covered / asset.value if asset.value else 0.0,
        status=status,
        policies=tuple((p.policy_id, p.coverage_amount, p.premium) for p in matching),
    )


def calculate_insured_uninsured_values(
    assets: List[Asset], policies: List[Policy]
) -> Tuple[float, float]:
    insured = 0.0
    uninsured = 0.0
    for asset in assets:
        status = calculate_asset_status(asset, policies)
        insured += status.covered_value
        uninsured += status.uncovered_value
    return insured, uninsured


def calculate_premium_total(policies: List[Policy]) -> float:
    return sum(p.premium for p in policies)


def calculate_open_claims_count(claims: List[Claim]) -> int:
    return sum(1 for c in claims if c.status.strip().lower() != "closed")


class InsuranceTracker:
    def __init__(self) -> None:
        self._assets: Dict[str, Asset] = {}
        self._policies: List[Policy] = []
        self._claims: List[Claim] = []

    def register_asset(self, asset_id: str, value: float) -> Asset:
        asset = Asset(asset_id, value)
        self._assets[asset_id] = asset
        return asset

    def register_policy(
        self,
        policy_id: str,
        asset_id: str,
        coverage_amount: float,
        premium: float,
    ) -> Policy:
        if asset_id not in self._assets:
            raise KeyError(f"unknown asset: {asset_id}")
        policy = Policy(policy_id, asset_id, coverage_amount, premium)
        self._policies.append(policy)
        return policy

    def register_claim(
        self, claim_id: str, asset_id: str, status: str = "open"
    ) -> Claim:
        if asset_id not in self._assets:
            raise KeyError(f"unknown asset: {asset_id}")
        claim = Claim(claim_id, asset_id, status)
        self._claims.append(claim)
        return claim

    def asset_status(self, asset_id: str) -> AssetStatus:
        if asset_id not in self._assets:
            raise KeyError(f"unknown asset: {asset_id}")
        return calculate_asset_status(self._assets[asset_id], self._policies)

    def insured_uninsured_values(self) -> Tuple[float, float]:
        return calculate_insured_uninsured_values(
            list(self._assets.values()), self._policies
        )

    def premium_total(self) -> float:
        return calculate_premium_total(self._policies)

    def open_claims_count(self) -> int:
        return calculate_open_claims_count(self._claims)

    def coverage_gaps(self) -> List[AssetStatus]:
        gaps = []
        for asset_id in self._assets:
            status = self.asset_status(asset_id)
            if status.has_coverage_gap:
                gaps.append(status)
        return gaps

    def summary(self) -> Dict[str, object]:
        insured, uninsured = self.insured_uninsured_values()
        return {
            "insured_value": insured,
            "uninsured_value": uninsured,
            "premium_total": self.premium_total(),
            "open_claims": self.open_claims_count(),
            "coverage_gaps": len(self.coverage_gaps()),
        }

    def report(self, report_date: str = "") -> Dict[str, object]:
        day = report_date or date.today().isoformat()
        return {
            "schema": "df-150-kpm-insurance-coverage-1.0",
            "date": day,
            **self.summary(),
            "assets": [
                {
                    "asset_id": status.asset_id,
                    "value": status.asset_value,
                    "covered_value": status.covered_value,
                    "uncovered_value": status.uncovered_value,
                    "status": status.status,
                }
                for status in (self.asset_status(aid) for aid in self._assets)
            ],
        }
# [CRUX-MK]
