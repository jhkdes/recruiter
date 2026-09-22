from __future__ import annotations

from pathlib import Path
import unittest


class MigrationContractTests(unittest.TestCase):
    def test_foundation_migration_contains_milestone_one_tables_and_constraints(self) -> None:
        migration = (Path(__file__).parents[1] / "supabase" / "migrations" / "202609220001_recruiting_foundation.sql").read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE campaigns", migration)
        self.assertIn("CREATE TABLE candidates", migration)
        self.assertIn("CREATE TABLE candidate_evidence", migration)
        self.assertIn("'review_required'", migration)
        self.assertIn("UNIQUE (candidate_id, criterion, source_url, observed_value)", migration)
