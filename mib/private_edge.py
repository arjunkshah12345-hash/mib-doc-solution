"""Tiny private-transfer edges on top of the Calling Moonshots / tyler runtime.

These never invent APPROVED. They only demote, or raise the bar for the
score-optimal review resolver (which the upstream memo links to 12 CFAs).
"""

from __future__ import annotations

import os
import re

# Field manual + public revoked list (same portable constants upstream uses).
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


def apply_emitted_demote(prediction: dict) -> dict:
    """One-way policy demote after upstream decide/resolver."""

    if prediction.get("adjudication") != "APPROVED":
        return prediction

    out = dict(prediction)
    flags = _flag_set(out.get("risk_flags"))
    visa = str(out.get("visa_class") or "")
    fee = str(out.get("fee_status") or "")
    sponsor = str(out.get("sponsor_id") or "")
    home = str(out.get("home_world") or "")

    if flags & _DISQUALIFYING or visa == "TRANSIT-7":
        out["adjudication"] = "DENIED"
        out["confidence"] = 0.95
        return out

    if sponsor in _BARRED and visa != "DIP-1":
        out["adjudication"] = "DENIED"
        out["confidence"] = 0.95
        return out

    if home in _SOFT_EMBARGO and visa != "DIP-1":
        out["adjudication"] = "DENIED"
        out["confidence"] = 0.95
        return out

    if fee == "unpaid":
        out["adjudication"] = "DENIED"
        out["confidence"] = 0.95
        return out

    if fee == "unknown" or flags & _REVIEW_ONLY:
        out["adjudication"] = "NEEDS_REVIEW"
        out["confidence"] = min(float(out.get("confidence") or 0.55), 0.55)
        return out

    if visa != "DIP-1" and sponsor in {"", "unknown", "SPN-0000"}:
        out["adjudication"] = "NEEDS_REVIEW"
        out["confidence"] = min(float(out.get("confidence") or 0.55), 0.55)
        return out

    name = str(out.get("applicant_name") or "").strip().casefold()
    if name in {"", "unknown"} and visa != "DIP-1":
        out["adjudication"] = "NEEDS_REVIEW"
        out["confidence"] = min(float(out.get("confidence") or 0.55), 0.55)
        return out

    return out


def configure_private_defaults() -> None:
    """Raise resolver APPROVED margin unless the operator overrides it.

    Upstream ships ``MIB_REVIEW_MARGIN=0`` (score-optimal). A small positive
    margin keeps most of their OCR/clerk lift while cutting the weakest
    insufficient_evidence → APPROVED bets (their documented CFA risk).
    """

    os.environ.setdefault("MIB_REVIEW_MARGIN", "0.35")
    # Keep their OCR path on; never enable answer-key style channels here.
    os.environ.setdefault("MIB_REVIEW_MODEL", "1")
