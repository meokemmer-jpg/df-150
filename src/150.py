"""Dark-Factory df-150: KPM Insurance Coverage Tracking (Core Logic)"""

def compute_insurance_status(assets, policies, claims):
    """
    Args:
        assets: list of dicts with keys: 'id', 'value', 'policy_id' (optional, can be None)
        policies: list of dicts with keys: 'id', 'premium', 'status' ('active' or 'lapsed')
        claims: list of dicts with keys: 'id', 'policy_id', 'status' ('open' or 'closed')
    Returns:
        dict with:
            'insured_value': total value of insured assets (EUR)
            'uninsured_value': total value of uninsured assets (EUR)
            'premium_total': sum of premiums of active policies (EUR)
            'open_claims_count': number of open claims
            'coverage_gaps': list of asset IDs that are not insured
    """
    policy_map = {p['id']: p for p in policies}
    
    insured_value = 0.0
    uninsured_value = 0.0
    coverage_gaps = []
    
    for asset in assets:
        asset_id = asset['id']
        value = asset['value']
        policy_id = asset.get('policy_id')
        if policy_id is not None:
            policy = policy_map.get(policy_id)
            if policy and policy['status'] == 'active':
                insured_value += value
            else:
                uninsured_value += value
                coverage_gaps.append(asset_id)
        else:
            uninsured_value += value
            coverage_gaps.append(asset_id)
    
    premium_total = sum(p['premium'] for p in policies if p['status'] == 'active')
    
    open_claims_count = sum(1 for c in claims if c['status'] == 'open')
    
    return {
        'insured_value': insured_value,
        'uninsured_value': uninsured_value,
        'premium_total': premium_total,
        'open_claims_count': open_claims_count,
        'coverage_gaps': coverage_gaps
    }
# [CRUX-MK]
