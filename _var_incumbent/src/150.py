# 150.py – Insurance status tracker for KPM (Dark Factory DF-150)
import json
import os
from datetime import datetime

class InsuranceTracker:
    """Track insurance status of assets for KPM."""
    
    def __init__(self):
        self.assets = {}  # asset_id -> dict with fields
    
    def add_asset(self, asset_id, value, insured=False, premium=0.0, open_claims=0):
        """Add an asset. Insured status defaults to False."""
        if asset_id in self.assets:
            raise ValueError(f"Asset '{asset_id}' already exists. Use update_asset instead.")
        self.assets[asset_id] = {
            'value': value,
            'insured': insured,
            'premium': premium,
            'open_claims': open_claims
        }
    
    def update_asset(self, asset_id, insured=None, value=None, premium=None, open_claims=None):
        """Update fields of an existing asset. None means keep current."""
        if asset_id not in self.assets:
            raise KeyError(f"Asset '{asset_id}' not found.")
        asset = self.assets[asset_id]
        if insured is not None:
            asset['insured'] = insured
        if value is not None:
            asset['value'] = value
        if premium is not None:
            asset['premium'] = premium
        if open_claims is not None:
            asset['open_claims'] = open_claims
    
    def remove_asset(self, asset_id):
        """Remove an asset from tracking."""
        if asset_id in self.assets:
            del self.assets[asset_id]
        else:
            raise KeyError(f"Asset '{asset_id}' not found.")
    
    def get_summary(self):
        """Return summary dict with totals and coverage gaps."""
        total_insured_value = 0.0
        total_uninsured_value = 0.0
        total_premium = 0.0
        total_open_claims = 0
        coverage_gaps = []  # list of asset_ids that are uninsured and have value > 0
        
        for aid, data in self.assets.items():
            if data['insured']:
                total_insured_value += data['value']
            else:
                total_uninsured_value += data['value']
                if data['value'] > 0:
                    coverage_gaps.append(aid)
            total_premium += data['premium']
            total_open_claims += data['open_claims']
        
        return {
            'total_insured_value_eur': total_insured_value,
            'total_uninsured_value_eur': total_uninsured_value,
            'total_premium_eur': total_premium,
            'total_open_claims_count': total_open_claims,
            'coverage_gaps': coverage_gaps,
            'coverage_gaps_count': len(coverage_gaps)
        }
    
    def generate_report(self, date_str=None):
        """Generate JSON report in reports/ directory. If date_str not given, use current date."""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        summary = self.get_summary()
        report = {
            'date': date_str,
            'asset_count': len(self.assets),
            'summary': summary,
            'assets': {aid: data for aid, data in self.assets.items()}
        }
        os.makedirs('reports', exist_ok=True)
        filename = f'reports/df-150-{date_str}.json'
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        return filename
# [CRUX-MK]
