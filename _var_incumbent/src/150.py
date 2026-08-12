from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any, Dict, List


@dataclass(frozen=True)
class Asset:
    name: str
    value_eur: float
    insured_value_eur: float = 0.0
    annual_premium_eur: float = 0.0
    required: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Asset":
        return cls(
            name=str(data["name"]),
            value_eur=float(data["value_eur"]),
            insured_value_eur=float(data.get("insured_value_eur", 0.0)),
            annual_premium_eur=float(data.get("annual_premium_eur", 0.0)),
            required=bool(data.get("required", True)),
        )


@dataclass(frozen=True)
class Claim:
    asset_name: str
    status: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Claim":
        return cls(
            asset_name=str(data["asset_name"]),
            status=str(data["status"]).strip().lower(),
        )


def calculate_insurance_status(
    assets: Iterable[Mapping[str, Any]],
    claims: Iterable[Mapping[str, Any]] = (),
) -> Dict[str, Any]:
    parsed_assets = [Asset.from_mapping(asset) for asset in assets]
    parsed_claims = [Claim.from_mapping(claim) for claim in claims]

    insured_total = 0.0
    uninsured_total = 0.0
    premium_total = 0.0
    coverage_gaps: List[Dict[str, Any]] = []

    for asset in parsed_assets:
        if asset.value_eur < 0 or asset.insured_value_eur < 0 or asset.annual_premium_eur < 0:
            raise ValueError("EUR values must be non-negative")

        effective_insured = min(asset.value_eur, asset.insured_value_eur)
        uninsured_amount = max(0.0, asset.value_eur - effective_insured)

        insured_total += effective_insured
        uninsured_total += uninsured_amount
        premium_total += asset.annual_premium_eur

        if asset.required and uninsured_amount > 0:
            gap_type = "uninsured" if effective_insured == 0 else "underinsured"
            coverage_gaps.append(
                {
                    "asset_name": asset.name,
                    "gap_type": gap_type,
                    "uninsured_value_eur": round(uninsured_amount, 2),
                }
            )

    open_claims_count = sum(1 for claim in parsed_claims if claim.status == "open")

    return {
        "insured_value_eur": round(insured_total, 2),
        "uninsured_value_eur": round(uninsured_total, 2),
        "premium_total_eur": round(premium_total, 2),
        "open_claims_count": open_claims_count,
        "coverage_gaps": coverage_gaps,
        "auto_policy_buy": False,
        "auto_policy_cancel": False,
    }
# [CRUX-MK]
