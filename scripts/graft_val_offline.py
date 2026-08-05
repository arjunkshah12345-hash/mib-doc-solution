#!/usr/bin/env python3
"""Offline: Moonshots val JSONL + Strobl val JSONL → grafted predictions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mib_pipeline.graft import APPROVE_CONF_MAX, PROMOTE_CONF_MIN, graft_row  # noqa: E402
from mib_pipeline.models import PredictionRow  # noqa: E402
from mib_pipeline.score_finalizer import VisibleScoreFinalizer  # noqa: E402


def load(path: Path) -> dict[str, dict]:
    by: dict[str, dict] = {}
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            by[row["case_id"]] = row
    return by


def merge_chunks(chunk_dir: Path) -> dict[str, dict]:
    by: dict[str, dict] = {}
    for path in sorted(chunk_dir.glob("pred-*.jsonl")):
        by.update(load(path))
    return by


def main() -> int:
    ms_chunks = Path("/tmp/mib-v43-val-chunks")
    st_chunks = Path("/tmp/mib-strobl-val-chunks")
    val_pdf = Path("/Users/arjunkshah21/Downloads/cursormib/mib-solution/data/validation")
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/mib-graft-val.jsonl")
    conf_max = float(sys.argv[2]) if len(sys.argv) > 2 else APPROVE_CONF_MAX
    promote_min = float(sys.argv[3]) if len(sys.argv) > 3 else PROMOTE_CONF_MIN

    ms = merge_chunks(ms_chunks)
    st = merge_chunks(st_chunks)
    print(f"ms={len(ms)} st={len(st)} conf_max={conf_max} promote_min={promote_min}", flush=True)
    if len(ms) < 5000 or len(st) < 5000:
        print("WARN: incomplete val coverage", flush=True)

    finalizer = VisibleScoreFinalizer()
    demoted = 0
    promoted = 0
    with out.open("w") as handle:
        for i in range(100001, 105001):
            cid = f"MIB-{i:06d}"
            m = ms.get(cid)
            s = st.get(cid)
            if m is None and s is None:
                continue
            if m is None:
                handle.write(json.dumps(s) + "\n")
                continue
            pdf = val_pdf / f"{cid}.pdf"
            base = PredictionRow.from_mapping(m, fallback_case_id=cid)
            try:
                hybrid = finalizer(pdf, base).to_dict()
            except Exception as exc:  # noqa: BLE001
                print(f"finalizer fail {cid}: {exc}", file=sys.stderr)
                hybrid = base.to_dict()
            if s is None:
                row = hybrid
            else:
                before = hybrid.get("adjudication")
                row = graft_row(
                    hybrid, s, conf_max=conf_max, promote_conf_min=promote_min
                )
                after = row.get("adjudication")
                if before == "APPROVED" and after != "APPROVED":
                    demoted += 1
                elif before == "NEEDS_REVIEW" and after == "APPROVED":
                    promoted += 1
            handle.write(json.dumps(row) + "\n")
    print(f"wrote {out} demoted={demoted} promoted={promoted}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
