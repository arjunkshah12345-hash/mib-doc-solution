# Experiments — private-first graft

Record of measured configs. No claim without a receipt.

| ID | Hypothesis | Config | Split | Total | CFA | Runtime note | Decision |
|----|------------|--------|-------|------:|----:|--------------|----------|
| E0 | Strobl alone is CFA-safe | strobl pipeline + finalizer | full train 1k | ~132.8–130.37* | 0 | *PR body 130.37; local runs varied by tip | Keep as second opinion |
| E1 | Moonshots raw | tyler/Moonshots tip | full train 1k | ~134.6 | ~9 | Strong fields; CFA poison | Reject solo |
| E2 | Moonshots + priv floor 0.62 | `MIB_MIN_APPROVE_CONF=0.62` + margin/edge | full train 1k | 133.47 | 3 | Safer but still CFA | Interim ship only |
| E3 | Hybrid MS+Strobl fields | VisibleScoreFinalizer on MS | full train 1k | ~133–135 | varies | Fields improve; still CFA risk | Intermediate |
| E4 | **Graft demote @ 0.913** | H=APPROVED & S≠APPROVED & conf≤0.913 → S | full train 1k | **136.07** | **0** | Best CFA=0 frontier | **SHIP** |
| E5 | Lower graft cut | conf_max &lt; 0.913 | full train 1k | &lt;136 | 0 | Leaves score on table | Reject |
| E6 | Higher graft cut | conf_max &gt; 0.913 | full train 1k | &gt;136 | &gt;0 | Reopens CFA | Reject |
| E7 | Always demote Strobl DENIED | Ignore conf when S=DENIED; keep 0.913 for REVIEW | full train 1k frontier artifacts | **136.07** (no-op) | **0** | 0 cases H=APPROVED+S=DENIED+conf&gt;0.913 | **SHIP** (private insurance) |
| E8 | **Promote Strobl APPROVED ≥0.90** | H=NEEDS_REVIEW & S=APPROVED & S.conf≥0.90 → S | full train 1k champion+Strobl | **136.71** | **0** | +0.64 class; 12 true A / 2 true R; 0 CFA | **SHIP** |
| E9 | Promote + clean risk_flags gate | Same + empty flags | full train 1k | no-op | 0 | Gate kills all promotes | Reject |
| E10 | Blind Strobl field overwrite | Replace all scored fields from Strobl | full train 1k | 136.17 | 0 | Fields drop | Reject |
| E11 | Gole all-fields + dual + Gole≥0.90 | Full field overwrite | full train 1k | **137.30** | **0** | 211↑/166↓ field cells; CFA hole over Strobl DENIED | **Superseded** |
| E14 | **Private seatbelt** | fee-only + dual + Gole≥0.90 **∧ Strobl≠DENIED** | full train 1k | **137.23** | **0** | Closes CFA hole; fee 49↑/9↓ | **SHIP** |
| E12 | Gole promote ≥0.85 ungated | Lower floor | full train 1k | ~136.5 | 3 | CFA bomb | Reject |
| E13 | AK / purpose×sig unlock | rival-style | full train 1k | vanity ↑ | 0* | Private drop / polarity refuse | **Refuse** |

## Frontier rule

Demote **0.913**, Strobl promote **0.90**, Gole promote **0.90** with Strobl-DENIED
veto, Gole fields = `fee_status` only. CFA=0 on full public 1k.

## Next actions (local only)

1. Docker smoke under contest limits.
2. Do not re-open full Gole fields / Gole≥0.85 / Engine B / AK.
