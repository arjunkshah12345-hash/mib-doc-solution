# Attribution

## Reference (not a drop-in copy)

We independently studied and **referenced** the public offline MIB pipeline
published by **strobl** (`https://github.com/strobl/mib-doc-solution`, MIT),
including its render-first OCR framing and fee-receipt recovery ideas.

That public work is a strong baseline (~130.26/150 on the 1,000-case train
split in our re-run). Our earlier native/heuristic stack plateaued near
**122.95**. We treat strobl as prior art to beat, not as a submission to
re-badge.

## What is ours

This repository’s scoring runtime is our maintained fork with material
divergences, including:

- Fail-closed fee-unknown FA gate on the statistical approval head
- Biometric clean-`none` emission from visible B-13 flags rows
- Waived-before-paid OCR repairs on damaged fee receipts
- Fuzzy fee-receipt page typing (`Fee Reraint` → fee receipt)
- Docker/`python -I` import path fix for the offline contract

We explicitly **removed** a train-correlated review→approve unlock that
promoted unobserved risk using sponsor page-type co-occurrence — that was
overfit / silent-risk unsafe.

See `mib_pipeline/arjun_heads.py` and the patched recovery/extraction paths.
Train/validation predictions and memo scores are our responsibility.

## License

Third-party MIT notice for referenced upstream code:
`third_party_licenses/`. Our modifications are provided under the same MIT
terms unless noted otherwise.
