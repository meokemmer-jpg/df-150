import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib
import pytest

# Import module '150' despite its numeric name
module = importlib.import_module('150')
compute_insurance_status = module.compute_insurance_status


def test_basic_tracking():
    assets = [
        {'id': 'A1', 'value': 100000.0, 'policy_id': 'P1'},
        {'id': 'A2', 'value': 50000.0, 'policy_id': 'P2'},
        {'id': 'A3', 'value': 75000.0, 'policy_id': None},
        {'id': 'A4', 'value': 200000.0, 'policy_id': 'P3'},
    ]
    policies = [
        {'id': 'P1', 'premium': 1500.0, 'status': 'active'},
        {'id': 'P2', 'premium': 800.0, 'status': 'lapsed'},
        {'id': 'P3', 'premium': 3000.0, 'status': 'active'},
    ]
    claims = [
        {'id': 'C1', 'policy_id': 'P1', 'status': 'open'},
        {'id': 'C2', 'policy_id': 'P1', 'status': 'closed'},
        {'id': 'C3', 'policy_id': 'P3', 'status': 'open'},
    ]
    
    result = compute_insurance_status(assets, policies, claims)
    
    assert result['insured_value'] == 300000.0
    assert result['uninsured_value'] == 125000.0
    assert result['premium_total'] == 4500.0
    assert result['open_claims_count'] == 2
    assert set(result['coverage_gaps']) == {'A2', 'A3'}
    assert len(result['coverage_gaps']) == 2


def test_no_policies():
    assets = [{'id': 'X', 'value': 1.0, 'policy_id': None}]
    result = compute_insurance_status(assets, [], [])
    assert result['insured_value'] == 0.0
    assert result['uninsured_value'] == 1.0
    assert result['premium_total'] == 0.0
    assert result['open_claims_count'] == 0
    assert result['coverage_gaps'] == ['X']


def test_all_insured():
    assets = [
        {'id': 'B1', 'value': 10.0, 'policy_id': 'P'},
        {'id': 'B2', 'value': 20.0, 'policy_id': 'P'},
    ]
    policies = [{'id': 'P', 'premium': 5.0, 'status': 'active'}]
    result = compute_insurance_status(assets, policies, [])
    assert result['insured_value'] == 30.0
    assert result['uninsured_value'] == 0.0
    assert result['premium_total'] == 5.0
    assert result['coverage_gaps'] == []
