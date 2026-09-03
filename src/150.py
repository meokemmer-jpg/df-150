"""df-150 - KPM Insurance Coverage Tracking (CRUX-MK core).

Per-asset insurance status tracking for the KPM family wealth-protection
domain (K_0, Welle 25).

Tracks, per asset and in aggregate:
  * insured / uninsured asset values (EUR)
  * premium totals (EUR)
  * open claims counts
  * coverage gaps

HARD SAFETY RULE: this module ONLY tracks and flags. It NEVER performs
auto-policy-buy and NEVER performs auto-policy-cancel. Every
recommendation it emits is advisory-only (``auto=False``) and the
report's ``auto_policy_actions`` list is empty by construction.

stdlib only.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

FACTORY = "df-150"
DOMAIN = "K_0"
WELLE = 25
STOP_FLAG_PATH = "/tmp/df-150.stop"
OPEN_CLAIM_STATUS = "open"

#: Operations this factory is forbidden to perform. Enforced by
#: construction: nothing in this module ever executes them; reports only
#: carry advisory flags.
FORBIDDEN_ACTIONS = (
    "auto-policy-buy",
    "auto-policy-cancel",
    "policy-buy",
    "policy-cancel",
)


@dataclass(frozen=True)
class Asset:
    """One KPM asset with its insurance state (immutable by design)."""

    asset_id: str
    value_eur: float
    insured_value_eur: float = 0.0
    premium_eur: float = 0.0
    claims: Sequence[Mapping[str, str]] = ()

    @property
    def uninsured_value_eur(self) -> float:
        return round(max(0.0, self.value_eur - self.insured_value_eur), 2)

    @property
    def open_claims(self) -> int:
        return sum(
            1
            for claim in self.claims
            if str(claim.get("status", "")).lower() == OPEN_CLAIM_STATUS
        )


@dataclass(frozen=True)
class CoverageSummary:
    """Aggregate insurance status across all tracked assets."""

    total_asset_value_eur: float
    insured_value_eur: float
    uninsured_value_eur: float
    premium_total_eur: float
    open_claims_count: int
    coverage_gap_count: int
    coverage_gap_value_eur: float
    coverage_ratio: float

    def to_dict(self) -> Dict:
        return asdict(self)


def track_assets(assets: Iterable[Asset]) -> CoverageSummary:
    """Aggregate per-asset insurance status (read-only, pure)."""
    assets = tuple(assets)
    total_value = round(sum(a.value_eur for a in assets), 2)
    insured = round(sum(a.insured_value_eur for a in assets), 2)
    uninsured = round(sum(a.uninsured_value_eur for a in assets), 2)
    premiums = round(sum(a.premium_eur for a in assets), 2)
    open_claims = sum(a.open_claims for a in assets)
    gaps = [a for a in assets if a.uninsured_value_eur > 0]
    gap_value = round(sum(a.uninsured_value_eur for a in gaps), 2)
    ratio = (insured / total_value) if total_value > 0 else 0.0
    return CoverageSummary(
        total_asset_value_eur=total_value,
        insured_value_eur=insured,
        uninsured_value_eur=uninsured,
        premium_total_eur=premiums,
        open_claims_count=open_claims,
        coverage_gap_count=len(gaps),
        coverage_gap_value_eur=gap_value,
        coverage_ratio=ratio,
    )


def coverage_gaps(assets: Iterable[Asset]) -> List[Dict]:
    """Flag every asset whose insured value does not cover its full value.

    Advisory only: ``recommendation.auto`` is ALWAYS False and
    ``recommendation.action`` is ALWAYS ``"review-manually"`` -- never a
    buy or cancel instruction.
    """
    gaps: List[Dict] = []
    for a in assets:
        if a.uninsured_value_eur > 0:
            gaps.append(
                {
                    "asset_id": a.asset_id,
                    "value_eur": a.value_eur,
                    "insured_value_eur": a.insured_value_eur,
                    "uninsured_value_eur": a.uninsured_value_eur,
                    "recommendation": {
                        "action": "review-manually",
                        "auto": False,
                    },
                }
            )
    return gaps


def build_report(assets: Iterable[Asset]) -> Dict:
    """Build the full df-150 report dict (JSON-serialisable)."""
    assets = tuple(assets)
    summary = track_assets(assets)
    return {
        "factory": FACTORY,
        "domain": DOMAIN,
        "welle": WELLE,
        "generated_on": date.today().isoformat(),
        "mode": "track-only",
        "summary": summary.to_dict(),
        "assets": [
            {
                "asset_id": a.asset_id,
                "value_eur": a.value_eur,
                "insured_value_eur": a.insured_value_eur,
                "uninsured_value_eur": a.uninsured_value_eur,
                "premium_eur": a.premium_eur,
                "open_claims": a.open_claims,
                "claims": [dict(c) for c in a.claims],
            }
            for a in assets
        ],
        "coverage_gaps": coverage_gaps(assets),
        # By construction this list is empty and MUST stay empty.
        "auto_policy_actions": [],
    }


def stop_requested(stop_path: str = STOP_FLAG_PATH) -> bool:
    """True if the df-150 STOP flag file exists."""
    return os.path.exists(stop_path)


def write_report(report: Mapping, reports_dir: str = "reports") -> str:
    """Persist the report as reports/df-150-{date}.json; return its path."""
    out_dir = Path(reports_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{FACTORY}-{date.today().isoformat()}.json"
    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
    return str(out_file)


# --- Mock-mode entry point (default when run as a script) ----------------

MOCK_ASSETS = (
    Asset(
        "family-home",
        1_250_000.0,
        insured_value_eur=1_000_000.0,
        premium_eur=2_400.0,
        claims=({"status": "open"}, {"status": "closed"}),
    ),
    Asset(
        "bond-portfolio",
        500_000.0,
        insured_value_eur=500_000.0,
        premium_eur=900.0,
    ),
    Asset(
        "art-collection",
        220_000.0,
        insured_value_eur=0.0,
        premium_eur=0.0,
        claims=({"status": "open"},),
    ),
)


def main() -> int:
    if stop_requested():
        print("df-150: STOP flag set - aborting before tracking.")
        return 1
    report = build_report(MOCK_ASSETS)
    path = write_report(report)
    print(f"df-150 report written: {path}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# [CRUX-MK]
