"""df-150 — KPM Insurance-Coverage [CRUX-MK].

Domain K_0 (KPM Familien-Vermoegen-Schutz), Welle 25.

Per-asset insurance status tracking:
  * insured / uninsured asset values (EUR)
  * premium total (EUR)
  * open claims count
  * coverage gaps

NIEMALS auto-policy-buy, NIEMALS auto-policy-cancel: this engine only
tracks, assesses and reports. Any buy/cancel action raises
AutoPolicyActionForbidden.

Stdlib only. Mock mode is the default (run_engine(mock=True), main()).
Output:  reports/df-150-{date}.json
STOP flag: /tmp/df-150.stop
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Optional, Union

MODULE_ID = "df-150"
MISSION = "KPM-Insurance-Coverage"
DOMAIN = "K_0"
DEFAULT_REPORTS_DIR = "reports"
DEFAULT_STOP_FLAG = Path("/tmp/df-150.stop")

# NIEMALS-clause: this engine can never execute these policy actions.
FORBIDDEN_POLICY_ACTIONS = frozenset({
    "buy", "cancel",
    "auto_buy", "auto_cancel", "auto-buy", "auto-cancel",
    "buy_policy", "cancel_policy",
})


class AutoPolicyActionForbidden(RuntimeError):
    """Raised when an auto-policy buy/cancel is attempted (NIEMALS clause)."""


@dataclass(frozen=True)
class Asset:
    """One tracked asset of the KPM family portfolio."""

    asset_id: str
    value_eur: float
    insured_value_eur: float = 0.0
    premium_eur: float = 0.0
    open_claims: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.asset_id, str) or not self.asset_id.strip():
            raise ValueError("asset_id must be a non-empty string")
        for field in ("value_eur", "insured_value_eur", "premium_eur"):
            val = getattr(self, field)
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise ValueError(f"{field} must be a number, got {val!r}")
            if val < 0:
                raise ValueError(f"{field} must be >= 0, got {val}")
        if isinstance(self.open_claims, bool) or not isinstance(self.open_claims, int):
            raise ValueError(f"open_claims must be an int, got {self.open_claims!r}")
        if self.open_claims < 0:
            raise ValueError(f"open_claims must be >= 0, got {self.open_claims}")


AssetInput = Union[Asset, Mapping[str, Any]]


@dataclass(frozen=True)
class AssetAssessment:
    """Computed per-asset insurance status."""

    asset_id: str
    value_eur: float
    insured_value_eur: float
    uninsured_value_eur: float
    premium_eur: float
    open_claims: int
    coverage_ratio: float
    has_coverage_gap: bool


def to_asset(data: AssetInput) -> Asset:
    """Accept an Asset or a plain mapping and return a validated Asset."""
    if isinstance(data, Asset):
        return data
    if isinstance(data, Mapping):
        return Asset(**dict(data))
    raise TypeError(f"cannot coerce {type(data).__name__} to Asset")


def assess_asset(asset: AssetInput) -> AssetAssessment:
    """Compute insured/uninsured split, coverage ratio and gap for one asset."""
    a = to_asset(asset)
    uninsured = max(0.0, float(a.value_eur) - float(a.insured_value_eur))
    if a.value_eur > 0:
        ratio = min(float(a.insured_value_eur), float(a.value_eur)) / float(a.value_eur)
    else:
        ratio = 1.0  # nothing to insure
    return AssetAssessment(
        asset_id=a.asset_id,
        value_eur=round(float(a.value_eur), 2),
        insured_value_eur=round(float(a.insured_value_eur), 2),
        uninsured_value_eur=round(uninsured, 2),
        premium_eur=round(float(a.premium_eur), 2),
        open_claims=a.open_claims,
        coverage_ratio=round(ratio, 4),
        has_coverage_gap=uninsured > 0,
    )


def build_coverage_report(
    assets: Iterable[AssetInput],
    report_date: Optional[date] = None,
) -> dict:
    """Aggregate per-asset assessments into the df-150 coverage report."""
    assessments = [assess_asset(a) for a in assets]
    day = report_date if report_date is not None else date.today()

    total_value = sum(a.value_eur for a in assessments)
    insured = sum(a.insured_value_eur for a in assessments)
    uninsured = sum(a.uninsured_value_eur for a in assessments)
    premium_total = sum(a.premium_eur for a in assessments)
    open_claims = sum(a.open_claims for a in assessments)
    gaps = [a.asset_id for a in assessments if a.has_coverage_gap]
    ratio = (min(insured, total_value) / total_value) if total_value > 0 else 1.0

    return {
        "module": MODULE_ID,
        "mission": MISSION,
        "domain": DOMAIN,
        "date": day.isoformat(),
        "asset_count": len(assessments),
        "total_value_eur": round(total_value, 2),
        "insured_value_eur": round(insured, 2),
        "uninsured_value_eur": round(uninsured, 2),
        "premium_total_eur": round(premium_total, 2),
        "open_claims_count": open_claims,
        "coverage_ratio": round(ratio, 4),
        "coverage_gaps": gaps,
        "coverage_gap_count": len(gaps),
        "auto_policy_buy": "DISABLED",     # NIEMALS auto-policy-buy
        "auto_policy_cancel": "DISABLED",  # NIEMALS auto-policy-cancel
        "assets": [asdict(a) for a in assessments],
    }


def assert_no_auto_policy_actions(actions: Sequence[str]) -> bool:
    """Guard for the NIEMALS clause: buy/cancel actions are refused.

    Returns True for harmless actions (e.g. 'review', 'alert'); raises
    AutoPolicyActionForbidden for any (auto-)buy/(auto-)cancel request.
    """
    requested = {str(a).strip().lower() for a in actions}
    refused = sorted(requested & FORBIDDEN_POLICY_ACTIONS)
    if refused:
        raise AutoPolicyActionForbidden(
            "df-150 NEVER executes auto-policy buy/cancel; refused: "
            + ", ".join(refused)
        )
    return True


def stop_requested(stop_path: Union[str, Path] = DEFAULT_STOP_FLAG) -> bool:
    """True iff the STOP flag file exists (/tmp/df-150.stop by default)."""
    return Path(stop_path).exists()


def write_report(report: dict, reports_dir: Union[str, Path] = DEFAULT_REPORTS_DIR) -> Path:
    """Persist the report as reports/df-150-{date}.json and return its path."""
    out_dir = Path(reports_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{MODULE_ID}-{report['date']}.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_engine(
    assets: Iterable[AssetInput],
    reports_dir: Union[str, Path] = DEFAULT_REPORTS_DIR,
    stop_path: Union[str, Path] = DEFAULT_STOP_FLAG,
    mock: bool = True,
    report_date: Optional[date] = None,
) -> dict:
    """Heil-Lauf: STOP flag wins; otherwise assess portfolio and persist report."""
    mode = "mock" if mock else "live"
    if stop_requested(stop_path):
        return {
            "status": "STOPPED",
            "mode": mode,
            "reason": f"stop flag present: {stop_path}",
            "report": None,
            "report_path": None,
        }
    report = build_coverage_report(assets, report_date=report_date)
    path = write_report(report, reports_dir)
    return {
        "status": "OK",
        "mode": mode,
        "report": report,
        "report_path": str(path),
    }


MOCK_PORTFOLIO = (
    Asset("house-munich", 1_250_000.0, insured_value_eur=1_000_000.0, premium_eur=4_800.0, open_claims=1),
    Asset("depot-etfs", 640_000.0, insured_value_eur=640_000.0, premium_eur=0.0, open_claims=0),
    Asset("art-collection", 210_000.0, insured_value_eur=150_000.0, premium_eur=2_150.0, open_claims=0),
    Asset("car-classic", 85_000.0, insured_value_eur=0.0, premium_eur=0.0, open_claims=2),
)


def main() -> int:
    result = run_engine(MOCK_PORTFOLIO)  # mock mode, default dirs + stop flag
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "OK" else 1


__all__ = [
    "Asset",
    "AssetAssessment",
    "AutoPolicyActionForbidden",
    "FORBIDDEN_POLICY_ACTIONS",
    "MOCK_PORTFOLIO",
    "assess_asset",
    "assert_no_auto_policy_actions",
    "build_coverage_report",
    "run_engine",
    "stop_requested",
    "to_asset",
    "write_report",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
# [CRUX-MK]
