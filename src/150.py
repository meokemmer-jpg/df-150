from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Any


@dataclass(frozen=True)
class AssetCoverage:
    asset_id: str
    asset_value_eur: float
    insured_value_eur: float
    premium_eur: float
    has_coverage_gap: bool
    gap_value_eur: float


def _to_float(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if number < 0:
        raise ValueError(f"{field_name} must be >= 0")
    return round(number, 2)


def evaluate_asset(asset: Mapping[str, Any]) -> AssetCoverage:
    asset_id = str(asset.get("asset_id", "")).strip()
    if not asset_id:
        raise ValueError("asset_id is required")

    asset_value = _to_float(asset.get("asset_value_eur", 0), "asset_value_eur")
    insured_value = _to_float(asset.get("insured_value_eur", 0), "insured_value_eur")
    premium = _to_float(asset.get("premium_eur", 0), "premium_eur")

    if insured_value > asset_value:
        raise ValueError("insured_value_eur cannot exceed asset_value_eur")

    gap_value = round(asset_value - insured_value, 2)
    return AssetCoverage(
        asset_id=asset_id,
        asset_value_eur=asset_value,
        insured_value_eur=insured_value,
        premium_eur=premium,
        has_coverage_gap=gap_value > 0,
        gap_value_eur=gap_value,
    )


def build_insurance_report(
    assets: Iterable[Mapping[str, Any]],
    open_claims: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    evaluated = [evaluate_asset(asset) for asset in assets]

    insured_total = round(sum(a.insured_value_eur for a in evaluated), 2)
    uninsured_total = round(sum(a.gap_value_eur for a in evaluated), 2)
    premium_total = round(sum(a.premium_eur for a in evaluated), 2)
    open_claims_count = sum(1 for claim in open_claims if claim.get("status") == "open")

    coverage_gaps = [
        {
            "asset_id": a.asset_id,
            "gap_value_eur": a.gap_value_eur,
        }
        for a in evaluated
        if a.has_coverage_gap
    ]

    return {
        "insured_asset_value_eur": insured_total,
        "uninsured_asset_value_eur": uninsured_total,
        "premium_total_eur": premium_total,
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "auto_policy_actions": [],
    }


def write_report(
    assets: Iterable[Mapping[str, Any]],
    open_claims: Iterable[Mapping[str, Any]] = (),
    output_dir: str | Path = "reports",
    report_date: date | None = None,
) -> Path:
    report = build_insurance_report(assets, open_claims)
    report_date = report_date or date.today()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"df-150-{report_date.isoformat()}.json"
    file_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return file_path
# [CRUX-MK]
