# df-150 engine - Insurance Coverage Tracking
# Save as 150.py

class InsuranceTracker:
    """Tracks per-asset insurance status, premiums, claims and coverage gaps."""

    def __init__(self):
        self._assets = {}       # asset_id -> dict(value, insured, premium)
        self._claims = {}       # claim_id -> "open"/"closed"
        self._next_claim_id = 1

    def add_asset(self, asset_id, value, insured=True, premium=0.0):
        """Register or update an asset with its insured status and premium."""
        self._assets[asset_id] = {
            'value': float(value),
            'insured': bool(insured),
            'premium': float(premium)
        }

    def remove_asset(self, asset_id):
        """Remove an asset from tracking."""
        self._assets.pop(asset_id, None)

    def set_insured_status(self, asset_id, insured):
        """Change insured flag of an existing asset."""
        if asset_id in self._assets:
            self._assets[asset_id]['insured'] = bool(insured)

    def file_claim(self):
        """Open a new claim. Returns claim_id."""
        cid = self._next_claim_id
        self._claims[cid] = 'open'
        self._next_claim_id += 1
        return cid

    def settle_claim(self, claim_id):
        """Close a claim."""
        if claim_id in self._claims:
            self._claims[claim_id] = 'closed'

    # --- computed properties ---
    @property
    def insured_value(self):
        """Total value of insured assets (EUR)."""
        return sum(a['value'] for a in self._assets.values() if a['insured'])

    @property
    def uninsured_value(self):
        """Total value of uninsured assets (EUR)."""
        return sum(a['value'] for a in self._assets.values() if not a['insured'])

    @property
    def premium_total(self):
        """Total premium across all tracked assets (EUR)."""
        return sum(a['premium'] for a in self._assets.values())

    @property
    def open_claims_count(self):
        """Number of open claims."""
        return sum(1 for s in self._claims.values() if s == 'open')

    @property
    def coverage_gaps(self):
        """List of asset_ids that are currently uninsured."""
        return [aid for aid, a in self._assets.items() if not a['insured']]
# [CRUX-MK]
