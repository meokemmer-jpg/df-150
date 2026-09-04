from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence

STOP_FLAG = Path("/tmp/df-150.stop")


@dataclass(frozen=True)
class AssetStatus:
    asset_id: str
    category: str
    asset_value_eur: float
    insured_value_eur: float
    uninsured_value_eur: float
    premium_eur: float
    open_claims_count: int
    coverage_gap: bool


def _to_float(value: object) -> float:
    number = float(value)
    if number < 0:
        raise ValueError("Negative monetary values are not allowed")
    return round(number, 2)


def evaluate_asset(
    asset: Mapping[str, object],
    policies: Sequence[Mapping[str, object]],
    claims: Sequence[Mapping[str, object]],
) -> AssetStatus:
    asset_id = str(asset["asset_id"])
    category = str(asset.get("category", "unknown"))
    asset_value = _to_float(asset["value_eur"])

    active_policies = [p for p in policies if str(p["asset_id"]) == asset_id and bool(p.get("active", True))]
    insured_value = min(asset_value, sum(_to_float(p.get("coverage_eur", 0)) for p in active_policies))
    premium_total = sum(_to_float(p.get("premium_eur", 0)) for p in active_policies)
    open_claims = sum(
        1
        for claim in claims
        if str(claim["asset_id"]) == asset_id and str(claim.get("status", "")).lower() == "open"
    )
    uninsured_value = round(asset_value - insured_value, 2)

    return AssetStatus(
        asset_id=asset_id,
        category=category,
        asset_value_eur=asset_value,
        insured_value_eur=round(insured_value, 2),
        uninsured_value_eur=uninsured_value,
        premium_eur=round(premium_total, 2),
        open_claims_count=open_claims,
        coverage_gap=uninsured_value > 0,
    )


def build_report(
    assets: Iterable[Mapping[str, object]],
    policies: Sequence[Mapping[str, object]],
    claims: Sequence[Mapping[str, object]],
) -> dict:
    if STOP_FLAG.exists():
        raise RuntimeError("STOP flag present: /tmp/df-150.stop")

    asset_statuses = [evaluate_asset(asset, policies, claims) for asset in assets]
    gaps_by_asset = [status.asset_id for status in asset_statuses if status.coverage_gap]
    gaps_by_category: dict[str, float] = defaultdict(float)

    for status in asset_statuses:
        if status.coverage_gap:
            gaps_by_category[status.category] += status.uninsured_value_eur

    return {
        "date": date.today().isoformat(),
        "insured_value_eur": round(sum(s.insured_value_eur for s in asset_statuses), 2),
        "uninsured_value_eur": round(sum(s.uninsured_value_eur for s in asset_statuses), 2),
        "premium_total_eur": round(sum(s.premium_eur for s in asset_statuses), 2),
        "open_claims_count": sum(s.open_claims_count for s in asset_statuses),
        "coverage_gaps": {
            "count": len(gaps_by_asset),
            "asset_ids": gaps_by_asset,
            "by_category_eur": dict(sorted((k, round(v, 2)) for k, v in gaps_by_category.items())),
        },
        "assets": [asdict(status) for status in asset_statuses],
        "auto_policy_actions": [],
    }


def write_report(report: Mapping[str, object], directory: str | Path = "reports") -> Path:
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"df-150-{report['date']}.json"
    target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return target


if __name__ == "__main__":
    sample_assets = [
        {"asset_id": "house-1", "category": "real_estate", "value_eur": 500000},
        {"asset_id": "art-1", "category": "collectibles", "value_eur": 120000},
    ]
    sample_policies = [
        {"policy_id": "p-1", "asset_id": "house-1", "coverage_eur": 500000, "premium_eur": 1800, "active": True},
        {"policy_id": "p-2", "asset_id": "art-1", "coverage_eur": 50000, "premium_eur": 400, "active": True},
    ]
    sample_claims = [
        {"claim_id": "c-1", "asset_id": "house-1", "status": "open"},
        {"claim_id": "c-2", "asset_id": "art-1", "status": "closed"},
    ]

    report = build_report(sample_assets, sample_policies, sample_claims)
    path = write_report(report)
    print(path)
# [CRUX-MK]
