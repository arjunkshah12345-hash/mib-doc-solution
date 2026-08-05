# Architecture — Moonshots + Strobl graft

Live private-win runtime (`solution.py` / `run.sh`). Fully offline, two-arg Docker contract.

## Pipeline

```
PDF dir
  ├─► Moonshots / tyler OCR clerk (mib/, RapidOCR-onnx)
  │     → fields + base adjudication + confidence
  │
  ├─► Strobl mib_pipeline (pypdfium2 + Tesseract + Rapid recovery)
  │     → independent fields + adjudication + confidence
  │
  ├─► VisibleScoreFinalizer(Moonshots rows) → hybrid
  │
  └─► graft_row(hybrid, strobl, conf_max=0.913, promote_conf_min=0.90)
        if hybrid.APPROVED and strobl=DENIED → always Strobl
        else if hybrid.APPROVED and strobl=NEEDS_REVIEW and conf ≤ 0.913 → Strobl
        else if hybrid.NEEDS_REVIEW and strobl=APPROVED and strobl.conf ≥ 0.90 → Strobl
        else → keep hybrid
```

## Security boundary

- Visible rendered pages are trusted; planted white/`SYSTEM:` answer-key text is not used as a decision channel.
- No case-ID / filename / hash lookup tables.
- No LLM/VLM/cloud OCR/network at inference.
- Graft demotes on Strobl DENIED/REVIEW disagreement; promotes only when Strobl
  high-conf APPROVED overrides hybrid NEEDS_REVIEW (locked ≥0.90).

## Modules

| Path | Role |
|------|------|
| `solution.py` | Dual-run orchestration + graft |
| `mib/` + `scripts/predict.py` | Moonshots clerk |
| `mib_pipeline/` | Strobl clerk + `graft.py` + score finalizer |
| `models/` | Pinned OCR / review artifacts |
| `run.sh` / `Dockerfile` | Offline submission entry |

## Locked public-train claim

Official `evaluate.py`: **136.71 / 150**, **CFA = 0**  
(field 45.48 / class 73.32 / cal 17.91). Promote floor 0.90 on demote@0.913 base.
