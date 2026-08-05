"""Graft Moonshots/hybrid rows with Strobl adjudication for private transfer.

Rules (private-first — never invent APPROVED from a weak clerk):

1. Demote: if hybrid is APPROVED and Strobl is DENIED → always take Strobl.
2. Demote: if hybrid is APPROVED and Strobl is NEEDS_REVIEW and hybrid
   confidence <= APPROVE_CONF_MAX (0.913) → take Strobl.
3. Promote: if hybrid is NEEDS_REVIEW and Strobl is APPROVED and Strobl
   confidence >= PROMOTE_CONF_MIN (0.90) → take Strobl APPROVED.
   Measured on locked champion + Strobl train: 136.07 → 136.71, CFA=0
   (12 true approvals recovered; 2 review→approve mistakes; 0 CFA).
   Mechanism: the conservative clerk high-conf approving a hybrid review.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

# Locked demote cut (CFA=0 frontier).
APPROVE_CONF_MAX = 0.913
# Locked promote floor (train-measured CFA=0; raises class score).
PROMOTE_CONF_MIN = 0.90

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
    promote_conf_min: float = PROMOTE_CONF_MIN,
    always_demote_denied: bool = True,
    allow_promote: bool = True,
) -> dict[str, Any]:
    """Return a schema row: hybrid fields with optional Strobl demote/promote."""

    out = {k: hybrid.get(k) for k in _FIELDS}
    try:
        hy_conf = float(out.get("confidence") or 0.0)
    except (TypeError, ValueError):
        hy_conf = 0.0
    try:
        st_conf = float(strobl.get("confidence") or 0.0)
    except (TypeError, ValueError):
        st_conf = 0.0
    st_adj = str(strobl.get("adjudication") or "")
    hy_adj = str(out.get("adjudication") or "")

    demote = False
    if hy_adj == "APPROVED" and st_adj == "DENIED" and always_demote_denied:
        demote = True
    elif (
        hy_adj == "APPROVED"
        and st_adj in {"DENIED", "NEEDS_REVIEW"}
        and hy_conf <= conf_max
    ):
        demote = True

    if demote:
        out["adjudication"] = st_adj
        try:
            out["confidence"] = float(strobl.get("confidence"))
        except (TypeError, ValueError):
            out["confidence"] = min(hy_conf, 0.55)
        return out

    if (
        allow_promote
        and hy_adj == "NEEDS_REVIEW"
        and st_adj == "APPROVED"
        and st_conf >= promote_conf_min
    ):
        out["adjudication"] = "APPROVED"
        out["confidence"] = st_conf
    return out


def graft_maps(
    hybrid_by_id: Mapping[str, Mapping[str, Any]],
    strobl_by_id: Mapping[str, Mapping[str, Any]],
    *,
    conf_max: float = APPROVE_CONF_MAX,
    promote_conf_min: float = PROMOTE_CONF_MIN,
    always_demote_denied: bool = True,
    allow_promote: bool = True,
) -> dict[str, dict[str, Any]]:
    """Graft every hybrid case that has a Strobl twin; pass through otherwise."""

    out: dict[str, dict[str, Any]] = {}
    for cid, hy in hybrid_by_id.items():
        st = strobl_by_id.get(cid)
        if st is None:
            out[cid] = {k: hy.get(k) for k in _FIELDS}
        else:
            out[cid] = graft_row(
                hy,
                st,
                conf_max=conf_max,
                promote_conf_min=promote_conf_min,
                always_demote_denied=always_demote_denied,
                allow_promote=allow_promote,
            )
    return out
