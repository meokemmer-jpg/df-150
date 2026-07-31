import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# NOTE: Python normally forbids numeric module names. The required import 'from 150 import ...'
# is syntactically invalid. We simulate the required behaviour via importlib.
import importlib
insurance_status = importlib.import_module('150').insurance_status


def test_empty_assets():
    result = insurance_status([])
    assert result == {
        'total_insured_value': 0.0,
        'total_uninsured_value': 0.0,
        'total_premium': 0.0,
        'open_claims_count': 0,
        'coverage_gaps': [],
    }


def test_mixed_assets():
    assets = [
        {'name': 'Building A', 'value': 5_000_000.0, 'insured': True, 'premium': 2500.0, 'open_claims': 1},
        {'name': 'Vehicle Fleet', 'value': 200_000.0, 'insured': False, 'premium': 0.0, 'open_claims': 0},
        {'name': 'Art Collection', 'value': 1_500_000.0, 'insured': True, 'premium': 5000.0, 'open_claims': 2},
        {'name': 'Liability', 'value': 0.0, 'insured': False, 'premium': 1000.0, 'open_claims': 0},
    ]
    result = insurance_status(assets)
    assert result['total_insured_value'] == 6_500_000.0
    assert result['total_uninsured_value'] == 200_000.0
    assert result['total_premium'] == 8500.0
    assert result['open_claims_count'] == 3
    assert set(result['coverage_gaps']) == {'Vehicle Fleet', 'Liability'}


def test_all_insured():
    assets = [
        {'name': 'Item1', 'value': 100.0, 'insured': True, 'premium': 10.0, 'open_claims': 0},
        {'name': 'Item2', 'value': 200.0, 'insured': True, 'premium': 20.0, 'open_claims': 5},
    ]
    result = insurance_status(assets)
    assert result['total_insured_value'] == 300.0
    assert result['total_uninsured_value'] == 0.0
    assert result['total_premium'] == 30.0
    assert result['open_claims_count'] == 5
    assert result['coverage_gaps'] == []


def test_all_uninsured():
    assets = [
        {'name': 'Risky', 'value': 50.0, 'insured': False, 'premium': 0.0, 'open_claims': 0},
    ]
    result = insurance_status(assets)
    assert result['total_insured_value'] == 0.0
    assert result['total_uninsured_value'] == 50.0
    assert result['total_premium'] == 0.0
    assert result['open_claims_count'] == 0
    assert result['coverage_gaps'] == ['Risky']

