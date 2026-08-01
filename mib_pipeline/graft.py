"""Graft Moonshots/hybrid rows with Strobl adjudication for private transfer.

Rule (train-locked): when the hybrid (Moonshots + VisibleScoreFinalizer) row is
APPROVED but Strobl alone is not, and hybrid confidence <= APPROVE_CONF_MAX,
take Strobl adjudication + confidence. Never invent APPROVED.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

# Locked on public train: 136.07 / 150, CFA=0 (2026-07-31).
APPROVE_CONF_MAX = 0.913

_FIELDS = (
    "case_id",
    "applicant_name",
    "species_code",
    "home_world",
    "visa_class",
    "sponsor_id",
    "arrival_date",
    "declared_purpose",
    "risk_flags",
    "fee_status",
    "adjudication",
    "confidence",
)


def graft_row(
    hybrid: Mapping[str, Any],
    strobl: Mapping[str, Any],
    *,
    conf_max: float = APPROVE_CONF_MAX,
) -> dict[str, Any]:
    """Return a schema row: hybrid fields with optional Strobl demote."""

    out = {k: hybrid.get(k) for k in _FIELDS}
    try:
        hy_conf = float(out.get("confidence") or 0.0)
    except (TypeError, ValueError):
        hy_conf = 0.0
    st_adj = str(strobl.get("adjudication") or "")
    hy_adj = str(out.get("adjudication") or "")
    if (
        hy_adj == "APPROVED"
        and st_adj in {"DENIED", "NEEDS_REVIEW"}
        and hy_conf <= conf_max
    ):
        out["adjudication"] = st_adj
        try:
            out["confidence"] = float(strobl.get("confidence"))
        except (TypeError, ValueError):
            out["confidence"] = min(hy_conf, 0.55)
    return out


def graft_maps(
    hybrid_by_id: Mapping[str, Mapping[str, Any]],
    strobl_by_id: Mapping[str, Mapping[str, Any]],
    *,
    conf_max: float = APPROVE_CONF_MAX,
) -> dict[str, dict[str, Any]]:
    """Graft every hybrid case that has a Strobl twin; pass through otherwise."""

    out: dict[str, dict[str, Any]] = {}
    for cid, hy in hybrid_by_id.items():
        st = strobl_by_id.get(cid)
        if st is None:
            out[cid] = {k: hy.get(k) for k in _FIELDS}
        else:
            out[cid] = graft_row(hy, st, conf_max=conf_max)
    return out
