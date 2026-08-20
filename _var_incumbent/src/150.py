"""DF-150 KPM Insurance Coverage Tracker.

Kern der Mission: Versicherungsstatus je Asset verfolgen,
Pramien summieren, offene Schaeden zaehlen und Deckungsluecken
ausweisen. Es werden keine Policen automatisch gekauft oder storniert.
"""

class KPMInsuranceTracker:
    """Manueller, zustandsbehafteter KPM-Versicherungs-Tracker."""

    def __init__(self):
        self.assets = {}
        self.claims = []
        self._next_claim_id = 1

    def _require_asset(self, asset_id):
        if asset_id not in self.assets:
            raise KeyError(f"Unbekanntes Asset: {asset_id}")

    def add_asset(self, asset_id, value_euro, insured_amount_euro=0.0):
        """Asset anlegen. Versicherungswert muss manuell erfasst werden."""
        if asset_id in self.assets:
            raise ValueError(f"Asset existiert bereits: {asset_id}")
        if value_euro < 0:
            raise ValueError("value_euro darf nicht negativ sein")
        if insured_amount_euro < 0:
            raise ValueError("insured_amount_euro darf nicht negativ sein")

        self.assets[asset_id] = {
            "value_euro": float(value_euro),
            "insured_amount_euro": float(insured_amount_euro),
            "premium_euro": 0.0,
        }
        return asset_id

    def update_asset_value(self, asset_id, value_euro):
        """Wert eines Assets aktualisieren (z.B. Neubewertung)."""
        self._require_asset(asset_id)
        if value_euro < 0:
            raise ValueError("value_euro darf nicht negativ sein")

        self.assets[asset_id]["value_euro"] = float(value_euro)
        return asset_id

    def set_policy(self, asset_id, coverage_amount_euro, premium_euro):
        """Manuelle Policenpflege. Kein Auto-Buy/Auto-Cancel."""
        self._require_asset(asset_id)
        if coverage_amount_euro < 0:
            raise ValueError("coverage_amount_euro darf nicht negativ sein")
        if premium_euro < 0:
            raise ValueError("premium_euro darf nicht negativ sein")

        asset = self.assets[asset_id]
        asset["insured_amount_euro"] = float(coverage_amount_euro)
        asset["premium_euro"] = float(premium_euro)
        return asset_id

    def open_claim(self, asset_id, amount_euro):
        """Offenen Schaden manuell erfassen."""
        self._require_asset(asset_id)
        if amount_euro < 0:
            raise ValueError("amount_euro darf nicht negativ sein")

        claim_id = self._next_claim_id
        self._next_claim_id += 1
        self.claims.append({
            "id": claim_id,
            "asset_id": asset_id,
            "amount_euro": float(amount_euro),
            "open": True,
        })
        return claim_id

    def close_claim(self, claim_id):
        """Schaden manuell schliessen."""
        for claim in self.claims:
            if claim["id"] == claim_id:
                claim["open"] = False
                return claim_id
        raise KeyError(f"Schaden nicht gefunden: {claim_id}")

    def status(self):
        """Liefert Statuskennzahlen fuer KPM."""
        total_asset_value = 0.0
        insured_value = 0.0
        premium_total = 0.0
        open_claims_count = 0
        coverage_gaps = []

        for asset_id, asset in self.assets.items():
            value = asset["value_euro"]
            insured_amount = asset["insured_amount_euro"]

            total_asset_value += value
            insured_value += min(value, insured_amount)
            premium_total += asset.get("premium_euro", 0.0)

            gap = value - insured_amount
            if gap > 0.0:
                coverage_gaps.append({
                    "asset_id": asset_id,
                    "gap_euro": round(gap, 2),
                })

        uninsured_value = total_asset_value - insured_value
        open_claims_count = sum(1 for claim in self.claims if claim["open"])
        coverage_gaps.sort(key=lambda item: item["asset_id"])

        return {
            "total_asset_value_euro": round(total_asset_value, 2),
            "insured_value_euro": round(insured_value, 2),
            "uninsured_value_euro": round(uninsured_value, 2),
            "premium_total_euro": round(premium_total, 2),
            "open_claims_count": open_claims_count,
            "coverage_gaps": coverage_gaps,
        }


# Modulweite Default-Instanz fuer einfache Nutzung
_default_tracker = KPMInsuranceTracker()


def add_asset(asset_id, value_euro, insured_amount_euro=0.0):
    return _default_tracker.add_asset(asset_id, value_euro, insured_amount_euro)


def update_asset_value(asset_id, value_euro):
    return _default_tracker.update_asset_value(asset_id, value_euro)


def set_policy(asset_id, coverage_amount_euro, premium_euro):
    return _default_tracker.set_policy(asset_id, coverage_amount_euro, premium_euro)


def open_claim(asset_id, amount_euro):
    return _default_tracker.open_claim(asset_id, amount_euro)


def close_claim(claim_id):
    return _default_tracker.close_claim(claim_id)


def get_status():
    return _default_tracker.status()
# [CRUX-MK]
