# DF-150 KPM-Insurance-Coverage [CRUX-MK]

**Status:** SKELETON-CONDITIONAL (Welle-51 W51-B Skeleton-Wave-2)
**Domain:** K_0 (KPM Familien-Vermoegen-Schutz)
**Welle:** 25

## Mission

Per-Asset-Insurance-Status-Tracking fuer KPM. Tracking:
- Insured/Uninsured Asset Values (EUR)
- Premium Total (EUR)
- Open Claims Count
- Coverage Gaps

**NIEMALS Auto-Policy-Buy oder Auto-Policy-Cancel.**

## Usage

```bash
cd ~/Projects/dark-factories/df-150
python df-150-engine.py        # Mock-Mode default
pytest tests/                   # Existing tests
```

## Output

- Reports: `reports/df-150-{date}.json`
- STOP-Flag: `/tmp/df-150.stop`

[CRUX-MK]
