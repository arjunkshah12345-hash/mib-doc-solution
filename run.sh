#!/usr/bin/env bash
set -euo pipefail

input_dir="${1:?usage: run.sh <input_pdf_dir> <output_path>}"
output_path="${2:?usage: run.sh <input_pdf_dir> <output_path>}"
shift 2

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export MIB_NATIVE_SCAN_OCR="${MIB_NATIVE_SCAN_OCR:-1}"
# The submitted profile is score-optimal under the challenge's published
# utility matrix. Keep the library-level resolver fail-closed by default, while
# making this entrypoint's candidate-trained, visible-feature head explicit.
export MIB_REVIEW_MODEL="${MIB_REVIEW_MODEL:-1}"
# Private edge (arjunkshah): require a small EV margin before the resolver may
# mint APPROVED from insufficient_evidence (upstream memo: that path drives CFA).
export MIB_REVIEW_MARGIN="${MIB_REVIEW_MARGIN:-0.35}"
# Private CFA insurance: soft floor — stay in ~133–134 band, CFA≪12.
export MIB_MIN_APPROVE_CONF="${MIB_MIN_APPROVE_CONF:-0.62}"

# shellcheck disable=SC1091
# Ensure private_edge defaults are visible to Python even if margin unset above.
export MIB_PRIVATE_EDGE=1

exec python3 /app/scripts/predict.py "$input_dir" "$output_path" "$@"
