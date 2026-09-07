import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# test_150.py — pytest suite for DF-150 KPM Insurance Coverage Tracker
# NOTE: The module file MUST be named '150.py' in the same directory.
# Because '150' is not a valid Python identifier for direct import,
# we use importlib.  The classes are then bound to local names exactly
# as if we had written: from 150 import KPMInsuranceTracker, Asset, ...

import importlib
import json
import os
import tempfile

import pytest

# -- import the module named '150' -------------------------------------------
_150 = importlib.import_module("150")

# -- bind required names to module-level (simulates: from 150 import ...) ----
KPMInsuranceTracker = _150.KPMInsuranceTracker
Asset = _150.Asset
InsurancePolicy = _150.InsurancePolicy
Claim = _150.Claim
create_tracker = _150.create_tracker
STOP_FLAG_PATH = _150.STOP_FLAG_PATH


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

class TestKPMInsuranceTracker:
    """Comprehensive tests for DF-150 core engine."""

    def setup_method(self) -> None:
        self.tracker = KPMInsuranceTracker()
        self._clean_stop_flag()

    def teardown_method(self) -> None:
        self._clean_stop_flag()

    @staticmethod
    def _clean_stop_flag() -> None:
        if os.path.exists(STOP_FLAG_PATH):
            os.remove(STOP_FLAG_PATH)

    # ---- asset registration ------------------------------------------------

    def test_register_asset(self) -> None:
        a = self.tracker.register_asset("A1", "Villa", 1_000_000.0, "real_estate")
        assert a.asset_id == "A1"
        assert a.value_eur == 1_000_000.0
        assert self.tracker.get_asset_count() == 1

    def test_register_duplicate_raises(self) -> None:
        self.tracker.register_asset("A1", "X", 1.0, "other")
        with pytest.raises(ValueError, match="already registered"):
            self.tracker.register_asset("A1", "Y", 2.0, "other")

    def test_remove_asset(self) -> None:
        self.tracker.register_asset("A1", "X", 1.0, "other")
        self.tracker.remove_asset("A1")
        assert self.tracker.get_asset("A1") is None
        assert self.tracker.get_asset_count() == 0

    def test_remove_nonexistent_asset_raises(self) -> None:
        with pytest.raises(KeyError, match="not found"):
            self.tracker.remove_asset("GHOST")

    def test_update_asset_value(self) -> None:
        self.tracker.register_asset("A1", "X", 1.0, "other")
        self.tracker.update_asset_value("A1", 999.0)
        assert self.tracker.get_asset("A1").value_eur == 999.0

    # ---- policy management -------------------------------------------------

    def test_add_policy(self) -> None:
        self.tracker.register_asset("A1", "X", 500_000.0, "real_estate")
        p = self.tracker.add_policy("A1", "P1", "Allianz", 2_000.0, 400_000.0,
                                    "2024-01-01", "2025-01-01")
        assert p.provider == "Allianz"
        assert p.active is True
        assert len(self.tracker.get_asset("A1").policies) == 1

    def test_add_duplicate_policy_raises(self) -> None:
        self.tracker.register_asset("A1", "X", 1.0, "other")
        self.tracker.add_policy("A1", "P1", "A", 1.0, 1.0, "d", "d")
        with pytest.raises(ValueError, match="already exists"):
            self.tracker.add_policy("A1", "P1", "B", 2.0, 2.0, "d", "d")

    def test_set_policy_active(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.add_policy("A1", "P1", "A", 10.0, 100.0, "d", "d")
        self.tracker.set_policy_active("A1", "P1", False)
        assert not self.tracker.get_asset("A1").is_insured()

    def test_remove_policy(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.add_policy("A1", "P1", "A", 10.0, 100.0, "d", "d")
        self.tracker.remove_policy("A1", "P1")
        assert len(self.tracker.get_asset("A1").policies) == 0

    # ---- claim management --------------------------------------------------

    def test_add_claim(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        c = self.tracker.add_claim("A1", "C1", 50.0, "open", "2024-06-01", "desc")
        assert c.status == "open"
        assert c.amount_eur == 50.0
        assert len(self.tracker.get_asset("A1").claims) == 1

    def test_update_claim_status(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.add_claim("A1", "C1", 50.0, "open")
        self.tracker.update_claim_status("A1", "C1", "closed")
        assert self.tracker.get_asset("A1").claims[0].status == "closed"
        assert self.tracker.get_asset("A1").open_claims_count() == 0

    def test_remove_claim(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.add_claim("A1", "C1", 50.0, "open")
        self.tracker.remove_claim("A1", "C1")
        assert len(self.tracker.get_asset("A1").claims) == 0

    def test_remove_nonexistent_claim_raises(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        with pytest.raises(KeyError, match="not found"):
            self.tracker.remove_claim("A1", "GHOST")

    def test_claim_auto_filed_date(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        c = self.tracker.add_claim("A1", "C1", 50.0, "open")
        today = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        assert c.filed_date == today

    # ---- insured / uninsured values ----------------------------------------

    def test_insured_uninsured_values(self) -> None:
        self.tracker.register_asset("A1", "Villa", 1_000_000.0, "real_estate")
        self.tracker.register_asset("A2", "Auto", 50_000.0, "vehicle")
        self.tracker.register_asset("A3", "Ring", 20_000.0, "jewelry")

        self.tracker.add_policy("A1", "P1", "X", 2_000.0, 800_000.0, "d", "d")
        self.tracker.add_policy("A2", "P2", "Y", 500.0, 50_000.0, "d", "d")
        # A3 remains uninsured

        assert self.tracker.calculate_insured_value() == 1_050_000.0
        assert self.tracker.calculate_uninsured_value() == 20_000.0
        assert self.tracker.calculate_total_asset_value() == 1_070_000.0

    def test_all_uninsured(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.register_asset("A2", "Y", 200.0, "other")
        assert self.tracker.calculate_insured_value() == 0.0
        assert self.tracker.calculate_uninsured_value() == 300.0

    def test_all_insured(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.register_asset("A2", "Y", 200.0, "other")
        self.tracker.add_policy("A1", "P1", "X", 1.0, 100.0, "d", "d")
        self.tracker.add_policy("A2", "P2", "Y", 1.0, 200.0, "d", "d")
        assert self.tracker.calculate_insured_value() == 300.0
        assert self.tracker.calculate_uninsured_value() == 0.0

    # ---- premium total -----------------------------------------------------

    def test_premium_total(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.add_policy("A1", "P1", "X", 200.0, 50.0, "d", "d")
        self.tracker.add_policy("A1", "P2", "Y", 300.0, 50.0, "d", "d", active=False)
        assert self.tracker.calculate_premium_total() == 200.0

    # ---- open claims -------------------------------------------------------

    def test_open_claims_count(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.add_claim("A1", "C1", 10.0, "open")
        self.tracker.add_claim("A1", "C2", 20.0, "open")
        self.tracker.add_claim("A1", "C3", 30.0, "closed")
        self.tracker.add_claim("A1", "C4", 40.0, "pending")
        assert self.tracker.count_open_claims() == 2
        assert self.tracker.calculate_open_claims_value() == 30.0

    def test_no_open_claims(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        assert self.tracker.count_open_claims() == 0
        assert self.tracker.calculate_open_claims_value() == 0.0

    # ---- coverage gaps -----------------------------------------------------

    def test_detect_coverage_gaps(self) -> None:
        self.tracker.register_asset("A1", "Villa", 1_000_000.0, "real_estate")
        self.tracker.register_asset("A2", "Auto", 50_000.0, "vehicle")
        self.tracker.register_asset("A3", "Ring", 20_000.0, "jewelry")

        self.tracker.add_policy("A1", "P1", "X", 2_000.0, 800_000.0, "d", "d")  # gap 200k
        self.tracker.add_policy("A2", "P2", "Y", 500.0, 50_000.0, "d", "d")     # fully covered
        # A3 uninsured → gap 20k

        gaps = self.tracker.detect_coverage_gaps()
        assert len(gaps) == 2
        gap_ids = {g["asset_id"] for g in gaps}
        assert gap_ids == {"A1", "A3"}

        villa = next(g for g in gaps if g["asset_id"] == "A1")
        assert villa["coverage_gap_eur"] == 200_000.0
        assert villa["gap_percentage"] == 20.0

        ring = next(g for g in gaps if g["asset_id"] == "A3")
        assert ring["coverage_gap_eur"] == 20_000.0
        assert ring["gap_percentage"] == 100.0

    def test_no_coverage_gaps(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.add_policy("A1", "P1", "X", 1.0, 100.0, "d", "d")
        assert self.tracker.detect_coverage_gaps() == []

    def test_overinsured_no_gap(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.add_policy("A1", "P1", "X", 1.0, 200.0, "d", "d")
        assert self.tracker.detect_coverage_gaps() == []

    # ---- asset-level methods -----------------------------------------------

    def test_asset_is_insured(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        a = self.tracker.get_asset("A1")
        assert not a.is_insured()
        self.tracker.add_policy("A1", "P1", "X", 1.0, 50.0, "d", "d")
        assert a.is_insured()

    def test_asset_coverage_gap_zero_value(self) -> None:
        self.tracker.register_asset("A1", "X", 0.0, "other")
        self.tracker.add_policy("A1", "P1", "X", 1.0, 1000.0, "d", "d")
        a = self.tracker.get_asset("A1")
        assert a.coverage_gap() == 0.0
        assert not a.has_coverage_gap()

    def test_multiple_policies_coverage_sum(self) -> None:
        self.tracker.register_asset("A1", "X", 1_000.0, "other")
        self.tracker.add_policy("A1", "P1", "X", 10.0, 300.0, "d", "d")
        self.tracker.add_policy("A1", "P2", "Y", 20.0, 400.0, "d", "d")
        self.tracker.add_policy("A1", "P3", "Z", 30.0, 300.0, "d", "d")
        a = self.tracker.get_asset("A1")
        assert a.total_coverage() == 1_000.0
        assert a.total_premium() == 60.0
        assert a.coverage_gap() == 0.0

    # ---- report generation -------------------------------------------------

    def test_generate_report_structure(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.add_policy("A1", "P1", "X", 10.0, 100.0, "d", "d")
        self.tracker.add_claim("A1", "C1", 5.0, "open")

        r = self.tracker.generate_report()
        assert r["report_metadata"]["factory"] == "df-150"
        assert r["report_metadata"]["wave"] == "W51-B"
        assert r["report_metadata"]["domain"] == "K_0"
        assert r["summary"]["total_assets"] == 1
        assert r["summary"]["insured_value_eur"] == 100.0
        assert r["summary"]["premium_total_eur"] == 10.0
        assert r["summary"]["open_claims_count"] == 1
        assert r["summary"]["coverage_gaps_count"] == 0
        assert len(r["per_asset"]) == 1

    def test_generate_report_mixed(self) -> None:
        self.tracker.register_asset("A1", "Villa", 1_000_000.0, "real_estate")
        self.tracker.register_asset("A2", "Auto", 50_000.0, "vehicle")
        self.tracker.register_asset("A3", "Ring", 20_000.0, "jewelry")

        self.tracker.add_policy("A1", "P1", "X", 2_000.0, 800_000.0, "d", "d")
        self.tracker.add_policy("A2", "P2", "Y", 500.0, 50_000.0, "d", "d")
        self.tracker.add_claim("A1", "C1", 10_000.0, "open")
        self.tracker.add_claim("A2", "C2", 2_000.0, "closed")

        r = self.tracker.generate_report()
        s = r["summary"]
        assert s["total_asset_value_eur"] == 1_070_000.0
        assert s["insured_value_eur"] == 1_050_000.0
        assert s["uninsured_value_eur"] == 20_000.0
        assert s["premium_total_eur"] == 2_500.0
        assert s["open_claims_count"] == 1
        assert s["coverage_gaps_count"] == 2
        assert len(r["per_asset"]) == 3

    def test_empty_report(self) -> None:
        r = self.tracker.generate_report()
        assert r["summary"]["total_assets"] == 0
        assert r["summary"]["total_asset_value_eur"] == 0.0
        assert r["coverage_gaps"] == []
        assert r["per_asset"] == []

    # ---- report saving -----------------------------------------------------

    def test_save_report(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        with tempfile.TemporaryDirectory() as d:
            fp = self.tracker.save_report("2024-12-01", output_dir=d)
            assert os.path.exists(fp)
            assert "df-150-2024-12-01.json" in fp
            with open(fp) as fh:
                data = json.load(fh)
            assert data["summary"]["total_assets"] == 1

    def test_save_report_to_path(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        with tempfile.TemporaryDirectory() as d:
            custom = os.path.join(d, "out.json")
            result = self.tracker.save_report_to_path(custom)
            assert result == custom
            assert os.path.exists(custom)

    # ---- stop flag ---------------------------------------------------------

    def test_stop_flag_not_present(self) -> None:
        self._clean_stop_flag()
        assert self.tracker.check_stop_flag() is False

    def test_set_and_check_stop_flag(self) -> None:
        self.tracker.set_stop_flag()
        assert os.path.exists(STOP_FLAG_PATH)
        assert self.tracker.check_stop_flag() is True

    def test_clear_stop_flag(self) -> None:
        self.tracker.set_stop_flag()
        self.tracker.clear_stop_flag()
        assert self.tracker.check_stop_flag() is False

    def test_stop_flag_in_report_metadata(self) -> None:
        self.tracker.register_asset("A1", "X", 1.0, "other")
        assert self.tracker.generate_report()["report_metadata"]["stop_flag_active"] is False
        self.tracker.set_stop_flag()
        assert self.tracker.generate_report()["report_metadata"]["stop_flag_active"] is True
        self.tracker.clear_stop_flag()

    # ---- factory function --------------------------------------------------

    def test_create_tracker_factory(self) -> None:
        t = create_tracker("TestPortfolio")
        assert t.portfolio_name == "TestPortfolio"
        t.register_asset("A1", "X", 1.0, "other")
        assert t.get_asset_count() == 1

    # ---- edge cases --------------------------------------------------------

    def test_add_policy_nonexistent_asset_raises(self) -> None:
        with pytest.raises(KeyError, match="not found"):
            self.tracker.add_policy("GHOST", "P1", "X", 1.0, 1.0, "d", "d")

    def test_add_claim_nonexistent_asset_raises(self) -> None:
        with pytest.raises(KeyError, match="not found"):
            self.tracker.add_claim("GHOST", "C1", 1.0, "open")

    def test_active_policy_count_in_summary(self) -> None:
        self.tracker.register_asset("A1", "X", 100.0, "other")
        self.tracker.add_policy("A1", "P1", "X", 1.0, 50.0, "d", "d")
        self.tracker.add_policy("A1", "P2", "Y", 1.0, 50.0, "d", "d", active=False)
        s = self.tracker.get_asset_summaries()[0]
        assert s["policy_count"] == 2
        assert s["active_policy_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
