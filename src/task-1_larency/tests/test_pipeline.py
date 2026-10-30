import unittest
from pipeline import SourceNormaliserPipeline

class TestTask1Pipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = SourceNormaliserPipeline()

    def test_valid_primary_source(self):
        data = [{
            "id": "SRC-001", "raw_url": "https://gov.de/doc", "canonical_url": "https://gov.de/doc",
            "publisher": "Gov", "source_type": "authoritative_gov", "publication_date": "2026-01-01",
            "content": "Official standards", "discovery_channel": "audit"
        }]
        res = self.pipeline.run(data)
        self.assertEqual(len(res["eligible"]), 1)
        self.assertEqual(res["eligible"][0]["eligibility"], "ELIGIBLE")

    def test_deduplication_preserves_provenance(self):
        data = [
            {"id": "SRC-001", "raw_url": "https://site.com/a?ref=1", "canonical_url": "https://site.com/a", "publisher": "P", "source_type": "primary_documentation", "publication_date": "2026-01-01", "content": "Text", "discovery_channel": "ch1"},
            {"id": "SRC-002", "raw_url": "https://site.com/a?ref=2", "canonical_url": "https://site.com/a", "publisher": "P", "source_type": "primary_documentation", "publication_date": "2026-01-01", "content": "Text", "discovery_channel": "ch2"}
        ]
        res = self.pipeline.run(data)
        self.assertEqual(len(res["eligible"]), 1)
        self.assertEqual(len(res["eligible"][0]["discovery_lineage"]), 2)

    def test_unknown_date_remains_none(self):
        data = [{
            "id": "SRC-005", "raw_url": "https://gov.de/doc", "canonical_url": "https://gov.de/doc",
            "publisher": "Gov", "source_type": "authoritative_gov", "publication_date": None,
            "content": "Official standards", "discovery_channel": "audit"
        }]
        res = self.pipeline.run(data)
        self.assertIsNone(res["eligible"][0]["publication_date"])

    def test_competitor_promotional_claim_excluded(self):
        data = [{
            "id": "SRC-003", "raw_url": "https://comp.com/a", "canonical_url": "https://comp.com/a",
            "publisher": "Comp", "source_type": "competitor", "publication_date": "2026-01-01",
            "content": "Our Cloud is cheaper and better!", "discovery_channel": "rss"
        }]
        res = self.pipeline.run(data)
        self.assertEqual(len(res["excluded"]), 1)
        self.assertIn("EXCLUDE_COMPETITOR_PROMOTIONAL_CLAIM", res["excluded"][0]["reason_codes"])

    def test_competitor_generic_claim_requires_verification(self):
        data = [{
            "id": "SRC-004", "raw_url": "https://comp.com/b", "canonical_url": "https://comp.com/b",
            "publisher": "Comp", "source_type": "competitor", "publication_date": "2026-01-01",
            "content": "EU introduced new GDPR rules.", "discovery_channel": "web"
        }]
        res = self.pipeline.run(data)
        self.assertEqual(len(res["excluded"]), 1)
        self.assertIn("COMPETITOR_GENERIC_CLAIM_REQUIRES_INDEPENDENT_VERIFICATION", res["excluded"][0]["reason_codes"])

    def test_malformed_input_handled(self):
        data = [{"id": "SRC-006_INVALID", "raw_url": "invalid-url"}]
        res = self.pipeline.run(data)
        self.assertEqual(len(res["validation_errors"]), 1)

if __name__ == "__main__":
    unittest.main()