#!/usr/bin/env python3
"""
DF-150 KPM Insurance Coverage Tracker (Core).
Per-Asset-Insurance-Status-Tracking.
"""
from dataclasses import dataclass
from typing import List

__all__ = [
    "AssetInsurance",
    "create_asset",
    "uninsured_value",
    "coverage_gap",
    "is_fully_insured",
    "total_insured",
    "total_uninsured",
    "total_premium",
    "total_open_claims",
    "coverage_gaps",
    "report",
]


@dataclass
class AssetInsurance:
    """Represents the insurance status of a single asset."""

    asset_id: str
    total_value: float
    insured_value: float
    premium: float
    open_claims: int


def create_asset(
    asset_id: str,
    total_value: float,
    insured_value: float,
    premium: float,
    open_claims: int = 0,
) -> AssetInsurance:
    """Create a new asset insurance record."""
    return AssetInsurance(asset_id, total_value, insured_value, premium, open_claims)


def uninsured_value(asset: AssetInsurance) -> float:
    """Return the uninsured portion of the asset's value."""
    return max(0.0, asset.total_value - asset.insured_value)


def coverage_gap(asset: AssetInsurance) -> float:
    """Return the coverage gap (shortfall). Same as uninsured_value."""
    return max(0.0, asset.total_value - asset.insured_value)


def is_fully_insured(asset: AssetInsurance) -> bool:
    """Check if the asset is fully insured (no gap)."""
    return asset.insured_value >= asset.total_value


def total_insured(assets: List[AssetInsurance]) -> float:
    """Calculate total insured value across assets."""
    return sum(a.insured_value for a in assets)


def total_uninsured(assets: List[AssetInsurance]) -> float:
    """Calculate total uninsured value across assets."""
    return sum(uninsured_value(a) for a in assets)


def total_premium(assets: List[AssetInsurance]) -> float:
    """Calculate total premium across assets."""
    return sum(a.premium for a in assets)


def total_open_claims(assets: List[AssetInsurance]) -> int:
    """Calculate total open claims across assets."""
    return sum(a.open_claims for a in assets)


def coverage_gaps(assets: List[AssetInsurance]) -> List[AssetInsurance]:
    """Return list of assets with coverage gap > 0."""
    return [a for a in assets if coverage_gap(a) > 0]


def report(assets: List[AssetInsurance]) -> dict:
    """Generate a summary report of insurance coverage status."""
    return {
        "total_insured": total_insured(assets),
        "total_uninsured": total_uninsured(assets),
        "total_premium": total_premium(assets),
        "total_open_claims": total_open_claims(assets),
        "coverage_gap_count": len(coverage_gaps(assets)),
    }
# [CRUX-MK]
