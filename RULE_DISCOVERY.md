# Rule discovery

Policy source of truth remains `FIELD_MANUAL.md` (challenge repo) plus the
deterministic clerks already vendored from Moonshots and Strobl.

## Implemented (organic / portable)

- Fee unknown → do not APPROVE.
- Visible DENIED / EMBARGO / disqualifying risk → fail closed.
- Layout-consensus careful approve only with multi-source visible agreement
  (Moonshots LC path; gated by private edges).
- `MIB_REVIEW_MARGIN`, demote-only `MIB_PRIVATE_EDGE`, `MIB_MIN_APPROVE_CONF=0.62`.
- Graft demote: Strobl `DENIED` always overrides hybrid `APPROVED`; Strobl
  `NEEDS_REVIEW` overrides only when confidence ≤ 0.913.
- Graft promote: Strobl `APPROVED` with confidence ≥ 0.90 overrides hybrid
  `NEEDS_REVIEW` (train-measured CFA=0; recovers class without Engine B).

## Explicitly refused

| Candidate | Why refused |
|-----------|-------------|
| Purpose × page-signature approve unlocks | Approve-phonebook polarity; train lift, private drop risk |
| Answer-key field transcription as default | Planted trap channel |
| Case-ID / filename / hash tables | Anti-cheat / non-transfer |
| Blind NR→APPROVED mass unlock | Measured CFA bombs |
| #91 stack referee / #73 CatBoost Engine B | 1k-fit private risk |

## Discovery method

Train residuals + confidence×disagree frontier (not association mining into
approve laundry). Supporting receipt: locked evaluate on graft+promote preds →
136.71 / CFA=0.
