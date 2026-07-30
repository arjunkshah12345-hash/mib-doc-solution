# mib-doc-solution (arjunkshah12345-hash)

Private-first fork of the audited Calling Moonshots / tylergibbs1 visible-OCR
runtime (MIT). See `ATTRIBUTION.md`.

**Ship idea:** keep their OCR clerk (~134.7 audit), add only demote-only private
edges (`mib/private_edge.py` + `MIB_REVIEW_MARGIN=0.35`) so we cut weak
resolver APPROVEDs without rewriting their stack.

```bash
docker build -t mib-submission .
docker run --rm --network none \
  --mount type=bind,src=/path/to/pdfs,dst=/input,readonly \
  --mount type=bind,src=/path/to/output,dst=/output \
  mib-submission /input /output/predictions.jsonl
```
