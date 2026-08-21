"""DF-150 KPM-Insurance-Coverage core tracker (stdlib only)."""
from __future__ import annotations

import datetime
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

class InsuranceError(Exception):
    """Raised when an insurance tracking operation is invalid."""

@dataclass(frozen=True)
class Asset:
    asset_id: str
    value_eur: float
    insured_value_eur: float = 0.0
    premium_eur: float = 0.0
    open_claims: int = 0

    def __post_init__(self) -> None:
        if self.value_eur < 0:
            raise InsuranceError("value_eur must be >= 0")
        if self.insured_value_eur < 0:
            raise InsuranceError("insured_value_eur must be >= 0")
        if self.insured_value_eur > self.value_eur:
            raise InsuranceError("insured_value_eur cannot exceed value_eur")
        if self.premium_eur < 0:
            raise InsuranceError("premium_eur must be >= 0")
        if self.open_claims < 0:
            raise InsuranceError("open_claims must be >= 0")

    @property
    def uninsured_value_eur(self) -> float:
        return self.value_eur - self.insured_value_eur

    @property
    def has_coverage_gap(self) -> bool:
        return self.uninsured_value_eur > 0


class DF150Tracker:
    """Tracks per-asset insurance status for KPM."""

    def __init__(self) -> None:
        self._assets: Dict[str, Asset] = {}

    def add_asset(
        self,
        asset_id: str,
        value_eur: float,
        insured_value_eur: float = 0.0,
        premium_eur: float = 0.0,
        open_claims: int = 0,
    ) -> Asset:
        if asset_id in self._assets:
            raise InsuranceError(f"asset already exists: {asset_id}")
        asset = Asset(asset_id, value_eur, insured_value_eur, premium_eur, open_claims)
        self._assets[asset_id] = asset
        return asset

    def update_asset(
        self,
        asset_id: str,
        *,
        value_eur: Optional[float] = None,
        insured_value_eur: Optional[float] = None,
        premium_eur: Optional[float] = None,
    ) -> Asset:
        """Manually update asset values/insurance. No automatic policy actions."""
        old = self._get_asset(asset_id)
        asset = Asset(
            asset_id=asset_id,
            value_eur=old.value_eur if value_eur is None else value_eur,
            insured_value_eur=old.insured_value_eur if insured_value_eur is None else insured_value_eur,
            premium_eur=old.premium_eur if premium_eur is None else premium_eur,
            open_claims=old.open_claims,
        )
        self._assets[asset_id] = asset
        return asset

    def get_asset(self, asset_id: str) -> Asset:
        return self._get_asset(asset_id)

    def _get_asset(self, asset_id: str) -> Asset:
        try:
            return self._assets[asset_id]
        except KeyError as exc:
            raise InsuranceError(f"unknown asset: {asset_id}") from exc

    def open_claim(self, asset_id: str) -> Asset:
        old = self._get_asset(asset_id)
        asset = Asset(
            old.asset_id,
            old.value_eur,
            old.insured_value_eur,
            old.premium_eur,
            old.open_claims + 1,
        )
        self._assets[asset_id] = asset
        return asset

    def settle_claim(self, asset_id: str) -> Asset:
        old = self._get_asset(asset_id)
        if old.open_claims == 0:
            raise InsuranceError(f"no open claims for asset: {asset_id}")
        asset = Asset(
            old.asset_id,
            old.value_eur,
            old.insured_value_eur,
            old.premium_eur,
            old.open_claims - 1,
        )
        self._assets[asset_id] = asset
        return asset

    @property
    def assets(self) -> List[Asset]:
        return list(self._assets.values())

    def total_asset_value(self) -> float:
        return sum(a.value_eur for a in self._assets.values())

    def insured_value_total(self) -> float:
        return sum(a.insured_value_eur for a in self._assets.values())

    def uninsured_value_total(self) -> float:
        return sum(a.uninsured_value_eur for a in self._assets.values())

    def premium_total(self) -> float:
        return sum(a.premium_eur for a in self._assets.values())

    def open_claims_count(self) -> int:
        return sum(a.open_claims for a in self._assets.values())

    def coverage_gaps(self) -> List[Asset]:
        return [a for a in self._assets.values() if a.has_coverage_gap]

    def report(self) -> dict:
        return {
            "insured_total_eur": self.insured_value_total(),
            "uninsured_total_eur": self.uninsured_value_total(),
            "total_asset_value_eur": self.total_asset_value(),
            "premium_total_eur": self.premium_total(),
            "open_claims_count": self.open_claims_count(),
            "coverage_gaps": [a.asset_id for a in self.coverage_gaps()],
            "assets": [self._asset_to_dict(a) for a in self._assets.values()],
        }

    @staticmethod
    def _asset_to_dict(a: Asset) -> dict:
        return {
            "asset_id": a.asset_id,
            "value_eur": a.value_eur,
            "insured_value_eur": a.insured_value_eur,
            "uninsured_value_eur": a.uninsured_value_eur,
            "premium_eur": a.premium_eur,
            "open_claims": a.open_claims,
        }

    def write_report(self, path: Optional[str] = None) -> str:
        if path is None:
            path = os.path.join(
                "reports",
                f"df-150-{datetime.date.today().isoformat()}.json",
            )
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.report(), fh, indent=2)
        return path


__all__ = ["DF150Tracker", "Asset", "InsuranceError"]
# [CRUX-MK]
