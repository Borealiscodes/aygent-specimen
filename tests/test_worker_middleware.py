#!/usr/bin/env python3
"""Standard-library unit tests for feedback-worker/shp_middleware.py (zero dependencies)."""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "feedback-worker"))

from shp_middleware import SHPWorkerMiddleware  # noqa: E402


class TestSHPWorkerMiddleware(unittest.TestCase):
    def test_enriches_event_and_preserves_message_sha256(self) -> None:
        middleware = SHPWorkerMiddleware(alpha=0.12, beta=2.40)
        original_event = {
            "user_id": "hue123",
            "message": "This feedback pipeline is working smoothly!",
            "category": "compliment",
            "metadata": {"source": "web", "mood": "ecstatic"},
        }
        expected_hash = hashlib.sha256(original_event["message"].encode("utf-8")).hexdigest()

        @middleware.wrap
        def dummy_worker_handler(event: dict) -> dict:
            return event

        processed = dummy_worker_handler(original_event)

        # 1. Original dictionary is not mutated in place
        self.assertNotIn("shp_v1_telemetry", original_event)

        # 2. Message body and SHA-256 provenance remain intact
        self.assertEqual(processed["message"], original_event["message"])
        tele = processed["shp_v1_telemetry"]
        self.assertEqual(tele["protocol"], "SHP-v1.0")
        self.assertEqual(tele["fact_payload_sha256"], expected_hash)
        self.assertEqual(tele["regime"], "CHROMATIC_STANDING_WAVE")
        self.assertFalse(tele["damping_triggered"])

    def test_audit_category_maps_to_high_literal_stimulus(self) -> None:
        middleware = SHPWorkerMiddleware()
        u0, u1 = middleware._extract_stimulus({"category": "security", "metadata": {"mood": "neutral"}})
        self.assertEqual(u0, 1.0)
        self.assertEqual(u1, 0.15)

    def test_dream_lane_governor_clamps_unstable_middleware_config(self) -> None:
        unstable_middleware = SHPWorkerMiddleware(alpha=0.95, beta=3.50, tau_safe=0.96)
        event = {"message": "Unbounded coupling test", "category": "bug"}
        enriched = unstable_middleware.enrich_event(event)
        tele = enriched["shp_v1_telemetry"]
        self.assertTrue(tele["damping_triggered"])
        self.assertEqual(tele["regime"], "DIVERGENT_DRIFT_DAMPED")


if __name__ == "__main__":
    unittest.main()
