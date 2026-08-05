FROM python:3.11-slim-bookworm

ENV BLIS_NUM_THREADS=2 \
    HOME=/tmp \
    MALLOC_ARENA_MAX=4 \
    MIB_MAX_WORKERS=2 \
    MIB_GRAFT_CONF_MAX=0.913 \
    MIB_NATIVE_SCAN_OCR=1 \
    MIB_REVIEW_MODEL=1 \
    MIB_REVIEW_MARGIN=0.35 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=2 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TMPDIR=/tmp \
    TOKENIZERS_PARALLELISM=false

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
      tesseract-ocr tesseract-ocr-eng \
      poppler-utils \
      libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Moonshots OCR stack + Strobl runtime deps (pypdfium2 / rapidocr 3 / pillow / numpy).
RUN pip install --no-cache-dir \
    coloredlogs==15.0.1 \
    flatbuffers==25.12.19 \
    humanfriendly==10.0 \
    mpmath==1.3.0 \
    pymupdf==1.28.0 \
    rapidocr-onnxruntime==1.4.4 \
    onnxruntime==1.20.1 \
    rapidfuzz==3.14.5 \
    numpy==2.2.6 \
    opencv-python==4.11.0.86 \
    opencv-python-headless==4.11.0.86 \
    packaging==26.2 \
    pillow==12.3.0 \
    protobuf==7.35.1 \
    pyclipper==1.4.0 \
    PyYAML==6.0.3 \
    shapely==2.1.2 \
    six==1.17.0 \
    sympy==1.14.0 \
    tqdm==4.69.1 \
    pypdfium2==5.11.0 \
    rapidocr==3.9.2 \
    colorlog==6.11.0 \
    omegaconf==2.3.0

COPY run.sh solution.py /app/
COPY mib /app/mib
COPY models /app/models
COPY mib_pipeline /app/mib_pipeline
COPY clerks /app/clerks
COPY scripts/predict.py scripts/run_shard.py /app/scripts/
COPY third_party_licenses /app/third_party_licenses
COPY LICENSE ATTRIBUTION.md MEMO.md /app/

RUN chmod 0555 /app/run.sh /app/solution.py \
    && chmod -R a=rX /app/mib /app/models /app/mib_pipeline /app/clerks /app/scripts \
    && python -c "from rapidocr_onnxruntime import RapidOCR; RapidOCR()" \
    && python -c "import mib.pipeline; import mib_pipeline.graft"

USER root
ENTRYPOINT ["/app/run.sh"]
