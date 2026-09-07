# 150.py — DF-150 KPM-Insurance-Coverage [CRUX-MK]
# Per-Asset-Insurance-Status-Tracking for KPM Familien-Vermoegen-Schutz
# Welle-51 W51-B Skeleton-Wave-2 | Domain: K_0
# NIEMALS Auto-Policy-Buy oder Auto-Policy-Cancel.

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STOP_FLAG_PATH: str = "/tmp/df-150.stop"
REPORTS_DIR: str = "reports"
DEFAULT_REPORT_FILENAME: str = "df-150-{date}.json"


# ---------------------------------------------------------------------------
# Data Models (stdlib dataclasses only)
# ---------------------------------------------------------------------------

@dataclass
class Claim:
    """An insurance claim filed against an asset."""
    claim_id: str
    amount_eur: float
    status: str  # "open" | "closed" | "pending"
    filed_date: str
    description: str = ""


@dataclass
class InsurancePolicy:
    """An insurance policy covering (part of) an asset.  Never auto-buy/cancel."""
    policy_id: str
    provider: str
    premium_eur: float
    coverage_amount_eur: float
    start_date: str
    end_date: str
    active: bool = True


@dataclass
class Asset:
    """
    A single insurable asset in the KPM family wealth portfolio.
    Tracks policies, claims, and computes coverage gaps.
    """
    asset_id: str
    name: str
    value_eur: float
    category: str  # e.g. real_estate, vehicle, art, jewelry, financial
    policies: List[InsurancePolicy] = field(default_factory=list)
    claims: List[Claim] = field(default_factory=list)
    notes: str = ""

    # -- asset-level queries ------------------------------------------------

    def is_insured(self) -> bool:
        """True if at least one active policy provides coverage > 0."""
        return self.total_coverage() > 0.0

    def total_coverage(self) -> float:
        """Sum of coverage_amount_eur across all *active* policies."""
        return sum(p.coverage_amount_eur for p in self.policies if p.active)

    def coverage_gap(self) -> float:
        """
        Positive = underinsured (gap exists).
        Zero or negative = fully covered (or overinsured).
        """
        return max(0.0, self.value_eur - self.total_coverage())

    def has_coverage_gap(self) -> bool:
        return self.coverage_gap() > 0.0

    def total_premium(self) -> float:
        """Sum of premiums across all *active* policies."""
        return sum(p.premium_eur for p in self.policies if p.active)

    def open_claims_count(self) -> int:
        return sum(1 for c in self.claims if c.status == "open")

    def open_claims_value(self) -> float:
        return sum(c.amount_eur for c in self.claims if c.status == "open")


# ---------------------------------------------------------------------------
# Core Engine: KPMInsuranceTracker
# ---------------------------------------------------------------------------

