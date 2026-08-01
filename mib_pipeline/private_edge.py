"""Private-transfer demote layer on top of strobl's VisibleScoreFinalizer.

Never invents APPROVED. Only demotes / hard-denies on portable policy signals
that may still slip past the upstream finalizer on private packets.
"""

from __future__ import annotations

from pathlib import Path

from .models import PredictionRow
from .score_finalizer import VisibleScoreFinalizer

_BARRED = frozenset({"SPN-0007", "SPN-0139", "SPN-4040"})
_DISQUALIFYING = frozenset(
    {
        "memory_tampering",
        "planetary_embargo",
        "active_warrant",
        "biohazard_red",
    }
)
_REVIEW_ONLY = frozenset(
    {
        "identity_conflict",
        "sponsor_mismatch",
        "illegible_biometrics",
        "rescinded_denial",
    }
)
_SOFT_EMBARGO = frozenset({"Wolf-1061c"})


def _flag_set(value: str | None) -> set[str]:
    raw = str(value or "none").strip()
    if not raw or raw.casefold() == "none":
        return set()
    return {part for part in raw.split("|") if part and part != "none"}


def apply_private_demote(row: PredictionRow) -> PredictionRow:
    """One-way demote after the strobl visible finalizer."""

    if row.adjudication != "APPROVED":
        return row

    payload = row.to_dict()
    flags = _flag_set(row.risk_flags)
    visa = row.visa_class
    fee = row.fee_status
    sponsor = row.sponsor_id
    home = row.home_world

    if flags & _DISQUALIFYING or visa == "TRANSIT-7":
        payload["adjudication"] = "DENIED"
        payload["confidence"] = 0.98
        return PredictionRow.from_mapping(payload, fallback_case_id=row.case_id)

    if sponsor in _BARRED and visa != "DIP-1":
        payload["adjudication"] = "DENIED"
        payload["confidence"] = 0.98
        return PredictionRow.from_mapping(payload, fallback_case_id=row.case_id)

    if home in _SOFT_EMBARGO and visa != "DIP-1":
        payload["adjudication"] = "DENIED"
        payload["confidence"] = 0.98
        return PredictionRow.from_mapping(payload, fallback_case_id=row.case_id)

    if fee == "unpaid":
        payload["adjudication"] = "DENIED"
        payload["confidence"] = 0.98
        return PredictionRow.from_mapping(payload, fallback_case_id=row.case_id)

    if fee == "unknown" or flags & _REVIEW_ONLY:
        payload["adjudication"] = "NEEDS_REVIEW"
        payload["confidence"] = min(float(row.confidence), 0.55)
        return PredictionRow.from_mapping(payload, fallback_case_id=row.case_id)

    if visa != "DIP-1" and sponsor in {"", "unknown", "SPN-0000"}:
        payload["adjudication"] = "NEEDS_REVIEW"
        payload["confidence"] = min(float(row.confidence), 0.55)
        return PredictionRow.from_mapping(payload, fallback_case_id=row.case_id)

    name = str(row.applicant_name or "").strip().casefold()
    if name in {"", "unknown"} and visa != "DIP-1":
        payload["adjudication"] = "NEEDS_REVIEW"
        payload["confidence"] = min(float(row.confidence), 0.55)
        return PredictionRow.from_mapping(payload, fallback_case_id=row.case_id)

    return row


class PrivateVisibleFinalizer:
    """Strobl visible finalizer + demote-only private edge."""

    def __init__(self) -> None:
        self._inner = VisibleScoreFinalizer()

    def __call__(self, pdf_path: Path, row: PredictionRow) -> PredictionRow:
        return apply_private_demote(self._inner(pdf_path, row))
