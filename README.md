# mib-doc-solution

Offline PDF extraction + adjudication for the
[MIB Doc Challenge](https://github.com/8090-inc/mib-doc-challenge).

**Ship build v42 (transfer-first):** DIP-1/XW-2 layout-consensus only, no
enumerated train trap phonebooks, emitted-policy guardrail. Targets **private**
generalization after unofficial board #3 ranked lower-train rivals above v41’s
**138.086** public peak. See `MEMO.md`, `ATTRIBUTION.md`.

## Pipeline

Render-first offline stack: page rasterization → Tesseract → RapidOCR fill →
evidence resolution → field-manual adjudication with fail-closed gates →
layout-consensus approval (**DIP-1 / XW-2** + visible fee + name agreement) →
optional answer-key **field transcription** (never key adjudication) →
fail-closed Finding/EMBARGO demotions → **emitted-policy guardrail** →
pinned confidence recalibration + OOF blend.

## Docker (scoring contract)

```bash
docker build -t mib-doc-solution .
docker run --rm --network none \
  --cpus 4 --memory 8g --pids-limit 512 --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=2g \
  --mount type=bind,src=/path/to/pdfs,dst=/input,readonly \
  --mount type=bind,src=/path/to/output,dst=/output \
  mib-doc-solution /input /output/predictions.jsonl
```

## Local smoke

```bash
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements.lock
PYTHONPATH=. MIB_MAX_WORKERS=4 python solution.py /path/to/pdfs /tmp/predictions.jsonl
```

## Layout

| Path | Role |
|------|------|
| `Dockerfile` / `run.sh` / `solution.py` | Two-argument offline contract |
| `mib_pipeline/` | Extraction, resolution, adjudication, recovery |
| `mib_pipeline/arjun_heads.py` | Fail-closed approval / repair heads |
| `mib_pipeline/arjun_answer_key.py` | Field transcription only |
| `MEMO.md` | Technical memo |
| `docs/INTERVIEW_BIBLE.md` | Full story: how we improved each score jump |
| `ATTRIBUTION.md` | strobl reference + our changes |
| `requirements.lock` | Hashed dependencies |

## License

MIT — see `ATTRIBUTION.md` and `third_party_licenses/`.
