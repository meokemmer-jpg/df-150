"""DF-150 KPM Insurance Coverage Tracker (stdlib only).

Tracks per-asset insured/uninsured values, premium totals, open claims count
and coverage gaps. Never auto-buys or auto-cancels policies.
"""
from typing import Any, Dict, List, Optional
import itertools


def _validate_nonnegative(value: float, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


class InsuranceTracker:
    """Tracks assets, insurance coverage, premiums, claims and coverage gaps."""

    def __init__(self) -> None:
        self.assets: Dict[str, Dict[str, Any]] = {}
        self.claims: Dict[str, Dict[str, Any]] = {}
        self._claim_counter = itertools.count(1)

    def add_asset(
        self,
        asset_id: str,
        name: str,
        value_eur: float,
        insured_value_eur: float = 0.0,
        premium_eur: float = 0.0,
    ) -> str:
        """Add a new asset with its current insurance data."""
        if asset_id in self.assets:
            raise ValueError(f"Asset '{asset_id}' already exists")
        _validate_nonnegative(value_eur, "value_eur")
        _validate_nonnegative(insured_value_eur, "insured_value_eur")
        _validate_nonnegative(premium_eur, "premium_eur")
        if insured_value_eur > value_eur:
            raise ValueError("insured_value_eur cannot exceed value_eur")

        self.assets[asset_id] = {
            "name": name,
            "value_eur": float(value_eur),
            "insured_value_eur": float(insured_value_eur),
            "premium_eur": float(premium_eur),
        }
        return asset_id

    def update_insurance(
        self,
        asset_id: str,
        insured_value_eur: Optional[float] = None,
        premium_eur: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Manually update an asset's insured value or premium."""
        asset = self._get_asset(asset_id)

        if insured_value_eur is not None:
            _validate_nonnegative(insured_value_eur, "insured_value_eur")
            if insured_value_eur > asset["value_eur"]:
                raise ValueError("insured_value_eur cannot exceed value_eur")
        if premium_eur is not None:
            _validate_nonnegative(premium_eur, "premium_eur")

        if insured_value_eur is not None:
            asset["insured_value_eur"] = float(insured_value_eur)
        if premium_eur is not None:
            asset["premium_eur"] = float(premium_eur)

        return asset

    def add_claim(
        self,
        asset_id: str,
        amount_eur: float,
        claim_id: Optional[str] = None,
    ) -> str:
        """Register a new open claim for an asset."""
        self._get_asset(asset_id)
        _validate_nonnegative(amount_eur, "amount_eur")

        if claim_id is None:
            claim_id = f"CL-{next(self._claim_counter)}"
        if claim_id in self.claims:
            raise ValueError(f"Claim '{claim_id}' already exists")

        self.claims[claim_id] = {
            "asset_id": asset_id,
            "amount_eur": float(amount_eur),
            "open": True,
        }
        return claim_id

    def close_claim(self, claim_id: str) -> str:
        """Mark a claim as closed."""
        self._get_claim(claim_id)["open"] = False
        return claim_id

    def get_asset_status(self, asset_id: str) -> Dict[str, Any]:
        """Return per-asset insurance status."""
        asset = self._get_asset(asset_id)
        return {
            "asset_id": asset_id,
            "name": asset["name"],
            "value_eur": asset["value_eur"],
            "insured_value_eur": asset["insured_value_eur"],
            "uninsured_value_eur": asset["value_eur"] - asset["insured_value_eur"],
            "premium_eur": asset["premium_eur"],
        }

    def coverage_gaps(self) -> List[Dict[str, Any]]:
        """Return all assets where insured value is below asset value."""
        gaps = []
        for asset_id in sorted(self.assets):
            asset = self.assets[asset_id]
            gap = asset["value_eur"] - asset["insured_value_eur"]
            if gap > 0:
                gaps.append({"asset_id": asset_id, "gap_eur": gap})
        return gaps

    def status(self) -> Dict[str, Any]:
        """Return aggregate KPM insurance tracking status."""
        total_value = sum(asset["value_eur"] for asset in self.assets.values())
        insured_value = sum(asset["insured_value_eur"] for asset in self.assets.values())
        premium_total = sum(asset["premium_eur"] for asset in self.assets.values())
        open_claims_count = sum(1 for claim in self.claims.values() if claim["open"])

        return {
            "total_value_eur": total_value,
            "insured_value_eur": insured_value,
            "uninsured_value_eur": total_value - insured_value,
            "premium_total_eur": premium_total,
            "open_claims_count": open_claims_count,
            "coverage_gaps": self.coverage_gaps(),
        }

    def _get_asset(self, asset_id: str) -> Dict[str, Any]:
        if asset_id not in self.assets:
            raise KeyError(f"Unknown asset '{asset_id}'")
        return self.assets[asset_id]

    def _get_claim(self, claim_id: str) -> Dict[str, Any]:
        if claim_id not in self.claims:
            raise KeyError(f"Unknown claim '{claim_id}'")
        return self.claims[claim_id]
# [CRUX-MK]
