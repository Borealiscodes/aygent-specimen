#!/usr/bin/env python3
"""
feedback-worker/shp_middleware.py
Non-destructive SHP-v1.0 Spectral Humor Eigenmode middleware hook for aygent-specimen.
Anchors raw feedback payloads via SHA-256 and attaches quantized rational telemetry
before worker execution.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any, Callable

# Ensure repository root `src/` is importable when invoked from `feedback-worker/`
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from humor_eigenmode_router import HumorEigenmodeRouter  # noqa: E402


class SHPWorkerMiddleware:
    """
    Wraps a feedback-worker event handler with bounded SHP-v1.0 spectral routing:
      1. Computes immutable SHA-256 digest of the incoming `message` payload.
      2. Maps message category/mood metadata to bounded stimulus (u0, u1).
      3. Runs Dream-Lane governed modal step (clamping ρ(M) <= 0.96).
      4. Attaches exact rational telemetry without mutating `message`.
    """

    def __init__(self, alpha: float = 0.12, beta: float = 2.40, tau_safe: float = 0.96) -> None:
        self.router = HumorEigenmodeRouter(alpha=alpha, beta=beta, tau_safe=tau_safe)

    @staticmethod
    def _extract_stimulus(event: dict[str, Any]) -> tuple[float, float]:
        """Map feedback category and mood hints onto [u0 (literal), u1 (playful)]."""
        category = str(event.get("category", "")).lower()
        meta = event.get("metadata") or {}
        mood = str(meta.get("mood", "")).lower()

        u0 = 1.0 if category in {"bug", "security", "incident", "audit"} else 0.6
        u1 = 0.6 if mood in {"ecstatic", "playful", "curious"} or category == "compliment" else 0.15
        return u0, u1

    def enrich_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """
        Return a shallow-copied event enriched with `shp_v1_telemetry`.
        Raises ValueError if payload integrity is violated.
        """
        raw_message = str(event.get("message", ""))
        expected_sha256 = hashlib.sha256(raw_message.encode("utf-8")).hexdigest()

        u0, u1 = self._extract_stimulus(event)
        state, tele = self.router.step(fact_payload=raw_message, intent_u0=u0, intent_u1=u1)

        if tele.fact_payload_sha256 != expected_sha256:
            raise ValueError("Seam Integrity Failure: Factual payload SHA-256 mutated during routing.")

        enriched = dict(event)
        enriched["shp_v1_telemetry"] = {
            "protocol": "SHP-v1.0",
            "turn": tele.turn,
            "regime": tele.regime,
            "alpha_effective_pq": f"{tele.alpha_effective.numerator}/{tele.alpha_effective.denominator}",
            "beta_chiral_pq": f"{tele.beta_chiral.numerator}/{tele.beta_chiral.denominator}",
            "spectral_radius_pq": f"{tele.spectral_radius.numerator}/{tele.spectral_radius.denominator}",
            "phase_angle_rad_pq": f"{tele.phase_angle_rad.numerator}/{tele.phase_angle_rad.denominator}",
            "damping_triggered": tele.damping_triggered,
            "fact_payload_sha256": tele.fact_payload_sha256,
            "modal_state": [round(state, 6), round(state, 6)],
        }
        return enriched

    def wrap(self, handler: Callable[[dict[str, Any]], Any]) -> Callable[[dict[str, Any]], Any]:
        """Decorator / wrapper around any existing worker message processor."""
        def _wrapped(event: dict[str, Any]) -> Any:
            enriched_event = self.enrich_event(event)
            return handler(enriched_event)

        return _wrapped
