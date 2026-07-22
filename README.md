# MIB Challenge v2

Offline PDF extraction + adjudication for the
[MIB Doc Challenge](https://github.com/8090-inc/mib-doc-challenge).

Public solution for **arjunkshah12345-hash** (v2). Independent of any v1 tree.

## Approach

Render-first offline pipeline: page rasterization → Tesseract → RapidOCR fill →
evidence resolution → deterministic policy + fail-closed FA gates.

We reference public prior art from strobl (`ATTRIBUTION.md`) and diverge with
evidence-based fee/purpose/risk OCR repairs. We do **not** unlock approvals from
unobserved risk using train-only correlations.

## Docker (scoring contract)

```bash
docker build -t mib-challenge-v2 .
docker run --rm --network none \
  --cpus 4 --memory 8g --pids-limit 512 --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=2g \
  --mount type=bind,src=/path/to/pdfs,dst=/input,readonly \
  --mount type=bind,src=/path/to/output,dst=/output \
  mib-challenge-v2 /input /output/predictions.jsonl
```

## Local

```bash
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements.lock
PYTHONPATH=. MIB_MAX_WORKERS=4 python solution.py /path/to/pdfs /tmp/predictions.jsonl
```

## Layout

| Path | Role |
|------|------|
| `Dockerfile` / `run.sh` / `solution.py` | Offline two-arg contract |
| `mib_pipeline/` | Extraction, resolution, adjudication, recovery |
| `mib_pipeline/arjun_heads.py` | Fail-closed FA gates |
| `ATTRIBUTION.md` / `MEMO.md` | Credit + technical notes |
| `requirements.lock` | Hashed deps |

## License

MIT — see `ATTRIBUTION.md` and `third_party_licenses/`.
