import importlib
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _load():
    return importlib.import_module("150")


def _write_json(path: Path, records):
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return path


def test_df150_discriminates_insured_asset_from_adversarial_uninsured_file(tmp_path):
    mod = _load()

    covered_asset = {
        "asset_id": "press-01",
        "name": "Production press",
        "value_eur": 120000,
        "coverage_required_eur": 120000,
        "insured": True,
        "policy_active": True,
        "insured_value_eur": 120000,
        "premium_eur": 2400,
    }
    adversarial_asset = {
        **covered_asset,
        "insured": False,
        "policy_active": False,
        "insured_value_eur": 0,
        "premium_eur": 0,
    }

    covered_path = _write_json(tmp_path / "covered_assets.json", [covered_asset])
    adversarial_path = _write_json(
        tmp_path / "adversarial_uninsured_assets.json",
        [adversarial_asset],
    )
    claims_path = _write_json(
        tmp_path / "claims.json",
        [{"claim_id": "clm-1", "status": "open"}],
    )

    covered = mod.evaluate_insurance_file(covered_path, claims_path)
    adversarial = mod.evaluate_insurance_file(adversarial_path, claims_path)

    assert covered != adversarial
    assert covered["assets"][0]["status"] == "insured"
    assert adversarial["assets"][0]["status"] == "uninsured"
    assert covered["coverage_gaps"] == []
    assert adversarial["coverage_gaps"][0]["gap_eur"] == adversarial_asset["coverage_required_eur"]
    assert covered["insured_asset_value_eur"] == covered_asset["value_eur"]
    assert adversarial["uninsured_asset_value_eur"] == adversarial_asset["value_eur"]
    assert covered["open_claims_count"] == adversarial["open_claims_count"] == 1


def test_df150_discriminates_underinsured_asset_from_fully_covered_file(tmp_path):
    mod = _load()

    full_cover = {
        "asset_id": "warehouse-02",
        "value_eur": 300000,
        "coverage_required_eur": 300000,
        "insured": True,
        "policy_active": True,
        "insured_value_eur": 300000,
    }
    underinsured = {
        **full_cover,
        "insured_value_eur": full_cover["coverage_required_eur"] - 75000,
    }

    full_cover_path = _write_json(tmp_path / "full_cover.json", {"assets": [full_cover]})
    underinsured_path = _write_json(
        tmp_path / "underinsured.json",
        {"assets": [underinsured]},
    )

    full_cover_result = mod.evaluate_insurance_file(full_cover_path)
    underinsured_result = mod.evaluate_insurance_file(underinsured_path)

    assert full_cover_result["assets"][0]["status"] == "insured"
    assert underinsured_result["assets"][0]["status"] == "underinsured"
    assert full_cover_result["assets"][0]["coverage_gap_eur"] == 0
    assert underinsured_result["assets"][0]["coverage_gap_eur"] == (
        underinsured["coverage_required_eur"] - underinsured["insured_value_eur"]
    )
    assert full_cover_result != underinsured_result
