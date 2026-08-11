"""DF-150 KPM-Insurance-Coverage [CRUX-MK]

Domain K_0 (KPM Familien-Vermoegen-Schutz), Welle 25.

KERN-Mission: Per-Asset-Insurance-Status-Tracking.
  * Insured/Uninsured Asset Values (EUR)
  * Premium Total (EUR)
  * Open Claims Count
  * Coverage Gaps

Harte Spec-Regel: NIEMALS Auto-Policy-Buy oder Auto-Policy-Cancel.
Dieses Modul MISST und MELDET nur. Jeder Versuch einer automatischen
Policen-Operation loest AutoPolicyForbidden aus.

Stdlib only. Datei: 150.py
"""

from __future__ import annotations

import datetime
import json
import math
import os

MODULE_ID = "df-150"
REPORT_PREFIX = "df-150"
REPORTS_DIR = "reports"
STOP_FLAG_PATH = os.path.join("/tmp", "df-150.stop")

STATUS_INSURED = "insured"
STATUS_UNDERINSURED = "underinsured"
STATUS_UNINSURED = "uninsured"


class AutoPolicyForbidden(RuntimeError):
    """Spec-Verletzung: automatische Police-Buy/Cancel ist strikt verboten."""


# ------------------------------------------------------------- guards
def auto_policy_buy(*_args, **_kwargs):
    """VERBOTEN (Spec): NIEMALS Auto-Policy-Buy. Raise immer."""
    raise AutoPolicyForbidden(
        "DF-150 Spec-Verbot: Auto-Policy-Buy ist NIEMALS erlaubt. "
        "Policen-Kauf ist eine manuelle Entscheidung."
    )


def auto_policy_cancel(*_args, **_kwargs):
    """VERBOTEN (Spec): NIEMALS Auto-Policy-Cancel. Raise immer."""
    raise AutoPolicyForbidden(
        "DF-150 Spec-Verbot: Auto-Policy-Cancel ist NIEMALS erlaubt. "
        "Policen-Kuendigung ist eine manuelle Entscheidung."
    )


def stop_requested(stop_path=STOP_FLAG_PATH):
    """True, wenn das STOP-Flag-File existiert."""
    return os.path.exists(stop_path)


# ------------------------------------------------------------- helpers
def _eur(x):
    """Auf Cent runden (2 Nachkommastellen)."""
    return round(float(x), 2)


