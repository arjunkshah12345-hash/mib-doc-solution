#!/usr/bin/env python3
"""Offline two-argument runtime: Moonshots fields + Strobl graft.

1) Moonshots OCR/decision → base rows
2) Strobl mib_pipeline → strobl rows
3) VisibleScoreFinalizer on Moonshots rows → hybrid
4) Graft: demote always on Strobl DENIED; demote mid/low-conf (≤0.913) on
   Strobl NEEDS_REVIEW; promote hybrid NEEDS_REVIEW → APPROVED when Strobl
   APPROVED conf ≥ 0.90
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

from mib_pipeline import (
    AdjudicationEngine,
    BatchRunner,
    CalibrationArtifactError,
    CaseLinker,
    ConfidenceCalibrator,
    DocumentRenderer,
    EvidencePrecedenceResolver,
    GeneralizablePolicyExceptionStore,
    OutputConfidenceRecalibrationProcessor,
    OutputConfidenceRecalibrator,
    PolicyArtifactError,
    RapidOutputRecoveryProcessor,
    ReviewDenialRecoveryAdjudicator,
    VisibleEvidenceExtractor,
)
from mib_pipeline.graft import APPROVE_CONF_MAX, PROMOTE_CONF_MIN, graft_row
from mib_pipeline.models import PredictionRow
from mib_pipeline.score_finalizer import VisibleScoreFinalizer


USAGE = "usage: solution.py <input_pdf_dir> <output_predictions_path>"
MAX_WORKERS = 4
ROOT = Path(__file__).resolve().parent


class ContractError(ValueError):
    """Raised when the two-argument runtime contract is not satisfied."""


def configured_worker_limit() -> int:
    raw_value = os.environ.get("MIB_MAX_WORKERS", str(MAX_WORKERS))
    try:
        requested = int(raw_value)
    except ValueError as exc:
        raise ContractError("MIB_MAX_WORKERS must be an integer") from exc
    if requested < 1:
        raise ContractError("MIB_MAX_WORKERS must be at least 1")
    return min(requested, MAX_WORKERS)


def parse_paths(argv: Sequence[str]) -> tuple[Path, Path]:
    if len(argv) != 3:
        raise ContractError(USAGE)

    input_dir = Path(argv[1])
    output_path = Path(argv[2])

    if not input_dir.is_dir():
        raise ContractError(f"input PDF directory does not exist: {input_dir}")
    if not output_path.name:
        raise ContractError("output predictions path must name a file")
    if output_path.exists() and output_path.is_dir():
        raise ContractError(f"output predictions path is a directory: {output_path}")
    if not output_path.parent.is_dir():
        raise ContractError(f"output directory does not exist: {output_path.parent}")

    resolved_input = input_dir.resolve()
    resolved_output = output_path.resolve()
    try:
        resolved_output.relative_to(resolved_input)
    except ValueError:
        output_is_inside_input = False
    else:
        output_is_inside_input = True
    if output_is_inside_input:
        raise ContractError("output predictions path must not be inside the input directory")

    return input_dir, output_path


def _load_jsonl(path: Path) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            by_id[str(row["case_id"])] = row
    return by_id


def _run_moonshots(input_dir: Path, out_path: Path) -> None:
    predict = ROOT / "scripts" / "predict.py"
    if not predict.is_file():
        raise ContractError(f"moonshots predict missing: {predict}")
    env = os.environ.copy()
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("MIB_NATIVE_SCAN_OCR", "1")
    env.setdefault("MIB_REVIEW_MODEL", "1")
    env["PYTHONPATH"] = str(ROOT) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    py = os.environ.get("MIB_MOONSHOTS_PYTHON", sys.executable)
    cmd = [py, "-B", str(predict), str(input_dir), str(out_path)]
    proc = subprocess.run(cmd, env=env, cwd=str(ROOT))
    if proc.returncode != 0:
        raise ContractError(f"moonshots predict failed with exit {proc.returncode}")
    if not out_path.is_file():
        raise ContractError("moonshots predict produced no output file")


def _run_strobl(input_dir: Path, out_path: Path) -> None:
    runner = BatchRunner(
        OutputConfidenceRecalibrationProcessor(
            processor=RapidOutputRecoveryProcessor(
                renderer=DocumentRenderer(),
                primary_extractor=VisibleEvidenceExtractor(
                    packet_page_type_markers=True,
                ),
                linker=CaseLinker(),
                resolver=EvidencePrecedenceResolver(),
                adjudicator=ReviewDenialRecoveryAdjudicator(
                    AdjudicationEngine(
                        calibrator=ConfidenceCalibrator.from_pinned_artifact(),
                        exceptions=GeneralizablePolicyExceptionStore.from_pinned_artifact(),
                    )
                ),
            ),
            recalibrator=OutputConfidenceRecalibrator.from_pinned_artifact(),
        ),
        max_workers=configured_worker_limit(),
        row_finalizer=None,
    )
    runner.run(input_dir, out_path)


def _pdf_index(input_dir: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in sorted(input_dir.glob("*.pdf")):
        stem = path.stem
        if stem.startswith("MIB-"):
            index[stem] = path
    return index


def main(argv: Sequence[str] | None = None) -> int:
    arguments = sys.argv if argv is None else argv
    try:
        input_dir, output_path = parse_paths(arguments)
        conf_max = float(os.environ.get("MIB_GRAFT_CONF_MAX", str(APPROVE_CONF_MAX)))
        promote_min = float(
            os.environ.get("MIB_GRAFT_PROMOTE_CONF_MIN", str(PROMOTE_CONF_MIN))
        )
        with tempfile.TemporaryDirectory(prefix="mib-graft-") as tmp:
            tmp_dir = Path(tmp)
            ms_path = tmp_dir / "moonshots.jsonl"
            st_path = tmp_dir / "strobl.jsonl"
            print("graft: running moonshots…", file=sys.stderr)
            _run_moonshots(input_dir, ms_path)
            print("graft: running strobl…", file=sys.stderr)
            _run_strobl(input_dir, st_path)
            ms_by = _load_jsonl(ms_path)
            st_by = _load_jsonl(st_path)
            pdfs = _pdf_index(input_dir)
            finalizer = VisibleScoreFinalizer()
            demoted = 0
            promoted = 0
            with output_path.open("w") as handle:
                for case_id in sorted(set(ms_by) | set(st_by) | set(pdfs)):
                    ms = ms_by.get(case_id)
                    st = st_by.get(case_id)
                    pdf = pdfs.get(case_id)
                    if ms is None and st is not None:
                        row = {k: st.get(k) for k in st}
                    elif ms is None:
                        continue
                    else:
                        base = PredictionRow.from_mapping(ms, fallback_case_id=case_id)
                        if pdf is not None:
                            try:
                                hybrid = finalizer(pdf, base).to_dict()
                            except Exception as exc:  # noqa: BLE001 — keep case
                                print(f"finalizer fail {case_id}: {exc}", file=sys.stderr)
                                hybrid = base.to_dict()
                        else:
                            hybrid = base.to_dict()
                        if st is None:
                            row = hybrid
                        else:
                            before = hybrid.get("adjudication")
                            row = graft_row(
                                hybrid,
                                st,
                                conf_max=conf_max,
                                promote_conf_min=promote_min,
                            )
                            after = row.get("adjudication")
                            if before == "APPROVED" and after != "APPROVED":
                                demoted += 1
                            elif before == "NEEDS_REVIEW" and after == "APPROVED":
                                promoted += 1
                    handle.write(json.dumps(row, ensure_ascii=True) + "\n")
            print(
                f"graft: wrote {output_path} demoted={demoted} promoted={promoted} "
                f"conf_max={conf_max} promote_min={promote_min}",
                file=sys.stderr,
            )
    except (CalibrationArtifactError, ContractError, OSError, PolicyArtifactError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 64
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
