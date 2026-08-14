#!/usr/bin/env python3
"""Static and pure-fixture regression tests for the governed badge contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase" / "migrations" / "20260814113440_governed_badge_awards.sql"
SQL_TEST = ROOT / "supabase" / "tests" / "governed_badge_awards_regression.sql"


def eligible_badges(submissions: int, reports: int, correction_fields: list[str]) -> set[str]:
    """Pure mirror of the SQL eligibility thresholds for fixture testing."""
    badges: set[str] = set()
    if submissions >= 1:
        badges.add("explorer")
    if reports >= 5:
        badges.add("community_hero")
    accessibility = {
        "is_accessible", "is_disabled_access", "has_wheelchair_access",
        "has_grab_rails", "has_lift", "has_adult_changing_place",
        "requires_radar_key",
    }
    family = {
        "has_baby_changing", "has_family_room", "has_baby_changing_inside",
        "has_separate_changing_room", "has_family_toilet", "has_pram_access",
    }
    if sum(field in accessibility for field in correction_fields) >= 3:
        badges.add("accessibility_champion")
    if sum(field in family for field in correction_fields) >= 3:
        badges.add("family_helper")
    return badges


class GovernedBadgeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = MIGRATION.read_text(encoding="utf-8")
        cls.regression_sql = SQL_TEST.read_text(encoding="utf-8")

    def test_migration_has_no_client_award_route(self) -> None:
        self.assertIn("REVOKE INSERT, UPDATE, DELETE", self.sql)
        self.assertIn("REVOKE ALL ON FUNCTION private.award_eligible_badges()", self.sql)
        self.assertNotIn("CREATE POLICY", self.sql)

    def test_migration_has_hardened_idempotent_trigger_contract(self) -> None:
        self.assertIn("SECURITY DEFINER", self.sql)
        self.assertIn("SET search_path = pg_catalog, public", self.sql)
        self.assertEqual(self.sql.count("ON CONFLICT (user_id, badge_type) DO NOTHING"), 4)
        self.assertEqual(self.sql.count("CREATE TRIGGER governed_badges_"), 3)
        self.assertNotRegex(self.sql, r"CREATE FUNCTION public\\.award")

    def test_thresholds_and_field_sets_match_current_client_contract(self) -> None:
        self.assertEqual(eligible_badges(1, 5, ["is_accessible"] * 3), {
            "explorer", "community_hero", "accessibility_champion",
        })
        self.assertEqual(eligible_badges(0, 4, ["has_family_room"] * 2), set())
        self.assertEqual(eligible_badges(0, 4, ["has_family_room"] * 3 + ["unrelated"]), {"family_helper"})

    def test_disposable_sql_assertions_cover_security_properties(self) -> None:
        self.assertIn("has_table_privilege('authenticated', 'public.user_badges', 'INSERT')", self.regression_sql)
        self.assertIn("has_function_privilege('authenticated', 'private.award_eligible_badges()', 'EXECUTE')", self.regression_sql)


if __name__ == "__main__":
    unittest.main()
