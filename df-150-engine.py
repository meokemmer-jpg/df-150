
# K16: Concurrent-Spawn-Mutex (fcntl-based, Trinity-CONSERVATIVE 2026-05-17)
def k16_lock_or_exit(df_name: str):
    """Acquire exclusive lock or exit(3). Prevents concurrent DF runs."""
    import fcntl, os, sys
    lock_path = f"/tmp/df-trinity-{df_name}.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_WRONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except BlockingIOError:
        sys.exit(3)


# K13: External-Anchor-Mock-RFC3161 (Trinity-CONSERVATIVE 2026-05-17)
def k13_anchor(payload_hash: str) -> dict:
    """Mock RFC3161-style timestamp anchor."""
    from datetime import datetime, timezone
    return {
        "anchor_type": "rfc3161-mock",
        "iso_ts": datetime.now(timezone.utc).isoformat(),
        "payload_hash": payload_hash,
    }


# K12: HMAC-SHA256-Provenance (Trinity-CONSERVATIVE 2026-05-17)
def k12_provenance(payload: bytes, key: bytes = b"df-trinity-conservative-v1") -> dict:
    """Returns payload_hash + HMAC-SHA256 signature."""
    import hashlib, hmac
    return {
        "payload_hash": hashlib.sha256(payload).hexdigest(),
        "hmac_sha256": hmac.new(key, payload, hashlib.sha256).hexdigest(),
    }

"""DF-150 tracker engine for KPM-Insurance-Coverage.

Tracks per-asset insurance status dimensions and writes a JSON report.
Mock mode is the default. Real API mode is gated by DF_150_REAL_API_ENABLED.
"""

import re
import os
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime, timezone

DF_DIR = Path(__file__).parent
LOCK_DIR = Path("/tmp/df-150.lock")
DF_ID = "150"
DECISION_KEYWORDS_REGEX = re.compile(
    r"\b(entscheid[a-z]*|empfehl(?:e|en|t|st)|sollt(?:e|en|est)|recommend[a-z]*|decid[a-z]*|advis[a-z]*|propos[a-z]*)\b",
    re.IGNORECASE,
)


@dataclass
class TrackerOutput:
    welle: str = "25"
    df: str = "DF-150"
    iso_timestamp: str = ""
    source: str = "mock"
    insured_assets_value_eur: float = 0
    uninsured_assets_value_eur: float = 0
    premium_total_eur: float = 0
    claims_open_count: int = 0
    coverage_gaps: list = field(default_factory=list)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_stable(path, min_age_sec=300) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    try:
        age = time.time() - p.stat().st_mtime
    except OSError:
        return False
    return age >= min_age_sec


def acquire_lock_with_identity() -> bool:
    stale_after_sec = 6 * 60 * 60
    now = time.time()

    try:
        LOCK_DIR.mkdir(mode=0o700)
        identity = {
            "df_id": DF_ID,
            "pid": os.getpid(),
            "created_at": iso_now(),
            "argv": sys.argv,
        }
        (LOCK_DIR / "identity.json").write_text(
            json.dumps(identity, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return True
    except FileExistsError:
        try:
            age = now - LOCK_DIR.stat().st_mtime
        except OSError:
            return False

        if age <= stale_after_sec:
            return False

        try:
            for child in LOCK_DIR.iterdir():
                if child.is_file() or child.is_symlink():
                    child.unlink()
            LOCK_DIR.rmdir()
        except OSError:
            return False

        try:
            LOCK_DIR.mkdir(mode=0o700)
            identity = {
                "df_id": DF_ID,
                "pid": os.getpid(),
                "created_at": iso_now(),
                "stale_lock_replaced": True,
                "argv": sys.argv,
            }
            (LOCK_DIR / "identity.json").write_text(
                json.dumps(identity, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return True
        except FileExistsError:
            return False


def release_lock() -> None:
    try:
        for child in LOCK_DIR.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()
        LOCK_DIR.rmdir()
    except FileNotFoundError:
        return
    except OSError:
        return


def k17_pre_action_verification(anchors) -> dict:
    env_tag = os.getenv("DF_150_ENV_TAG", "local")
    missing_anchors = []

    for anchor in anchors or []:
        if isinstance(anchor, (str, os.PathLike)):
            if not Path(anchor).exists():
                missing_anchors.append(str(anchor))
        elif not anchor:
            missing_anchors.append(str(anchor))

    return {
        "ok": len(missing_anchors) == 0,
        "missing_anchors": missing_anchors,
        "env_tag": env_tag,
    }


def _is_real_api_enabled() -> bool:
    value = os.getenv("DF_150_REAL_API_ENABLED", "false").strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def scan_output_for_decision_keywords(text) -> list:
    if text is None:
        return []
    return sorted({match.group(0) for match in DECISION_KEYWORDS_REGEX.finditer(str(text))})


def assert_no_decision_keywords(output) -> None:
    if isinstance(output, TrackerOutput):
        text = json.dumps(asdict(output), ensure_ascii=False, sort_keys=True)
    elif isinstance(output, (dict, list)):
        text = json.dumps(output, ensure_ascii=False, sort_keys=True)
    else:
        text = str(output)

    hits = scan_output_for_decision_keywords(text)
    if hits:
        raise ValueError(f"Q_0/K_0 decision keyword block triggered: {hits}")


def _float_env(name, default=0.0) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return float(raw)


def _int_env(name, default=0) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def _list_env_json(name) -> list:
    raw = os.getenv(name)
    if not raw:
        return []
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError(f"{name} must contain a JSON list")
    return parsed


def collect_tracker_output() -> TrackerOutput:
    output = TrackerOutput(iso_timestamp=iso_now())

    if not _is_real_api_enabled():
        return output

    output.source = "real_api_env"
    output.insured_assets_value_eur = _float_env("DF_150_INSURED_ASSETS_VALUE_EUR")
    output.uninsured_assets_value_eur = _float_env("DF_150_UNINSURED_ASSETS_VALUE_EUR")
    output.premium_total_eur = _float_env("DF_150_PREMIUM_TOTAL_EUR")
    output.claims_open_count = _int_env("DF_150_CLAIMS_OPEN_COUNT")
    output.coverage_gaps = _list_env_json("DF_150_COVERAGE_GAPS_JSON")
    return output


def main() -> int:
    if not acquire_lock_with_identity():
        return 3

    try:
        pav = k17_pre_action_verification([DF_DIR])
        if not pav.get("ok"):
            report = {
                "welle": "25",
                "df": "DF-150",
                "iso_timestamp": iso_now(),
                "status": "pre_action_verification_failed",
                "k17_pre_action_verification": pav,
            }
            assert_no_decision_keywords(report)
            reports_dir = DF_DIR / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            date_part = datetime.now(timezone.utc).date().isoformat()
            report_path = reports_dir / f"df-150-{date_part}.json"
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            return 3

        output = collect_tracker_output()
        report = asdict(output)
        report["k17_pre_action_verification"] = pav

        assert_no_decision_keywords(report)

        reports_dir = DF_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        date_part = datetime.now(timezone.utc).date().isoformat()
        report_path = reports_dir / f"df-150-{date_part}.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())