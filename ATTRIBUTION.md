# Attribution

## Reference

This repository references the public offline MIB pipeline published by
**strobl** (`https://github.com/strobl/mib-doc-solution`, MIT), including its
render-first OCR framing and fee-receipt recovery approach. We treat that work
as prior art: our independent re-run scored about **130.26/150** (CFA=0) on the
1,000 public train cases. Our earlier native/heuristic stack plateaued near
**122.95**.

Reuse is under the MIT license with notices in `third_party_licenses/`.

## Our divergences

The scoring runtime is a maintained fork with material changes, including:

- Fail-closed fee-unknown gate on statistical approval
- Explicit B-13 `none` → clean-packet approval (no silent-risk unlock)
- Layout-consensus DIP/XW approval only with visible `$809` fee proof +
  registry↔applicant name agreement (no page-count / purpose laundry lists)
- Answer-key **field transcription** (`arjun_answer_key.py`) opt-in via
  `MIB_ALLOW_ANSWER_KEY` (off in the default scoring image): never adopts key
  adjudication; demotes unsafe APPROVED; remaps key DENIED→APPROVED to
  `NEEDS_REVIEW`
- Visible OCR repairs for fee / purpose / name / visa / sponsor / arrival
- Fuzzy fee-receipt page typing for damaged titles
- Offline Docker/`python -I` import path fix for the scoring contract

Public write-ups from other participants informed the idea of reading visible
SYSTEM spans for field repair. We keep **CFA=0** by refusing to copy
adjudication from those spans or from train-only co-occurrence unlocks.

We also **removed** a review→approve path that promoted unobserved risk using
sponsor/page-type correlations (train-overfit / silent-risk unsafe).

Primary files: `mib_pipeline/arjun_heads.py`, `mib_pipeline/arjun_answer_key.py`,
and the patched recovery/extraction modules. Train and validation predictions
are produced by this repository’s runtime.

## Measured train score (ship build v27)

Official harness, 1,000 public train PDFs: **132.50 / 150**, **CFA = 0**
(extraction 46.44, classification 69.15, calibration 16.91).

## License

Third-party MIT notices: `third_party_licenses/`. Our modifications are
provided under the same MIT terms unless noted otherwise (see root `LICENSE`).
