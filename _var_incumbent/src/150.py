from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping, Any


STOP_FLAG_PATH = "/tmp/df-150.stop"


def _money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _as_eur(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def evaluate_insurance_status(
    assets: Iterable[Mapping[str, Any]],
    claims: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    insured_value = Decimal("0.00")
    uninsured_value = Decimal("0.00")
    premium_total = Decimal("0.00")
    coverage_gaps: list[dict[str, Any]] = []

    for index, asset in enumerate(assets, start=1):
        asset_id = str(asset.get("asset_id") or asset.get("name") or f"asset-{index}")
        value = _money(asset.get("value_eur", 0))
        premium = _money(asset.get("premium_eur", 0))
        insured = bool(asset.get("insured", False))
        required = bool(asset.get("coverage_required", True))

        premium_total += premium
        if insured:
            insured_value += value
        else:
            uninsured_value += value
            if required and value > 0:
                coverage_gaps.append(
                    {
                        "asset_id": asset_id,
                        "reason": "required_asset_uninsured",
                        "value_eur": _as_eur(value),
                    }
                )

        if insured and premium == 0 and value > 0:
            coverage_gaps.append(
                {
                    "asset_id": asset_id,
                    "reason": "insured_asset_missing_premium",
                    "value_eur": _as_eur(value),
                }
            )

    open_claims_count = 0
    for claim in claims or ():
        status = str(claim.get("status", "")).strip().lower()
        if status in {"open", "pending", "in_progress"}:
            open_claims_count += 1

    return {
        "insured_value_eur": _as_eur(insured_value),
        "uninsured_value_eur": _as_eur(uninsured_value),
        "premium_total_eur": _as_eur(premium_total),
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "stop_flag_path": STOP_FLAG_PATH,
        "auto_policy_actions": [],
    }


def build_report(
    assets: Iterable[Mapping[str, Any]],
    claims: Iterable[Mapping[str, Any]] | None = None,
    report_date: date | None = None,
) -> dict[str, Any]:
    report_date = report_date or date.today()
    summary = evaluate_insurance_status(assets, claims)
    return {
        "factory": "df-150",
        "domain": "K_0",
        "report_date": report_date.isoformat(),
        **summary,
    }


def write_report(
    assets: Iterable[Mapping[str, Any]],
    claims: Iterable[Mapping[str, Any]] | None = None,
    report_date: date | None = None,
    reports_dir: str | Path = "reports",
) -> Path:
    report = build_report(assets, claims, report_date=report_date)
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    target = reports_path / f"df-150-{report['report_date']}.json"
    target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return target
# [CRUX-MK]
