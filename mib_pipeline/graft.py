"""Graft Moonshots/hybrid rows with Strobl (+ optional Gole) for private transfer.

Rules (private-first):

1. Demote: if hybrid is APPROVED and Strobl is DENIED → always take Strobl.
2. Demote: if hybrid is APPROVED and Strobl is NEEDS_REVIEW and hybrid
   confidence <= APPROVE_CONF_MAX (0.913) → take Strobl.
3. Promote: if hybrid is NEEDS_REVIEW and Strobl is APPROVED and Strobl
   confidence >= PROMOTE_CONF_MIN (0.90) → take Strobl APPROVED.
4. Gole fields (optional): overwrite scored fields from nonempty Gole values.
5. Gole dual-DENIED: if still NEEDS_REVIEW and both Strobl+Gole are DENIED → DENIED.
6. Gole promote: if still NEEDS_REVIEW and Gole APPROVED conf >= GOLE_PROMOTE_MIN
   (0.90) → APPROVED.

Locked train (champion + Strobl + Gole): **137.30 / 150, CFA = 0**.
"""

from __future__ import annotations

from typing import Any, Mapping

# Locked demote cut (CFA=0 frontier).
APPROVE_CONF_MAX = 0.913
# Locked Strobl promote floor.
PROMOTE_CONF_MIN = 0.90
# Locked Gole promote floor (CFA=0 with dual-DENIED).
GOLE_PROMOTE_MIN = 0.90

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

_SCORED_FIELDS = (
    "applicant_name",
    "species_code",
    "home_world",
    "visa_class",
    "sponsor_id",
    "arrival_date",
    "declared_purpose",
    "fee_status",
)


def _conf(row: Mapping[str, Any], default: float = 0.0) -> float:
    try:
        return float(row.get("confidence") or default)
    except (TypeError, ValueError):
        return default


def graft_row(
    hybrid: Mapping[str, Any],
    strobl: Mapping[str, Any],
    gole: Mapping[str, Any] | None = None,
    *,
    conf_max: float = APPROVE_CONF_MAX,
    promote_conf_min: float = PROMOTE_CONF_MIN,
    gole_promote_min: float = GOLE_PROMOTE_MIN,
    always_demote_denied: bool = True,
    allow_promote: bool = True,
    take_gole_fields: bool = True,
    allow_gole_promote: bool = True,
    allow_dual_denied: bool = True,
) -> dict[str, Any]:
    """Hybrid fields with Strobl demote/promote and optional Gole field/class graft."""

    out = {k: hybrid.get(k) for k in _FIELDS}
    hy_conf = _conf(out)
    st_conf = _conf(strobl)
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
    elif (
        allow_promote
        and hy_adj == "NEEDS_REVIEW"
        and st_adj == "APPROVED"
        and st_conf >= promote_conf_min
    ):
        out["adjudication"] = "APPROVED"
        out["confidence"] = st_conf

    if gole is None:
        return out

    if take_gole_fields:
        for field in _SCORED_FIELDS:
            value = gole.get(field)
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            if value == "" or value == []:
                continue
            out[field] = value

    go_adj = str(gole.get("adjudication") or "")
    go_conf = _conf(gole)
    cur = str(out.get("adjudication") or "")

    if (
        allow_dual_denied
        and cur == "NEEDS_REVIEW"
        and st_adj == "DENIED"
        and go_adj == "DENIED"
    ):
        out["adjudication"] = "DENIED"
        out["confidence"] = st_conf if st_conf > 0 else 0.55
        return out

    if (
        allow_gole_promote
        and cur == "NEEDS_REVIEW"
        and go_adj == "APPROVED"
        and go_conf >= gole_promote_min
    ):
        out["adjudication"] = "APPROVED"
        out["confidence"] = go_conf

    return out


def graft_maps(
    hybrid_by_id: Mapping[str, Mapping[str, Any]],
    strobl_by_id: Mapping[str, Mapping[str, Any]],
    gole_by_id: Mapping[str, Mapping[str, Any]] | None = None,
    *,
    conf_max: float = APPROVE_CONF_MAX,
    promote_conf_min: float = PROMOTE_CONF_MIN,
    gole_promote_min: float = GOLE_PROMOTE_MIN,
    always_demote_denied: bool = True,
    allow_promote: bool = True,
    take_gole_fields: bool = True,
    allow_gole_promote: bool = True,
    allow_dual_denied: bool = True,
) -> dict[str, dict[str, Any]]:
    """Graft every hybrid case; optional Gole map keyed by case_id."""

    gole_by_id = gole_by_id or {}
    out: dict[str, dict[str, Any]] = {}
    for cid, hy in hybrid_by_id.items():
        st = strobl_by_id.get(cid)
        go = gole_by_id.get(cid)
        if st is None:
            row = {k: hy.get(k) for k in _FIELDS}
            if go is not None and take_gole_fields:
                for field in _SCORED_FIELDS:
                    value = go.get(field)
                    if value not in (None, "", []):
                        row[field] = value
            out[cid] = row
        else:
            out[cid] = graft_row(
                hy,
                st,
                go,
                conf_max=conf_max,
                promote_conf_min=promote_conf_min,
                gole_promote_min=gole_promote_min,
                always_demote_denied=always_demote_denied,
                allow_promote=allow_promote,
                take_gole_fields=take_gole_fields,
                allow_gole_promote=allow_gole_promote,
                allow_dual_denied=allow_dual_denied,
            )
    return out
