from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

STOP_FLAG_PATH = Path("/tmp/df-150.stop")
_CENTS = Decimal("0.01")


def _as_money(value: Any) -> Decimal:
    try:
        amount = Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive conversion guard
        raise ValueError(f"invalid money value: {value!r}") from exc
    if amount < 0:
        raise ValueError(f"money value must be >= 0: {value!r}")
    return amount.quantize(_CENTS, rounding=ROUND_HALF_UP)


def _as_non_negative_int(value: Any) -> int:
    try:
        number = int(value)
    except Exception as exc:  # pragma: no cover - defensive conversion guard
        raise ValueError(f"invalid integer value: {value!r}") from exc
    if number < 0:
        raise ValueError(f"integer value must be >= 0: {value!r}")
    return number


def _money_to_float(value: Decimal) -> float:
    return float(value.quantize(_CENTS, rounding=ROUND_HALF_UP))


def calculate_insurance_status(assets: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    insured_total = Decimal("0.00")
    uninsured_total = Decimal("0.00")
    premium_total = Decimal("0.00")
    open_claims_total = 0
    coverage_gaps: list[dict[str, Any]] = []

    for index, asset in enumerate(assets, start=1):
        asset_name = str(asset.get("asset_id") or asset.get("name") or f"asset-{index}")
        asset_value = _as_money(asset.get("value_eur", 0))
        insured_value = _as_money(asset.get("insured_value_eur", 0))
        premium = _as_money(asset.get("premium_eur", 0))
        open_claims = _as_non_negative_int(asset.get("open_claims_count", 0))
        coverage_required = bool(asset.get("coverage_required", True))

        effective_insured = min(asset_value, insured_value)
        uncovered_value = asset_value - effective_insured

        insured_total += effective_insured
        uninsured_total += uncovered_value
        premium_total += premium
        open_claims_total += open_claims

        if coverage_required and uncovered_value > 0:
            reason = "uninsured" if effective_insured == 0 else "underinsured"
            coverage_gaps.append(
                {
                    "asset": asset_name,
                    "reason": reason,
                    "asset_value_eur": _money_to_float(asset_value),
                    "insured_value_eur": _money_to_float(effective_insured),
                    "gap_value_eur": _money_to_float(uncovered_value),
                }
            )

    return {
        "insured_asset_value_eur": _money_to_float(insured_total),
        "uninsured_asset_value_eur": _money_to_float(uninsured_total),
        "premium_total_eur": _money_to_float(premium_total),
        "open_claims_count": open_claims_total,
        "coverage_gaps": coverage_gaps,
    }


def build_report(
    assets: Iterable[Mapping[str, Any]],
    *,
    report_date: str | None = None,
    stop_flag_path: str | Path = STOP_FLAG_PATH,
) -> dict[str, Any]:
    resolved_date = report_date or date.today().isoformat()
    report = calculate_insurance_status(assets)
    report["report_date"] = resolved_date
    report["stop_requested"] = Path(stop_flag_path).exists()
    return report


def write_report(
    assets: Iterable[Mapping[str, Any]],
    *,
    report_dir: str | Path = "reports",
    report_date: str | None = None,
    stop_flag_path: str | Path = STOP_FLAG_PATH,
) -> Path:
    report = build_report(assets, report_date=report_date, stop_flag_path=stop_flag_path)
    target_dir = Path(report_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"df-150-{report['report_date']}.json"
    target_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target_path
# [CRUX-MK]
