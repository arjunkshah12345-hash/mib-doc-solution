#!/usr/bin/env bash
set -euo pipefail

input_dir="${1:?usage: run.sh <input_pdf_dir> <output_path>}"
output_path="${2:?usage: run.sh <input_pdf_dir> <output_path>}"
shift 2 || true

# Dual-pipeline graft: Moonshots OCR + Strobl second opinion (private-first).
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export MIB_NATIVE_SCAN_OCR="${MIB_NATIVE_SCAN_OCR:-1}"
export MIB_REVIEW_MODEL="${MIB_REVIEW_MODEL:-1}"
export MIB_REVIEW_MARGIN="${MIB_REVIEW_MARGIN:-0.35}"
export MIB_MAX_WORKERS="${MIB_MAX_WORKERS:-2}"
export MIB_GRAFT_CONF_MAX="${MIB_GRAFT_CONF_MAX:-0.913}"
export MIB_PRIVATE_EDGE=1

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 -B "$SCRIPT_DIR/solution.py" "$input_dir" "$output_path"
