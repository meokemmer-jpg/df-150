from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


Number = int | float


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "ja", "active"}:
            return True
        if normalized in {"false", "0", "no", "n", "nein", "inactive", ""}:
            return False
    return bool(value)


def _as_eur(value: Any, field: str) -> float:
    try:
        amount = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if amount < 0:
        raise ValueError(f"{field} must not be negative")
    return amount


def load_records(path: str | Path) -> List[Dict[str, Any]]:
    """
    Load asset or claim records from a real JSON or CSV file.

    JSON files may contain either a list of records or an object with an
    "assets" or "claims" list. CSV files are returned as row dictionaries.
    """
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [dict(item) for item in payload]
        if isinstance(payload, dict):
            for key in ("assets", "claims"):
                if isinstance(payload.get(key), list):
                    return [dict(item) for item in payload[key]]
        raise ValueError("JSON input must be a list or contain assets/claims")
    if suffix == ".csv":
        with source.open(newline="", encoding="utf-8") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    raise ValueError(f"Unsupported input format: {source.suffix}")


def evaluate_insurance_status(
    assets: Iterable[Mapping[str, Any]],
    claims: Iterable[Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Compute per-asset and portfolio-level insurance status for df-150.

    Required asset fields:
    - asset_id
    - value_eur

    Optional asset fields:
    - name
    - insured
    - premium_eur
    - insured_value_eur
    - coverage_required_eur
    - policy_active
    """
    claims = list(claims or [])
    asset_reports: List[Dict[str, Any]] = []

    insured_asset_value = 0.0
    uninsured_asset_value = 0.0
    premium_total = 0.0
    coverage_gaps: List[Dict[str, Any]] = []

    for raw_asset in assets:
        if "asset_id" not in raw_asset:
            raise ValueError("asset_id is required")
        if "value_eur" not in raw_asset:
            raise ValueError("value_eur is required")

        asset_id = str(raw_asset["asset_id"])
        name = str(raw_asset.get("name", asset_id))
        value_eur = _as_eur(raw_asset["value_eur"], "value_eur")
        insured = _as_bool(raw_asset.get("insured", False))
        policy_active = _as_bool(raw_asset.get("policy_active", insured))
        premium_eur = _as_eur(raw_asset.get("premium_eur", 0.0), "premium_eur")
        required_eur = _as_eur(
            raw_asset.get("coverage_required_eur", value_eur),
            "coverage_required_eur",
        )

        if insured and policy_active:
            insured_value_eur = _as_eur(
                raw_asset.get("insured_value_eur", value_eur),
                "insured_value_eur",
            )
            insured_asset_value += value_eur
            effective_insured_value = min(insured_value_eur, value_eur)
            gap_eur = max(0.0, required_eur - effective_insured_value)
            status = "insured" if gap_eur == 0 else "underinsured"
        else:
            effective_insured_value = 0.0
            uninsured_asset_value += value_eur
            gap_eur = required_eur
            status = "uninsured"

        premium_total += premium_eur

        asset_report = {
            "asset_id": asset_id,
            "name": name,
            "status": status,
            "value_eur": round(value_eur, 2),
            "insured_value_eur": round(effective_insured_value, 2),
            "premium_eur": round(premium_eur, 2),
            "coverage_gap_eur": round(gap_eur, 2),
            "policy_active": policy_active,
        }
        asset_reports.append(asset_report)

        if gap_eur > 0:
            coverage_gaps.append(
                {
                    "asset_id": asset_id,
                    "name": name,
                    "gap_eur": round(gap_eur, 2),
                    "reason": status,
                }
            )

    open_claims_count = sum(
        1 for claim in claims if str(claim.get("status", "")).strip().lower() == "open"
    )

    return {
        "insured_asset_value_eur": round(insured_asset_value, 2),
        "uninsured_asset_value_eur": round(uninsured_asset_value, 2),
        "premium_total_eur": round(premium_total, 2),
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "assets": asset_reports,
    }


def evaluate_insurance_file(
    assets_path: str | Path,
    claims_path: str | Path | None = None,
) -> Dict[str, Any]:
    assets = load_records(assets_path)
    claims = load_records(claims_path) if claims_path is not None else []
    return evaluate_insurance_status(assets, claims)
