"""
df-150 KPM Insurance Coverage Tracker
Tracks per-asset insurance status: insured/uninsured values, premium total,
open claims count, coverage gaps.
"""

from typing import List, Dict, Union

def insurance_status(assets: List[Dict[str, Union[str, float, int, bool]]]) -> Dict[str, Union[float, int, List[str]]]:
    """
    Calculate aggregate insurance metrics from a list of assets.

    Each asset dict must have:
        'name': str          - identifier of the asset
        'value': float       - asset value in EUR
        'insured': bool      - insurance status
        'premium': float     - annual premium in EUR
        'open_claims': int   - number of open claims

    Returns a dict with:
        'total_insured_value': sum of values of insured assets
        'total_uninsured_value': sum of values of uninsured assets
        'total_premium': sum of premiums across all assets
        'open_claims_count': total number of open claims
        'coverage_gaps': list of names of uninsured assets
    """
    total_insured = 0.0
    total_uninsured = 0.0
    premium_total = 0.0
    claims_count = 0
    gaps = []

    for asset in assets:
        value = float(asset['value'])
        premium = float(asset['premium'])
        claims = int(asset['open_claims'])

        if asset['insured']:
            total_insured += value
        else:
            total_uninsured += value
            gaps.append(asset['name'])

        premium_total += premium
        claims_count += claims

    return {
        'total_insured_value': total_insured,
        'total_uninsured_value': total_uninsured,
        'total_premium': premium_total,
        'open_claims_count': claims_count,
        'coverage_gaps': gaps,
    }
# [CRUX-MK]
