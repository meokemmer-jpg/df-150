"""df-150 core: per-asset insurance status tracking for KPM (Domain K_0).

Read-only analytics over an asset portfolio:
    * insured / uninsured asset values (EUR)
    * premium total (EUR)
    * open claims count
    * coverage gaps (per-asset, ranked)

Hard guarantee: this module NEVER buys or cancels policies.
"""

from dataclasses import dataclass, asdict
from datetime import date


@dataclass(frozen=True)
class Asset:
    name: str
    value_eur: float
    insured_value_eur: float = 0.0
    premium_eur: float = 0.0
    open_claims: int = 0


@dataclass(frozen=True)
class CoverageGap:
    asset: str
    gap_eur: float
    severity: float  # gap/value ratio; 1.0 == completely uninsured


_ALIASES = {
    "name": ("name",),
    "value_eur": ("value_eur", "value"),
    "insured_value_eur": ("insured_value_eur", "insured_value", "insured"),
    "premium_eur": ("premium_eur", "premium"),
    "open_claims": ("open_claims", "claims"),
}


def _coerce(record):
    """Accept Asset instances or plain dicts (with lenient key aliases)."""
    if isinstance(record, Asset):
        return record
    if not isinstance(record, dict):
        raise TypeError(f"asset record must be Asset or dict, got {type(record)!r}")
    kwargs = {}
    for field, aliases in _ALIASES.items():
        for alias in aliases:
            if alias in record:
                kwargs[field] = record[alias]
                break
    if "name" not in kwargs:
        raise KeyError("asset record must provide a 'name'")
    return Asset(**kwargs)


def coverage_gaps(assets):
    """All assets where insured value < asset value, biggest gap first."""
    gaps = []
    for record in assets:
        a = _coerce(record)
        gap = a.value_eur - a.insured_value_eur
        if gap > 0:
            severity = gap / a.value_eur if a.value_eur > 0 else 1.0
            gaps.append(CoverageGap(asset=a.name,
                                    gap_eur=round(gap, 2),
                                    severity=round(severity, 4)))
    return sorted(gaps, key=lambda g: (-g.gap_eur, g.asset))


def summarize(assets):
    """Aggregate insurance status for a portfolio (JSON-safe dict)."""
    items = [_coerce(r) for r in assets]
    total = sum(a.value_eur for a in items)
    insured = sum(a.insured_value_eur for a in items)
    gaps = coverage_gaps(items)
    ratio = insured / total if total > 0 else 1.0
    return {
        "asset_count": len(items),
        "total_value_eur": round(total, 2),
        "insured_value_eur": round(insured, 2),
        "uninsured_value_eur": round(total - insured, 2),
        "premium_total_eur": round(sum(a.premium_eur for a in items), 2),
        "open_claims": sum(a.open_claims for a in items),
        "coverage_gap_count": len(gaps),
        "coverage_gaps_eur": round(sum(g.gap_eur for g in gaps), 2),
        "coverage_ratio": round(ratio, 4),
        "gaps": [asdict(g) for g in gaps],
    }


def build_report(assets, report_date=None):
    """Sketch of the df-150 daily report payload (never touching policies)."""
    return {
        "mission": "df-150-kpm-insurance-coverage",
        "date": (report_date or date.today()).isoformat(),
        "policy_action": "none-read-only",
        "summary": summarize(assets),
    }
# [CRUX-MK]
