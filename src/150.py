"""Insurance Coverage Tracker (df-150) - stdlib only"""

class InsuranceTracker:
    """Track insured/uninsured asset values, premiums, claims, and coverage gaps."""

    def __init__(self):
        self._assets = []   # list of dicts: id, name, value, insured_amount, premium
        self._claims = []   # list of dicts: id, asset_id, amount, status

    def _get_asset(self, asset_id):
        """Return asset dict by id or raise KeyError."""
        for a in self._assets:
            if a['id'] == asset_id:
                return a
        raise KeyError(f'Asset {asset_id!r} not found')

    def add_asset(self, asset_id, name, value):
        """Register a new asset with zero insurance and premium."""
        if any(a['id'] == asset_id for a in self._assets):
            raise ValueError(f'Asset {asset_id!r} already exists')
        self._assets.append({
            'id': asset_id,
            'name': name,
            'value': value,
            'insured_amount': 0.0,
            'premium': 0.0,
        })

    def set_insured_amount(self, asset_id, amount):
        """Update insured amount; cannot exceed asset value."""
        asset = self._get_asset(asset_id)
        if amount < 0:
            raise ValueError('Insured amount cannot be negative')
        if amount > asset['value']:
            raise ValueError('Insured amount cannot exceed asset value')
        asset['insured_amount'] = amount

    def set_premium(self, asset_id, premium):
        """Set the premium for an asset's policy."""
        asset = self._get_asset(asset_id)
        if premium < 0:
            raise ValueError('Premium cannot be negative')
        asset['premium'] = premium

    def add_claim(self, claim_id, asset_id, amount):
        """File a new open claim against an asset."""
        self._get_asset(asset_id)  # ensure asset exists
        if any(c['id'] == claim_id for c in self._claims):
            raise ValueError(f'Claim {claim_id!r} already exists')
        self._claims.append({
            'id': claim_id,
            'asset_id': asset_id,
            'amount': amount,
            'status': 'open',
        })

    def close_claim(self, claim_id):
        """Close an open claim."""
        for claim in self._claims:
            if claim['id'] == claim_id:
                if claim['status'] != 'open':
                    raise ValueError(f'Claim {claim_id!r} is not open')
                claim['status'] = 'closed'
                return
        raise KeyError(f'Claim {claim_id!r} not found')

    @property
    def insured_value(self):
        """Total insured value across all assets (EUR)."""
        return sum(a['insured_amount'] for a in self._assets)

    @property
    def uninsured_value(self):
        """Total uninsured value (asset value minus insured amount) across all assets (EUR)."""
        return sum(a['value'] - a['insured_amount'] for a in self._assets)

    @property
    def total_premium(self):
        """Sum of all premiums (EUR)."""
        return sum(a['premium'] for a in self._assets)

    @property
    def open_claims_count(self):
        """Number of claims currently open."""
        return sum(1 for c in self._claims if c['status'] == 'open')

    @property
    def coverage_gap_count(self):
        """Number of assets where insured_amount < asset value."""
        return sum(1 for a in self._assets if a['insured_amount'] < a['value'])

    def report(self):
        """Return a dictionary with all key metrics."""
        return {
            'insured_value': self.insured_value,
            'uninsured_value': self.uninsured_value,
            'total_premium': self.total_premium,
            'open_claims_count': self.open_claims_count,
            'coverage_gap_count': self.coverage_gap_count,
        }
# [CRUX-MK]
