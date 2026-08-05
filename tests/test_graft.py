"""Unit tests for private-first Strobl graft demote."""

from __future__ import annotations

from mib_pipeline.graft import graft_row


def _row(adj: str, conf: float, case_id: str = "c1") -> dict:
    return {
        "case_id": case_id,
        "applicant_name": "A",
        "species_code": "HUM",
        "home_world": "EARTH",
        "visa_class": "XW-1",
        "sponsor_id": "S1",
        "arrival_date": "2024-01-01",
        "declared_purpose": "WORK",
        "risk_flags": [],
        "fee_status": "PAID",
        "adjudication": adj,
        "confidence": conf,
    }


def test_high_conf_denied_always_demotes():
    hy = _row("APPROVED", 0.99)
    st = _row("DENIED", 0.8)
    out = graft_row(hy, st)
    assert out["adjudication"] == "DENIED"
    assert out["confidence"] == 0.8


def test_high_conf_needs_review_does_not_demote():
    """Raising the review cut reopens CFA — keep 0.913 gate only."""
    hy = _row("APPROVED", 0.95)
    st = _row("NEEDS_REVIEW", 0.4)
    out = graft_row(hy, st, conf_max=0.913)
    assert out["adjudication"] == "APPROVED"
    assert out["confidence"] == 0.95


def test_mid_conf_needs_review_demotes():
    hy = _row("APPROVED", 0.90)
    st = _row("NEEDS_REVIEW", 0.55)
    out = graft_row(hy, st, conf_max=0.913)
    assert out["adjudication"] == "NEEDS_REVIEW"
    assert out["confidence"] == 0.55


def test_never_invents_approved_below_floor():
    """Promote only at >= 0.90 Strobl APPROVED; below floor stays review."""
    hy = _row("NEEDS_REVIEW", 0.4)
    st = _row("APPROVED", 0.899)
    out = graft_row(hy, st)
    assert out["adjudication"] == "NEEDS_REVIEW"


def test_legacy_flag_skips_high_conf_denied():
    hy = _row("APPROVED", 0.99)
    st = _row("DENIED", 0.8)
    out = graft_row(hy, st, always_demote_denied=False, conf_max=0.913)
    assert out["adjudication"] == "APPROVED"


def test_high_conf_strobl_approve_promotes_review():
    hy = _row("NEEDS_REVIEW", 0.4)
    st = _row("APPROVED", 0.92)
    out = graft_row(hy, st)
    assert out["adjudication"] == "APPROVED"
    assert out["confidence"] == 0.92


def test_low_conf_strobl_approve_does_not_promote():
    hy = _row("NEEDS_REVIEW", 0.4)
    st = _row("APPROVED", 0.80)
    out = graft_row(hy, st)
    assert out["adjudication"] == "NEEDS_REVIEW"


def test_promote_disabled():
    hy = _row("NEEDS_REVIEW", 0.4)
    st = _row("APPROVED", 0.95)
    out = graft_row(hy, st, allow_promote=False)
    assert out["adjudication"] == "NEEDS_REVIEW"


def test_gole_fields_overwrite():
    hy = _row("NEEDS_REVIEW", 0.4)
    st = _row("NEEDS_REVIEW", 0.4)
    go = _row("NEEDS_REVIEW", 0.4)
    go["fee_status"] = "waived"
    go["species_code"] = "JOVIAN_GASFORM"
    out = graft_row(hy, st, go)
    assert out["fee_status"] == "waived"
    assert out["species_code"] == "JOVIAN_GASFORM"


def test_gole_dual_denied():
    hy = _row("NEEDS_REVIEW", 0.4)
    st = _row("DENIED", 0.6)
    go = _row("DENIED", 0.55)
    out = graft_row(hy, st, go)
    assert out["adjudication"] == "DENIED"


def test_gole_high_conf_promote():
    hy = _row("NEEDS_REVIEW", 0.4)
    st = _row("NEEDS_REVIEW", 0.3)
    go = _row("APPROVED", 0.95)
    out = graft_row(hy, st, go)
    assert out["adjudication"] == "APPROVED"
    assert out["confidence"] == 0.95


def test_gole_low_conf_no_promote():
    hy = _row("NEEDS_REVIEW", 0.4)
    st = _row("NEEDS_REVIEW", 0.3)
    go = _row("APPROVED", 0.85)
    out = graft_row(hy, st, go)
    assert out["adjudication"] == "NEEDS_REVIEW"
