"""
Dark Factory df-150: KPM Insurance Coverage Tracking (Core)

Per-asset status, insured/uninsured values, premium total,
open claims count, coverage gaps. No auto-buy/cancel.
"""
import datetime
from typing import List, Dict, Optional, Any


class Asset:
    """Single asset with insurance-related data."""
    def __init__(self, asset_id: str, value: float):
        self.asset_id = asset_id
        self.value = value
        self.insured = False
        self.premium = 0.0
        self.open_claims = 0
        self.insured_from: Optional[datetime.date] = None
        self.insured_until: Optional[datetime.date] = None

    def __repr__(self):
        return (f"Asset({self.asset_id!r}, value={self.value}, "
                f"insured={self.insured})")


class AssetInsuranceTracker:
    """Tracks insurance status for a collection of assets."""

    def __init__(self):
        self.assets: Dict[str, Asset] = {}

    def add_asset(self, asset_id: str, value: float,
                  insured: bool = False, premium: float = 0.0,
                  open_claims: int = 0,
                  insured_from: Optional[datetime.date] = None,
                  insured_until: Optional[datetime.date] = None):
        """Register a new asset with optional insurance parameters."""
        asset = Asset(asset_id, value)
        asset.insured = insured
        asset.premium = premium
        asset.open_claims = open_claims
        asset.insured_from = insured_from
        asset.insured_until = insured_until
        self.assets[asset_id] = asset

    def update_insurance(self, asset_id: str,
                         insured: Optional[bool] = None,
                         premium: Optional[float] = None,
                         open_claims: Optional[int] = None,
                         insured_from: Optional[datetime.date] = None,
                         insured_until: Optional[datetime.date] = None):
        """Change insurance fields of an existing asset."""
        if asset_id not in self.assets:
            raise KeyError(f"Asset {asset_id} not found")
        asset = self.assets[asset_id]
        if insured is not None:
            asset.insured = insured
        if premium is not None:
            asset.premium = premium
        if open_claims is not None:
            asset.open_claims = open_claims
        if insured_from is not None:
            asset.insured_from = insured_from
        if insured_until is not None:
            asset.insured_until = insured_until

    def get_insured_value(self) -> float:
        """Total value of insured assets (EUR)."""
        return sum(a.value for a in self.assets.values() if a.insured)

    def get_uninsured_value(self) -> float:
        """Total value of uninsured assets (EUR)."""
        return sum(a.value for a in self.assets.values() if not a.insured)

    def get_total_premium(self) -> float:
        """Sum of all recorded premiums (EUR)."""
        return sum(a.premium for a in self.assets.values())

    def get_open_claims_count(self) -> int:
        """Total number of open claims."""
        return sum(a.open_claims for a in self.assets.values())

    def get_coverage_gaps(self) -> List[Asset]:
        """Assets with a coverage gap (value > 0 and not insured)."""
        return [a for a in self.assets.values() if a.value > 0 and not a.insured]

    def generate_report(self) -> Dict[str, Any]:
        """Produce a summary report dictionary (today's date)."""
        today = datetime.date.today().isoformat()
        return {
            "report_date": today,
            "insured_value_eur": self.get_insured_value(),
            "uninsured_value_eur": self.get_uninsured_value(),
            "premium_total_eur": self.get_total_premium(),
            "open_claims_count": self.get_open_claims_count(),
            "coverage_gaps": [a.asset_id for a in self.get_coverage_gaps()],
        }
# [CRUX-MK]
