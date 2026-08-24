from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class AssetInsuranceStatus:
    asset_id: str
    asset_name: str
    asset_value_eur: float
    insured_value_eur: float
    premium_eur: float
    open_claims_count: int
    coverage_gap_eur: float
    insured: bool


def evaluate_asset_coverage(asset: dict) -> AssetInsuranceStatus:
    asset_id = str(asset["asset_id"])
    asset_name = str(asset["asset_name"])
    asset_value_eur = float(asset["asset_value_eur"])
    insured_value_eur = max(0.0, min(float(asset.get("insured_value_eur", 0.0)), asset_value_eur))
    premium_eur = max(0.0, float(asset.get("premium_eur", 0.0)))
    open_claims_count = max(0, int(asset.get("open_claims_count", 0)))

    coverage_gap_eur = round(max(0.0, asset_value_eur - insured_value_eur), 2)
    insured = insured_value_eur > 0.0 and coverage_gap_eur == 0.0

    return AssetInsuranceStatus(
        asset_id=asset_id,
        asset_name=asset_name,
        asset_value_eur=round(asset_value_eur, 2),
        insured_value_eur=round(insured_value_eur, 2),
        premium_eur=round(premium_eur, 2),
        open_claims_count=open_claims_count,
        coverage_gap_eur=coverage_gap_eur,
        insured=insured,
    )


def build_insurance_report(assets: Iterable[dict], report_date: Optional[str] = None) -> dict:
    evaluated: List[AssetInsuranceStatus] = [evaluate_asset_coverage(asset) for asset in assets]

    insured_total = round(sum(a.insured_value_eur for a in evaluated), 2)
    asset_total = round(sum(a.asset_value_eur for a in evaluated), 2)
    uninsured_total = round(sum(a.coverage_gap_eur for a in evaluated), 2)
    premium_total = round(sum(a.premium_eur for a in evaluated), 2)
    open_claims_total = sum(a.open_claims_count for a in evaluated)

    coverage_gaps = [
        {
            "asset_id": a.asset_id,
            "asset_name": a.asset_name,
            "gap_eur": a.coverage_gap_eur,
        }
        for a in evaluated
        if a.coverage_gap_eur > 0.0
    ]

    return {
        "report_date": report_date or date.today().isoformat(),
        "totals": {
            "asset_value_eur": asset_total,
            "insured_value_eur": insured_total,
            "uninsured_value_eur": uninsured_total,
            "premium_total_eur": premium_total,
            "open_claims_count": open_claims_total,
        },
        "coverage_gaps": coverage_gaps,
        "assets": [
            {
                "asset_id": a.asset_id,
                "asset_name": a.asset_name,
                "asset_value_eur": a.asset_value_eur,
                "insured_value_eur": a.insured_value_eur,
                "premium_eur": a.premium_eur,
                "open_claims_count": a.open_claims_count,
                "coverage_gap_eur": a.coverage_gap_eur,
                "insured": a.insured,
            }
            for a in evaluated
        ],
        "policy_actions": {
            "auto_policy_buy": False,
            "auto_policy_cancel": False,
        },
    }


def report_to_json(report: dict) -> str:
    return json.dumps(report, indent=2, sort_keys=True)
# [CRUX-MK]