def _non_negative_number(field, x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError("%s muss numerisch sein: %r" % (field, x))
    if not math.isfinite(v) or v < 0.0:
        raise ValueError("%s muss endlich und >= 0 sein: %r" % (field, x))
    return v


# ------------------------------------------------------------- model
def make_asset(asset_id, value_eur, coverage_eur=0.0, premium_eur=0.0,
               open_claims=0, name=""):
    """Erzeugt einen validierten Asset-Record (dict, JSON-tauglich).

    coverage_eur = aktuell versicherte Summe; 0 => unversichert.
    """
    if not asset_id or not str(asset_id).strip():
        raise ValueError("asset_id darf nicht leer sein")
    value = _non_negative_number("value_eur", value_eur)
    coverage = _non_negative_number("coverage_eur", coverage_eur)
    premium = _non_negative_number("premium_eur", premium_eur)
    try:
        claims = int(open_claims)
    except (TypeError, ValueError):
        raise ValueError("open_claims muss ganzzahlig sein: %r" % (open_claims,))
    if claims < 0 or claims != open_claims:
        raise ValueError(
            "open_claims muss eine nicht-negative ganze Zahl sein: %r" % (open_claims,))
    return {
        "asset_id": str(asset_id),
        "name": str(name),
        "value_eur": _eur(value),
        "coverage_eur": _eur(coverage),
        "premium_eur": _eur(premium),
        "open_claims": claims,
    }


def assess_asset(asset):
    """Bewertet EIN Asset: Status, Gap, (Ueber-)Versicherungsanteile."""
    value = _eur(asset["value_eur"])
    coverage = _eur(asset.get("coverage_eur", 0.0))
    gap = _eur(max(0.0, value - coverage))
    over = _eur(max(0.0, coverage - value))
    if gap <= 0.0:
        status = STATUS_INSURED
    elif coverage > 0.0:
        status = STATUS_UNDERINSURED
    else:
        status = STATUS_UNINSURED
    return {
        "asset_id": asset["asset_id"],
        "name": asset.get("name", ""),
        "value_eur": value,
        "coverage_eur": coverage,
        "premium_eur": _eur(asset.get("premium_eur", 0.0)),
        "open_claims": int(asset.get("open_claims", 0)),
        "status": status,
        "insured_value_eur": _eur(min(value, coverage)),
        "uninsured_value_eur": gap,
        "overinsured_eur": over,
    }


def compute_insurance_status(assets):
    """KERN-Funktion: aggregiert alle Assets zum KPM-Coverage-Status."""
    assessed = [assess_asset(a) for a in assets]
    total_value = _eur(sum(a["value_eur"] for a in assessed))
    insured_value = _eur(sum(a["insured_value_eur"] for a in assessed))
    uninsured_value = _eur(sum(a["uninsured_value_eur"] for a in assessed))
    premium_total = _eur(sum(a["premium_eur"] for a in assessed))
    open_claims = int(sum(a["open_claims"] for a in assessed))
    gaps = [
        {
            "asset_id": a["asset_id"],
            "name": a["name"],
            "status": a["status"],
            "gap_eur": a["uninsured_value_eur"],
        }
        for a in assessed
        if a["uninsured_value_eur"] > 0.0
    ]
    ratio = round(insured_value / total_value, 4) if total_value > 0.0 else 1.0
    return {
        "module": MODULE_ID,
        "date": datetime.date.today().isoformat(),
        "asset_count": len(assessed),
        "total_asset_value_eur": total_value,
        "insured_value_eur": insured_value,
        "uninsured_value_eur": uninsured_value,
        "premium_total_eur": premium_total,
        "open_claims_count": open_claims,
        "coverage_ratio": ratio,
        "coverage_gap_count": len(gaps),
        "coverage_gaps": gaps,
        "auto_policy_ops": "forbidden",  # Spec: NIEMALS Auto-Buy/-Cancel
        "assets": assessed,
    }


# ------------------------------------------------------------- io
def write_report(summary, reports_dir=REPORTS_DIR, date=None):
    """Schreibt reports/df-150-{date}.json, gibt den Pfad zurueck."""
    date = date or datetime.date.today().isoformat()
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, "%s-%s.json" % (REPORT_PREFIX, date))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False, sort_keys=True)
    return path


def mock_assets():
    """Mock-Portfolio (Default-Modus, keine echten Daten)."""
    return [
        make_asset("KPM-IMMO-01", 850000.0, coverage_eur=850000.0,
                   premium_eur=2150.0, open_claims=0, name="Familienhaus"),
        make_asset("KPM-DEPOT-01", 420000.0, coverage_eur=300000.0,
                   premium_eur=980.0, open_claims=1, name="Wertpapierdepot"),
        make_asset("KPM-KFZ-01", 65000.0, coverage_eur=0.0,
                   premium_eur=0.0, open_claims=2, name="Oldtimer (unversichert)"),
        make_asset("KPM-KUNST-01", 120000.0, coverage_eur=90000.0,
                   premium_eur=640.0, open_claims=0, name="Kunstsammlung"),
    ]


def main(reports_dir=REPORTS_DIR, stop_path=STOP_FLAG_PATH):
    """Heil-Lauf im Mock-Mode: Status berechnen, Report schreiben."""
    if stop_requested(stop_path):
        print("[%s] STOP-Flag aktiv (%s) - Lauf abgebrochen." % (MODULE_ID, stop_path))
        return None
    summary = compute_insurance_status(mock_assets())
    path = write_report(summary, reports_dir=reports_dir)
    print("[%s] Mock-Lauf OK: %d Assets, gesamt %.2f EUR, davon unversichert %.2f EUR."
          % (MODULE_ID, summary["asset_count"],
             summary["total_asset_value_eur"], summary["uninsured_value_eur"]))
    print("[%s] Praemien gesamt: %.2f EUR | Offene Schadensfaelle: %d | Deckungsluecken: %d"
          % (MODULE_ID, summary["premium_total_eur"],
             summary["open_claims_count"], summary["coverage_gap_count"]))
    print("[%s] Report geschrieben: %s" % (MODULE_ID, path))
    return path


if __name__ == "__main__":
    main()
# [CRUX-MK]
