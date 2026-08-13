#!/usr/bin/env python3
"""DF-150 KPM-Insurance-Coverage [CRUX-MK] - Per-Asset-Insurance-Status-Tracking.

Constraints:
  - NEVER auto-buy or auto-cancel policies.
  - This module only records and reports insurance coverage status.
"""

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Asset:
    asset_id: str
    value_eur: float
    insured: bool = False
    premium_eur: float = 0.0

    def __post_init__(self) -> None:
        if self.value_eur < 0:
            raise ValueError("value_eur must be >= 0")
        if self.premium_eur < 0:
            raise ValueError("premium_eur must be >= 0")
        if not self.insured and self.premium_eur != 0.0:
            raise ValueError("an uninsured asset cannot carry a premium")


@dataclass
class InsuranceTracker:
    assets: Dict[str, Asset] = field(default_factory=dict)
    _open_claims: int = 0

    def add_asset(
        self,
        asset_id: str,
        value_eur: float,
        insured: bool = False,
        premium_eur: float = 0.0,
    ) -> Asset:
        """Register an asset with its current insurance status."""
        if not asset_id:
            raise ValueError("asset_id must not be empty")
        if asset_id in self.assets:
            raise KeyError(f"asset {asset_id!r} already exists")
        asset = Asset(
            asset_id=asset_id,
            value_eur=value_eur,
            insured=insured,
            premium_eur=premium_eur,
        )
        self.assets[asset_id] = asset
        return asset

    def record_insurance_status(
        self, asset_id: str, insured: bool, premium_eur: float = 0.0
    ) -> None:
        """Manually record a policy status change. No automatic buy/cancel."""
        if asset_id not in self.assets:
            raise KeyError(f"unknown asset {asset_id!r}")
        if premium_eur < 0:
            raise ValueError("premium_eur must be >= 0")
        if not insured and premium_eur != 0.0:
            raise ValueError("an uninsured asset cannot carry a premium")
        asset = self.assets[asset_id]
        asset.insured = insured
        asset.premium_eur = premium_eur if insured else 0.0

    def register_claim(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self._open_claims += count

    def settle_claim(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self._open_claims = max(0, self._open_claims - count)

    @property
    def open_claims_count(self) -> int:
        return self._open_claims

    def insured_value_eur(self) -> float:
        return sum(a.value_eur for a in self.assets.values() if a.insured)

    def uninsured_value_eur(self) -> float:
        return sum(a.value_eur for a in self.assets.values() if not a.insured)

    def premium_total_eur(self) -> float:
        return sum(a.premium_eur for a in self.assets.values() if a.insured)

    def coverage_gaps(self) -> List[str]:
        """Return IDs of uninsured assets with positive value."""
        return [
            a.asset_id
            for a in self.assets.values()
            if not a.insured and a.value_eur > 0
        ]

    def asset_statuses(self) -> List[dict]:
        return [
            {
                "asset_id": a.asset_id,
                "value_eur": a.value_eur,
                "insured": a.insured,
                "premium_eur": a.premium_eur,
            }
            for a in self.assets.values()
        ]

    def report(self) -> dict:
        return {
            "insured_value_eur": self.insured_value_eur(),
            "uninsured_value_eur": self.uninsured_value_eur(),
            "premium_total_eur": self.premium_total_eur(),
            "open_claims_count": self.open_claims_count,
            "coverage_gaps": self.coverage_gaps(),
            "assets": self.asset_statuses(),
        }

    def write_report(self, path: Optional[Path] = None) -> Path:
        target = (
            Path(path)
            if path is not None
            else Path("reports") / f"df-150-{date.today().isoformat()}.json"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.report(), indent=2), encoding="utf-8")
        return target


if __name__ == "__main__":
    tracker = InsuranceTracker()
    tracker.add_asset("DE0001", 100_000.0)
    tracker.add_asset("DE0002", 250_000.0, insured=True, premium_eur=1_250.0)
    tracker.add_asset("DE0003", 50_000.0)
    print(json.dumps(tracker.report(), indent=2))
# [CRUX-MK]