class KPMInsuranceTracker:
    """
    DF-150 Core Engine.
    Tracks insured / uninsured asset values, total premiums, open claims,
    and coverage gaps.  NEVER auto-buys or auto-cancels policies.
    """

    def __init__(self, portfolio_name: str = "KPM-Familien-Vermoegen-Schutz") -> None:
        self.portfolio_name: str = portfolio_name
        self.assets: Dict[str, Asset] = {}

    # -- asset CRUD ---------------------------------------------------------

    def register_asset(
        self, asset_id: str, name: str, value_eur: float, category: str, notes: str = ""
    ) -> Asset:
        if asset_id in self.assets:
            raise ValueError(f"Asset {asset_id} already registered.")
        asset = Asset(asset_id=asset_id, name=name, value_eur=value_eur,
                      category=category, notes=notes)
        self.assets[asset_id] = asset
        return asset

    def remove_asset(self, asset_id: str) -> None:
        self._require_asset(asset_id)
        del self.assets[asset_id]

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        return self.assets.get(asset_id)

    def update_asset_value(self, asset_id: str, new_value_eur: float) -> Asset:
        asset = self._require_asset(asset_id)
        asset.value_eur = new_value_eur
        return asset

    def get_asset_count(self) -> int:
        return len(self.assets)

    # -- policy management (tracking only, NO buy/cancel) -------------------

    def add_policy(
        self, asset_id: str, policy_id: str, provider: str,
        premium_eur: float, coverage_amount_eur: float,
        start_date: str, end_date: str, active: bool = True,
    ) -> InsurancePolicy:
        asset = self._require_asset(asset_id)
        if any(p.policy_id == policy_id for p in asset.policies):
            raise ValueError(f"Policy {policy_id} already exists on asset {asset_id}.")
        policy = InsurancePolicy(
            policy_id=policy_id, provider=provider,
            premium_eur=premium_eur, coverage_amount_eur=coverage_amount_eur,
            start_date=start_date, end_date=end_date, active=active,
        )
        asset.policies.append(policy)
        return policy

    def set_policy_active(self, asset_id: str, policy_id: str, active: bool) -> None:
        asset = self._require_asset(asset_id)
        for p in asset.policies:
            if p.policy_id == policy_id:
                p.active = active
                return
        raise KeyError(f"Policy {policy_id} not found on asset {asset_id}.")

    def remove_policy(self, asset_id: str, policy_id: str) -> None:
        asset = self._require_asset(asset_id)
        for i, p in enumerate(asset.policies):
            if p.policy_id == policy_id:
                asset.policies.pop(i)
                return
        raise KeyError(f"Policy {policy_id} not found on asset {asset_id}.")

    # -- claim management (tracking only) -----------------------------------

    def add_claim(
        self, asset_id: str, claim_id: str, amount_eur: float,
        status: str = "open", filed_date: str = "", description: str = "",
    ) -> Claim:
        asset = self._require_asset(asset_id)
        if any(c.claim_id == claim_id for c in asset.claims):
            raise ValueError(f"Claim {claim_id} already exists on asset {asset_id}.")
        if not filed_date:
            filed_date = datetime.now().strftime("%Y-%m-%d")
        claim = Claim(claim_id=claim_id, amount_eur=amount_eur, status=status,
                      filed_date=filed_date, description=description)
        asset.claims.append(claim)
        return claim

    def update_claim_status(self, asset_id: str, claim_id: str, status: str) -> None:
        asset = self._require_asset(asset_id)
        for c in asset.claims:
            if c.claim_id == claim_id:
                c.status = status
                return
        raise KeyError(f"Claim {claim_id} not found on asset {asset_id}.")

    def remove_claim(self, asset_id: str, claim_id: str) -> None:
        asset = self._require_asset(asset_id)
        for i, c in enumerate(asset.claims):
            if c.claim_id == claim_id:
                asset.claims.pop(i)
                return
        raise KeyError(f"Claim {claim_id} not found on asset {asset_id}.")

    # -- aggregation / core reporting numbers -------------------------------

    def calculate_insured_value(self) -> float:
        """Total EUR value of insured assets."""
        return sum(a.value_eur for a in self.assets.values() if a.is_insured())

    def calculate_uninsured_value(self) -> float:
        """Total EUR value of uninsured assets."""
        return sum(a.value_eur for a in self.assets.values() if not a.is_insured())

    def calculate_total_asset_value(self) -> float:
        return sum(a.value_eur for a in self.assets.values())

    def calculate_premium_total(self) -> float:
        """Total EUR premiums across all active policies."""
        return sum(a.total_premium() for a in self.assets.values())

    def count_open_claims(self) -> int:
        return sum(a.open_claims_count() for a in self.assets.values())

    def calculate_open_claims_value(self) -> float:
        return sum(a.open_claims_value() for a in self.assets.values())

    def detect_coverage_gaps(self) -> List[Dict[str, Any]]:
        """List all assets with a coverage gap (underinsured or uninsured)."""
        gaps: List[Dict[str, Any]] = []
        for a in self.assets.values():
            if a.has_coverage_gap():
                gap = a.coverage_gap()
                gaps.append({
                    "asset_id": a.asset_id,
                    "asset_name": a.name,
                    "asset_value_eur": a.value_eur,
                    "total_coverage_eur": a.total_coverage(),
                    "coverage_gap_eur": gap,
                    "gap_percentage": round(gap / a.value_eur * 100, 2) if a.value_eur > 0 else 0.0,
                    "category": a.category,
                })
        return gaps

    def get_asset_summaries(self) -> List[Dict[str, Any]]:
        summaries: List[Dict[str, Any]] = []
        for a in self.assets.values():
            summaries.append({
                "asset_id": a.asset_id,
                "name": a.name,
                "value_eur": a.value_eur,
                "category": a.category,
                "insured": a.is_insured(),
                "total_coverage_eur": a.total_coverage(),
                "coverage_gap_eur": a.coverage_gap(),
                "has_coverage_gap": a.has_coverage_gap(),
                "premium_total_eur": a.total_premium(),
                "open_claims_count": a.open_claims_count(),
                "open_claims_value_eur": a.open_claims_value(),
                "policy_count": len(a.policies),
                "active_policy_count": sum(1 for p in a.policies if p.active),
                "claim_count": len(a.claims),
            })
        return summaries

    # -- report generation --------------------------------------------------

    def generate_report(self) -> Dict[str, Any]:
        total_value = self.calculate_total_asset_value()
        insured_value = self.calculate_insured_value()
        return {
            "report_metadata": {
                "factory": "df-150",
                "wave": "W51-B",
                "domain": "K_0",
                "portfolio": self.portfolio_name,
                "generated_at": datetime.now().isoformat(),
                "stop_flag_active": self.check_stop_flag(),
            },
            "summary": {
                "total_assets": len(self.assets),
                "total_asset_value_eur": total_value,
                "insured_value_eur": insured_value,
                "uninsured_value_eur": self.calculate_uninsured_value(),
                "insurance_coverage_ratio": round(insured_value / total_value * 100, 2) if total_value > 0 else 0.0,
                "premium_total_eur": self.calculate_premium_total(),
                "open_claims_count": self.count_open_claims(),
                "open_claims_value_eur": self.calculate_open_claims_value(),
                "coverage_gaps_count": len(self.detect_coverage_gaps()),
            },
            "coverage_gaps": self.detect_coverage_gaps(),
            "per_asset": self.get_asset_summaries(),
        }

    def save_report(self, report_date: str = "", output_dir: str = REPORTS_DIR) -> str:
        if not report_date:
            report_date = datetime.now().strftime("%Y-%m-%d")
        filename = DEFAULT_REPORT_FILENAME.format(date=report_date)
        filepath = os.path.join(output_dir, filename)
        os.makedirs(output_dir, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(self.generate_report(), fh, indent=2, ensure_ascii=False)
        return filepath

    def save_report_to_path(self, filepath: str) -> str:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(self.generate_report(), fh, indent=2, ensure_ascii=False)
        return filepath

    # -- stop-flag ----------------------------------------------------------

    def check_stop_flag(self) -> bool:
        return os.path.exists(STOP_FLAG_PATH)

    def set_stop_flag(self) -> str:
        Path(STOP_FLAG_PATH).touch()
        return STOP_FLAG_PATH

    def clear_stop_flag(self) -> None:
        if os.path.exists(STOP_FLAG_PATH):
            os.remove(STOP_FLAG_PATH)

    # -- helpers ------------------------------------------------------------

    def _require_asset(self, asset_id: str) -> Asset:
        if asset_id not in self.assets:
            raise KeyError(f"Asset {asset_id} not found.")
        return self.assets[asset_id]


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def create_tracker(portfolio_name: str = "KPM-Familien-Vermoegen-Schutz") -> KPMInsuranceTracker:
    return KPMInsuranceTracker(portfolio_name=portfolio_name)


# ---------------------------------------------------------------------------
# Mock-Mode Entry Point (python df-150-engine.py)
# ---------------------------------------------------------------------------

def run_mock_mode() -> KPMInsuranceTracker:
    """Demonstrate the engine with sample data."""
    t = KPMInsuranceTracker()

    t.register_asset("AST-001", "Villa am See", 2_500_000.0, "real_estate")
    t.register_asset("AST-002", "Oldtimer Porsche 911", 180_000.0, "vehicle")
    t.register_asset("AST-003", "Gemaelde Monet", 950_000.0, "art")
    t.register_asset("AST-004", "Diamantring", 75_000.0, "jewelry")
    t.register_asset("AST-005", "Aktienportfolio", 500_000.0, "financial")

    t.add_policy("AST-001", "POL-001", "Allianz", 3_500.0, 2_000_000.0, "2024-01-01", "2025-01-01")
    t.add_policy("AST-002", "POL-002", "HDI", 1_200.0, 150_000.0, "2024-03-01", "2025-03-01")
    t.add_policy("AST-003", "POL-003", "AXA", 2_200.0, 950_000.0, "2024-02-01", "2025-02-01")
    # AST-004 intentionally left uninsured
    t.add_policy("AST-005", "POL-005", "Generali", 800.0, 300_000.0, "2024-01-15", "2025-01-15")

    t.add_claim("AST-002", "CLM-001", 5_000.0, "open", "2024-06-15", "Kratzer Lackierung")
    t.add_claim("AST-001", "CLM-002", 15_000.0, "open", "2024-07-01", "Sturmschaden Dach")
    t.add_claim("AST-003", "CLM-003", 20_000.0, "closed", "2024-04-10", "Rahmen restauriert")

    report = t.generate_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    filepath = t.save_report()
    print(f"\nReport saved to: {filepath}")
    return t


if __name__ == "__main__":
    run_mock_mode()
# [CRUX-MK]
