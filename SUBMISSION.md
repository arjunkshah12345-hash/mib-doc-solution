# Solution repository

Public solution repository (includes the mandatory `Dockerfile`):

https://github.com/arjunkshah12345-hash/mib-doc-solution

Dockerfile:

https://github.com/arjunkshah12345-hash/mib-doc-solution/blob/main/Dockerfile

## Offline run contract

```bash
docker build -t mib-submission .
docker run --rm --network none \
  --cpus 4 --memory 8g --pids-limit 512 --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=2g \
  --mount type=bind,source=/path/to/pdfs,destination=/input,readonly \
  --mount type=bind,source=/path/to/output,destination=/output \
  mib-submission /input /output/predictions.jsonl
```

Ship build: **v27** — train **132.34/150**, **CFA=0** (see `MEMO.md`).
