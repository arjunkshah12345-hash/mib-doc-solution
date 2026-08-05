# Architecture — Moonshots + Strobl graft

Live private-win runtime (`solution.py` / `run.sh`). Fully offline, two-arg Docker contract.

## Pipeline

```
PDF dir
  ├─► Moonshots / tyler OCR clerk (mib/, RapidOCR-onnx)     ⎤ parallel
  ├─► thegoleffect clerk (clerks/goleffect/)               ⎦
  ├─► Strobl mib_pipeline (in-process)
  ├─► VisibleScoreFinalizer(Moonshots rows) → hybrid
  └─► graft_row(hybrid, strobl, gole)  [private seatbelt]
        Strobl demote DENIED / REVIEW≤0.913; Strobl promote ≥0.90
        Gole fee_status only; dual-DENIED; Gole promote ≥0.90 iff Strobl ≠ DENIED
```

## Security boundary

- Visible rendered pages are trusted; planted white/`SYSTEM:` answer-key text is not used as a decision channel.
- No case-ID / filename / hash lookup tables.
- No LLM/VLM/cloud OCR/network at inference.
- Never Gole-promote over Strobl DENIED; no blind full-field Gole overwrite.

## Modules

| Path | Role |
|------|------|
| `solution.py` | Triple-clerk orchestration + graft |
| `mib/` + `scripts/predict.py` | Moonshots clerk |
| `mib_pipeline/` | Strobl clerk + `graft.py` + score finalizer |
| `clerks/goleffect/` | Vendored thegoleffect clerk |
| `models/` | Pinned OCR / review artifacts |
| `run.sh` / `Dockerfile` | Offline submission entry |

## Locked public-train claim

Official `evaluate.py`: **137.23 / 150**, **CFA = 0**  
(field 45.66 / class 73.62 / cal 17.95).
