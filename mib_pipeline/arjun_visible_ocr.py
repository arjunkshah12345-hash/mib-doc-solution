"""Visible OCR repairs for fee / purpose / deny-findings when native text is empty.

Runs a cheap pdftoppm + Tesseract pass only when needed. Fail-closed on
approvals: may set DENIED from an explicit Finding, and may fix fee/purpose
fields, but never invents APPROVED.

Also recovers image-only ``Fee Status: unpaid`` via multi-crop ROI OCR when
native PDF text has a SAMPLE DENIAL watermark but no selectable fee fields
(measured decoy class: bare ``Fee Status: unpaid`` OCR on waived APPROVED
packets without SAMPLE).

Also recovers tilted Manual Adjudicator Note pages (Finding:DENIED / mandatory
fee unpaid) via deskewed top-left ROI tesseract, gated by SAMPLE DENIAL +
risk=none (ablation: 1 gold DEN / 0 AP / 0 true-REVIEW on 71 REVIEW probes).

Also recovers DIP-1 image-only unpaid denies when native text lacks SAMPLE /
Fee fields but red-channel OCR reads a SAMPLE DENIAL watermark and no Fee
Receipt page exists (ablation: MIB-000570 + MIB-000898; 0 CFA / 0 FAP).

Conditional hi-res retry (thegoleffect-style): one 300 DPI grayscale contrast
pass when risk=none, damage/redaction cues are visible, and adjudication is
NEEDS_REVIEW or confidence is thin. Recovers risk phrases / Finding lines only;
never invents APPROVED.
"""

from __future__ import annotations

import difflib
import io
import os
import re
import subprocess
import tempfile
from pathlib import Path

from .models import PredictionRow

_HI_RES_DPI = 300
_HI_RES_CONFIDENCE_GATE = 0.90
_DAMAGE_CUES = re.compile(
    r"\b(?:UNREADABLE|REDACTED|CUT\s+OUT|WHITEOUT|WASHED\s+OUT|"
    r"PANEL\s+MISSING|REGISTRY\s+LOST)\b",
    re.I,
)
_DISQUALIFYING_RISK = frozenset(
    {
        "biohazard_red",
        "memory_tampering",
        "active_warrant",
        "planetary_embargo",
    }
)
_REVIEW_RISK = frozenset(
    {
        "identity_conflict",
        "sponsor_mismatch",
        "illegible_biometrics",
        "rescinded_denial",
    }
)

_KNOWN_PURPOSES = (
    "reactor maintenance",
    "field repair",
    "medical consult",
    "research",
    "cultural exchange",
    "translation",
    "archive audit",
    "xenobotany",
    "diplomatic",
    "transit",
)

# Top-left crops for image-only MIB Fee Receipt headers (RGB, 4× upscale).
_FEE_ROI_CROPS = (
    (0.05, 0.05, 0.55, 0.22),
    (0.03, 0.03, 0.50, 0.20),
    (0.08, 0.06, 0.58, 0.24),
    (0.04, 0.04, 0.65, 0.28),
)


def _ocr_packet(pdf_path: Path, dpi: int = 160) -> str:
    with tempfile.TemporaryDirectory(prefix="mib-vis-") as tmp:
        work = Path(tmp)
        prefix = work / "page"
        try:
            subprocess.run(
                [
                    "pdftoppm",
                    "-jpeg",
                    "-jpegopt",
                    "quality=85",
                    "-r",
                    str(dpi),
                    str(pdf_path),
                    str(prefix),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=50,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        chunks: list[str] = []
        for image in sorted(work.glob("page-*.jpg")):
            for psm in ("4", "6", "11"):
                try:
                    cp = subprocess.run(
                        ["tesseract", image.name, "stdout", "--psm", psm],
                        cwd=work,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        text=True,
                        errors="replace",
                        timeout=25,
                        check=False,
                    )
                    chunks.append(cp.stdout if cp.returncode == 0 else "")
                except (OSError, subprocess.TimeoutExpired):
                    chunks.append("")
        return "\n".join(chunks)


def _ocr_packet_high_resolution(pdf_path: Path, dpi: int = _HI_RES_DPI) -> str:
    """One expensive 300 DPI grayscale contrast pass for redacted/damaged packets.

    Uses pypdfium2 + PIL (no ImageMagick) for Docker portability.
    """

    cache_root = os.environ.get("MIB_HIRES_OCR_CACHE")
    cache_file = Path(cache_root, pdf_path.stem + ".txt") if cache_root else None
    if cache_file and cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="replace")

    try:
        import pypdfium2 as pdfium
        from PIL import ImageFilter, ImageOps
    except ImportError:
        return ""

    scale = dpi / 72.0
    chunks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="mib-hires-") as tmp:
        work = Path(tmp)
        try:
            document = pdfium.PdfDocument(str(pdf_path))
        except Exception:
            return ""
        try:
            for index in range(len(document)):
                try:
                    gray = document[index].render(scale=scale).to_pil().convert("L")
                except Exception:
                    chunks.append("")
                    continue
                prepared = ImageOps.autocontrast(gray, cutoff=2).filter(
                    ImageFilter.SHARPEN
                )
                out = work / f"page-{index}.png"
                try:
                    prepared.save(out)
                except Exception:
                    chunks.append("")
                    continue
                try:
                    cp = subprocess.run(
                        ["tesseract", str(out), "stdout", "--psm", "6"],
                        capture_output=True,
                        text=True,
                        errors="replace",
                        timeout=30,
                        check=False,
                    )
                    chunks.append(cp.stdout if cp.returncode == 0 else "")
                except (OSError, subprocess.TimeoutExpired):
                    chunks.append("")
        finally:
            document.close()
    text = "\f".join(chunks)
    if cache_file and text.strip():
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(text, encoding="utf-8")
    return text


def _baseline_visibility_text(pdf_path: Path, extra: str = "") -> str:
    native = _native_pdf_text(pdf_path)
    layout = ""
    try:
        from .arjun_heads import _pdf_layout_text

        layout = _pdf_layout_text(pdf_path)
    except Exception:
        pass
    return f"{native}\n{layout}\n{extra}"


def _should_hi_res_retry(row: PredictionRow, visibility_text: str) -> bool:
    """Gate: clean-risk ambiguity on visibly damaged/redacted packets only."""

    if _norm_risk(row.risk_flags) != "none":
        return False
    if not _DAMAGE_CUES.search(visibility_text):
        return False
    confidence = float(row.confidence or 0.0)
    if row.adjudication == "NEEDS_REVIEW":
        return True
    if confidence < _HI_RES_CONFIDENCE_GATE:
        return True
    return False


def _apply_hi_res_text_repairs(row: PredictionRow, text: str) -> PredictionRow:
    """Field-fill / demote-only repairs from hi-res OCR. Never invents APPROVED."""

    if not text.strip():
        return row
    payload = row.to_dict()
    changed = False

    risk = _risk_tokens(text)
    if risk and _norm_risk(payload.get("risk_flags")) == "none":
        payload["risk_flags"] = risk
        changed = True

    risk_set = set((payload.get("risk_flags") or "none").split("|")) - {"none", ""}
    if risk_set & _DISQUALIFYING_RISK and payload.get("adjudication") in {
        "NEEDS_REVIEW",
        "APPROVED",
    }:
        payload["adjudication"] = "DENIED"
        payload["confidence"] = 0.98
        changed = True
    elif risk_set & _REVIEW_RISK and payload.get("adjudication") == "APPROVED":
        payload["adjudication"] = "NEEDS_REVIEW"
        payload["confidence"] = min(float(payload.get("confidence") or 0.7), 0.55)
        changed = True

    if _finding_denied(text) and payload.get("adjudication") != "DENIED":
        payload["adjudication"] = "DENIED"
        payload["confidence"] = 0.98
        changed = True
    elif _finding_needs_review(text) and payload.get("adjudication") == "DENIED":
        payload["adjudication"] = "NEEDS_REVIEW"
        payload["confidence"] = max(float(payload.get("confidence") or 0), 0.85)
        changed = True
    elif _finding_needs_review(text) and payload.get("adjudication") == "APPROVED":
        payload["adjudication"] = "NEEDS_REVIEW"
        payload["confidence"] = min(float(payload.get("confidence") or 0.7), 0.55)
        changed = True

    if not changed:
        return row
    return PredictionRow.from_mapping(payload, fallback_case_id=row.case_id)


def apply_hi_res_ocr_repairs(
    row: PredictionRow,
    pdf_path: Path,
    *,
    baseline_ocr: str = "",
) -> PredictionRow:
    """Conditional hi-res OCR retry for redacted/damaged clean-risk ambiguity."""

    import os

    flag = os.environ.get("MIB_ENABLE_HIRES_OCR", "1").strip().lower()
    if flag in {"0", "false", "no", "off"}:
        return row
    visibility = _baseline_visibility_text(pdf_path, baseline_ocr)
    if not _should_hi_res_retry(row, visibility):
        return row
    hi_res = _ocr_packet_high_resolution(pdf_path)
    if not hi_res.strip():
        return row
    return _apply_hi_res_text_repairs(row, hi_res)


def _native_pdf_text(pdf_path: Path) -> str:
    try:
        import fitz
    except ImportError:
        return ""
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return ""
    return "\n".join(page.get_text() for page in doc)


def _ocr_fee_receipt_rois(pdf_path: Path) -> str:
    """Multi-crop RGB OCR of large embedded page images (fee receipt headers)."""

    try:
        import fitz
        from PIL import Image
    except ImportError:
        return ""

    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return ""

    chunks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="mib-fee-roi-") as tmp:
        work = Path(tmp)
        n = 0
        seen: set[int] = set()
        for page in doc:
            for imref in page.get_images(full=True):
                xref = int(imref[0])
                if xref in seen:
                    continue
                seen.add(xref)
                try:
                    info = doc.extract_image(xref)
                except Exception:
                    continue
                if int(info.get("width") or 0) < 1000:
                    continue
                try:
                    image = Image.open(io.BytesIO(info["image"])).convert("RGB")
                except Exception:
                    continue
                width, height = image.size
                for x0, y0, x1, y1 in _FEE_ROI_CROPS:
                    roi = image.crop(
                        (
                            int(width * x0),
                            int(height * y0),
                            int(width * x1),
                            int(height * y1),
                        )
                    )
                    roi = roi.resize(
                        (max(1, roi.width * 4), max(1, roi.height * 4)),
                        Image.Resampling.LANCZOS,
                    )
                    out = work / f"{n}.png"
                    n += 1
                    try:
                        roi.save(out)
                    except Exception:
                        continue
                    for psm in ("4", "6", "11"):
                        try:
                            cp = subprocess.run(
                                [
                                    "tesseract",
                                    str(out),
                                    "stdout",
                                    "--psm",
                                    psm,
                                    "-l",
                                    "eng",
                                ],
                                capture_output=True,
                                text=True,
                                errors="replace",
                                timeout=40,
                                check=False,
                            )
                            chunks.append(cp.stdout or "")
                        except (OSError, subprocess.TimeoutExpired):
                            chunks.append("")
    return "\n".join(chunks)


def _fee_from_ocr(text: str) -> str | None:
    cleaned = re.sub(r"samp\w*\s*denia\w*", "", text, flags=re.I)
    if re.search(r"Fee\s*Status\s*[: ]\s*waived", cleaned, re.I):
        return "waived"
    if re.search(r"Amount\s*\$?\s*0(?:[.,]00)?", cleaned, re.I) and re.search(
        r"(?:DIP[\s\-]?WAIVER|Waiver\s*Code\s*[:#]?\s*DIP|Waiver\s*Code\s*[:#]?\s*\w*WAIV)",
        cleaned,
        re.I,
    ):
        return "waived"
    if re.search(r"Fee\s*Status\s*[: ]\s*unpaid", cleaned, re.I):
        return "unpaid"
    # Measured OCR garble on image-only unpaid receipts (e.g. ``Fes Gti umgpae``).
    if re.search(
        r"Fes?\w*.{0,24}(umgpae|ump\s*ete|unpa(?:id)?|aqald|umgp)",
        cleaned,
        re.I,
    ):
        return "unpaid"
    if re.search(
        r"(Fee|Fes|Receipt|Race\s+ad).{0,40}(umgpae|ump\s*ete|unpa|aqald)",
        cleaned,
        re.I,
    ):
        return "unpaid"
    if re.search(r"\bunpaid\b", cleaned, re.I) and re.search(
        r"(Fee|Receipt|Status|MIB|Race)", cleaned, re.I
    ):
        return "unpaid"
    if re.search(r"Fee\s*Status\s*[: ]\s*paid", cleaned, re.I):
        return "paid"
    if re.search(r"Amount\s*\$?\s*809(?:[.,]00)?", cleaned, re.I):
        return "paid"
    if re.search(r"Fee\s*Status\s*[: ]\s*unknown", cleaned, re.I):
        return "unknown"
    return None


def _purpose_from_ocr(text: str) -> str | None:
    # Sponsor attestation sentence.
    for match in re.finditer(
        r"attests that [A-Z][a-z]+(?:\s+[A-Z][a-z]+)+ is expected on Earth for ([a-z \n]+?)(?:\.|,|\n)",
        text,
        re.I,
    ):
        blob = " ".join(match.group(1).casefold().split())
        for purpose in _KNOWN_PURPOSES:
            if blob == purpose or blob.startswith(purpose):
                return purpose
    for purpose in _KNOWN_PURPOSES:
        if purpose == "reactor maintenance":
            continue
        if re.search(
            rf"(?:declared\s+purpose\s*[:#.=_-]\s*{re.escape(purpose)}"
            rf"|purpose\s+of\s+visit\s*[:#.=_-]\s*{re.escape(purpose)})",
            text,
            re.I,
        ):
            return purpose
    return None


def _finding_denied(text: str) -> bool:
    if re.search(r"Finding\s*[: ]\s*DENIED", text, re.I):
        return True
    # Avoid SAMPLE DENIAL watermarks.
    cleaned = re.sub(r"\bsamp\w*\s*denia\w*\b", "", text, flags=re.I)
    if re.search(r"Finding\s*:\s*NEEDS[_\s]?REVIEW\b", cleaned, re.I):
        return False
    if re.search(r"Finding\s*:\s*APPROVED\b", cleaned, re.I):
        return False
    if re.search(r"\bFinding\b.{0,20}\bDENIED\b", cleaned, re.I | re.S):
        return True
    # Deskew OCR garble: "Maru Adjuulicater Nate" / "Manu Adj*".
    manual = bool(re.search(r"Manu\w*\s+Adj\w*", cleaned, re.I))
    unpaidish = bool(
        re.search(
            r"(DENIED|unpaid|enpaid|wepuil|wnpell|wpeid|umgpae|Mntstay|"
            r"fen\s+eyed|Manitey|feo\s*un|fe\s*un|fee\s*un|fee\s*en|fos\s*sid)",
            cleaned,
            re.I,
        )
    )
    find_den_garble = bool(
        re.search(
            r"(Find\w*|Finis?|Fins?|Fini|Finy|Fiaiey|Frey|Pirwe|Paras)"
            r"\s*[: ]\s*(DENIED|DED|ED|GED|SEED|DD|Dena)\b",
            cleaned,
            re.I,
        )
    )
    if manual and unpaidish:
        return True
    if manual and find_den_garble:
        return True
    return False


def _ocr_manual_adjudicator_rois(pdf_path: Path) -> str:
    """Deskewed top-left ROI OCR for tilted Manual Adjudicator Note pages."""

    try:
        import fitz
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError:
        return ""

    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return ""

    chunks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="mib-adj-roi-") as tmp:
        work = Path(tmp)
        n = 0
        for page in doc:
            for imref in page.get_images(full=True):
                try:
                    info = doc.extract_image(int(imref[0]))
                except Exception:
                    continue
                if int(info.get("width") or 0) < 1000:
                    continue
                try:
                    image = Image.open(io.BytesIO(info["image"])).convert("RGB")
                except Exception:
                    continue
                for ang in (-2, -1, 0, 1, 2):
                    rotated = image.rotate(
                        ang, expand=False, fillcolor=(255, 255, 255)
                    )
                    width, height = rotated.size
                    crop = rotated.crop(
                        (
                            int(width * 0.02),
                            int(height * 0.04),
                            int(width * 0.62),
                            int(height * 0.22),
                        )
                    )
                    up = crop.resize(
                        (max(1, crop.width * 4), max(1, crop.height * 4)),
                        Image.Resampling.LANCZOS,
                    )
                    variants = (
                        up,
                        ImageEnhance.Contrast(ImageOps.autocontrast(up)).enhance(
                            2.2
                        ),
                        ImageOps.autocontrast(up.convert("L"))
                        .point(lambda x: 0 if x < 130 else 255)
                        .convert("RGB"),
                    )
                    for variant in variants:
                        out = work / f"{n}.png"
                        n += 1
                        try:
                            variant.save(out)
                        except Exception:
                            continue
                        for psm in ("6", "11"):
                            try:
                                cp = subprocess.run(
                                    [
                                        "tesseract",
                                        str(out),
                                        "stdout",
                                        "--psm",
                                        psm,
                                        "-l",
                                        "eng",
                                    ],
                                    capture_output=True,
                                    text=True,
                                    errors="replace",
                                    timeout=30,
                                    check=False,
                                )
                                piece = cp.stdout or ""
                            except (OSError, subprocess.TimeoutExpired):
                                piece = ""
                            chunks.append(piece)
                            if piece and _finding_denied(piece):
                                return "\n".join(chunks)
                # Manual Adjudicator note is typically the first large embed.
                return "\n".join(chunks)
    return "\n".join(chunks)


def _finding_needs_review(text: str) -> bool:
    cleaned = re.sub(r"\bsamp\w*\s*denia\w*\b", "", text, flags=re.I)
    return bool(re.search(r"Finding\s*[: ]\s*NEEDS[_\s]?REVIEW\b", cleaned, re.I))


def _risk_tokens(text: str) -> str | None:
    flags: list[str] = []
    lowered = text.lower().replace(" ", "_")
    for flag in (
        "biohazard_red",
        "memory_tampering",
        "active_warrant",
        "planetary_embargo",
        "illegible_biometrics",
        "identity_conflict",
        "sponsor_mismatch",
        "rescinded_denial",
    ):
        if flag in lowered:
            flags.append(flag)
    if re.search(r"Registry\s+Status\s*[: ]\s*EMBARGO", text, re.I):
        flags.append("planetary_embargo")
    for match in re.finditer(r"\bObserved\s+flags?\s*[: ]\s*([^\n]+)", text, re.I):
        blob = match.group(1).lower().replace(" ", "_")
        for flag in (
            "biohazard_red",
            "memory_tampering",
            "active_warrant",
            "planetary_embargo",
            "illegible_biometrics",
            "identity_conflict",
            "sponsor_mismatch",
            "rescinded_denial",
        ):
            if flag in blob and flag not in flags:
                flags.append(flag)
        if re.search(r"\bnone\b", match.group(1), re.I):
            continue
    for flag in _fuzzy_risk_mentions(text):
        if flag not in flags:
            flags.append(flag)
    if not flags:
        return None
    return "|".join(sorted(set(flags)))


def _fuzzy_risk_mentions(text: str) -> set[str]:
    """Recover badly OCRed flag names from flag/reason contexts only."""

    found: set[str] = set()
    all_flags = (
        "biohazard_red",
        "memory_tampering",
        "active_warrant",
        "planetary_embargo",
        "illegible_biometrics",
        "identity_conflict",
        "sponsor_mismatch",
        "rescinded_denial",
    )
    for line in text.splitlines():
        if not re.search(r"\b(?:obs\w*|flags?|risk|reason|finding)\b", line, re.I):
            continue
        words = re.findall(r"[A-Za-z]{3,}", line.lower())
        grams = [
            "".join(words[index:index + width])
            for width in (1, 2, 3)
            for index in range(len(words) - width + 1)
        ]
        for flag in all_flags:
            target = flag.replace("_", "")
            if any(
                difflib.SequenceMatcher(None, gram, target).ratio() >= 0.76
                for gram in grams
            ):
                found.add(flag)
    return found


def _norm_risk(value: str | None) -> str:
    raw = " ".join(str(value or "").strip().split()).casefold()
    if raw in {"", "none", "null", "unknown"}:
        return "none"
    return raw


def _red_channel_sample_denial(pdf_path: Path) -> bool:
    """Detect SAMPLE DENIAL watermarks via red-channel isolation + tesseract.

    Portable (Linux/Docker). Native selectable text often lacks the watermark
    on fully rasterized packets (e.g. MIB-000570).
    """

    try:
        import fitz
        import numpy as np
        from PIL import Image
    except ImportError:
        return False

    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return False

    with tempfile.TemporaryDirectory(prefix="mib-red-samp-") as tmp:
        work = Path(tmp)
        for index, page in enumerate(doc):
            try:
                pix = page.get_pixmap(dpi=180)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            except Exception:
                continue
            arr = np.asarray(image).astype(np.int16)
            red = arr[:, :, 0]
            green = arr[:, :, 1]
            blue = arr[:, :, 2]
            score = np.clip(
                red.astype(np.float32) - 0.5 * green - 0.5 * blue, 0, None
            )
            if float(score.max()) <= 0:
                continue
            scaled = (score / score.max() * 255.0).astype(np.uint8)
            positive = scaled[scaled > 0]
            thr = float(np.percentile(positive, 85)) if positive.size else 200.0
            mask = (scaled >= thr).astype(np.uint8) * 255
            inv = 255 - mask
            out = work / f"{index}.png"
            try:
                Image.fromarray(inv).save(out)
            except Exception:
                continue
            for psm in ("6", "11"):
                try:
                    cp = subprocess.run(
                        [
                            "tesseract",
                            str(out),
                            "stdout",
                            "--psm",
                            psm,
                            "-l",
                            "eng",
                        ],
                        capture_output=True,
                        text=True,
                        errors="replace",
                        timeout=40,
                        check=False,
                    )
                    text = cp.stdout or ""
                except (OSError, subprocess.TimeoutExpired):
                    text = ""
                if re.search(r"SAMP\w*\s*DENI", text, re.I):
                    return True
                if re.search(
                    r"SAMPLE\s+[A-Z0-9]*N[A-Z0-9]*[AIYL]", text, re.I
                ):
                    return True
    return False


def _has_fee_receipt_signal(pdf_path: Path, *, native: str = "") -> bool:
    """True when a fee receipt / Fee Status / Amount is selectable or OCR-visible."""

    blob = native or _native_pdf_text(pdf_path)
    if re.search(r"Fee\s*Receipt|Fee\s+Status|Amount\s*\$", blob, re.I):
        return True

    try:
        import fitz
        from PIL import Image
    except ImportError:
        return False

    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return False

    with tempfile.TemporaryDirectory(prefix="mib-fee-sig-") as tmp:
        work = Path(tmp)
        for index, page in enumerate(doc):
            try:
                pix = page.get_pixmap(dpi=150)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            except Exception:
                continue
            out = work / f"{index}.png"
            try:
                image.save(out)
            except Exception:
                continue
            try:
                cp = subprocess.run(
                    [
                        "tesseract",
                        str(out),
                        "stdout",
                        "--psm",
                        "11",
                        "-l",
                        "eng",
                    ],
                    capture_output=True,
                    text=True,
                    errors="replace",
                    timeout=40,
                    check=False,
                )
                text = cp.stdout or ""
            except (OSError, subprocess.TimeoutExpired):
                text = ""
            if re.search(
                r"MIB\s*Fee\s*Receipt|Fee\s*Receipt|Fee\s*Status\s*:", text, re.I
            ):
                return True
    return False


def _has_hollow_slash_stamp(pdf_path: Path, *, scale: float = 2.0) -> bool:
    """True when a hollow near-square blue slash stamp is present (666 class).

    Geometry gate (aspect≈1, fill≈0.23, area 1000–1800 at 2× render) plus the
    caller’s paid+no-``Amount $809`` gate: train ablation 1 gold DEN / 0 AP /
    0 true-REVIEW.
    """

    try:
        import numpy as np
        import pypdfium2 as pdfium
    except ImportError:
        return False

    def ink_mask(arr: "np.ndarray") -> "np.ndarray":
        r = arr[:, :, 0].astype(np.int16)
        g = arr[:, :, 1].astype(np.int16)
        b = arr[:, :, 2].astype(np.int16)
        return (b > r + 25) & (b > g + 5) & (b > 160) & (r < 210) & (b < 250)

    try:
        document = pdfium.PdfDocument(str(pdf_path))
    except Exception:
        return False
    try:
        from collections import deque

        for index in range(len(document)):
            arr = np.asarray(document[index].render(scale=scale).to_pil().convert("RGB"))
            mask = ink_mask(arr)
            height, width = mask.shape
            visited = np.zeros_like(mask, dtype=bool)
            ys, xs = np.where(mask)
            for y, x in zip(ys, xs):
                if visited[y, x]:
                    continue
                queue = deque([(y, x)])
                visited[y, x] = True
                cells = [(y, x)]
                while queue:
                    cy, cx = queue.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if (
                            0 <= ny < height
                            and 0 <= nx < width
                            and mask[ny, nx]
                            and not visited[ny, nx]
                        ):
                            visited[ny, nx] = True
                            queue.append((ny, nx))
                            cells.append((ny, nx))
                area = len(cells)
                if area < 1000 or area > 1800:
                    continue
                yy = [c[0] for c in cells]
                xx = [c[1] for c in cells]
                bw = max(xx) - min(xx) + 1
                bh = max(yy) - min(yy) + 1
                aspect = bw / max(bh, 1)
                fill = area / (bw * bh)
                if 0.95 <= aspect <= 1.05 and 70 <= bw <= 90 and 0.20 <= fill <= 0.28:
                    return True
    finally:
        document.close()
    return False


def apply_slash_stamp_denial(row: PredictionRow, pdf_path: Path) -> PredictionRow:
    """Deny-only when a hollow slash-square stamp is present on unpaid-class packets."""

    if row.adjudication != "NEEDS_REVIEW":
        return row
    if row.fee_status != "paid":
        return row
    try:
        from .arjun_heads import _pdf_layout_text, _layout_fee_paid_proven
    except Exception:
        return row
    text = _pdf_layout_text(pdf_path)
    if text and _layout_fee_paid_proven(text):
        return row
    if not _has_hollow_slash_stamp(pdf_path):
        return row
    payload = row.to_dict()
    payload["adjudication"] = "DENIED"
    payload["confidence"] = 0.95
    return PredictionRow.from_mapping(payload, fallback_case_id=row.case_id)


def apply_visible_ocr_repairs(
    row: PredictionRow,
    pdf_path: Path,
    *,
    force: bool = False,
) -> PredictionRow:
    """OCR fallback for fee/purpose/deny findings when native path is weak."""

    native = _native_pdf_text(pdf_path)
    native_has_fee = bool(re.search(r"Fee\s+Status|Amount\s*\$", native, re.I))
    sample_denial = bool(re.search(r"SAMPLE\s*[- ]*DENIAL", native, re.I))

    # Image-only unpaid receipts: pred says paid, no selectable fee fields, but
    # SAMPLE DENIAL watermark is present. Requires ROI OCR (not full-page).
    needs_image_unpaid = (
        row.adjudication == "NEEDS_REVIEW"
        and row.fee_status == "paid"
        and (not native_has_fee)
        and sample_denial
    ) or force

    # DIP-1 raster packets: SAMPLE only in pixels, no fee receipt at all → unpaid deny.
    # Skip transit: decoy SAMPLE DENIAL watermarks appear on paid gold APPROVED
    # transit packs (e.g. MIB-000436) without an unpaid fee receipt.
    needs_dip_sample_unpaid = (
        row.adjudication == "NEEDS_REVIEW"
        and row.visa_class == "DIP-1"
        and row.fee_status == "paid"
        and row.declared_purpose != "transit"
        and _norm_risk(row.risk_flags) == "none"
        and (not native_has_fee)
        and (not sample_denial)
    ) or force

    # Do not OCR every paid packet — that is slow and adds decoy noise.
    needs_fee = row.fee_status in {"unknown", "unpaid"} or needs_image_unpaid or force
    needs_purpose = row.declared_purpose == "reactor maintenance" or force
    needs_deny = (
        row.adjudication == "NEEDS_REVIEW" and _norm_risk(row.risk_flags) == "none"
    ) or force
    needs_review_finding = row.adjudication == "DENIED" or force
    if not (
        needs_fee
        or needs_purpose
        or needs_deny
        or needs_review_finding
        or needs_dip_sample_unpaid
    ):
        return row

    # SAMPLE-gated Manual Adjudicator deskew OCR (Finding:DENIED / fee unpaid).
    needs_manual_finding = (
        needs_deny and sample_denial and (not native_has_fee)
    ) or force

    text = ""
    if needs_fee or needs_purpose or needs_deny or needs_review_finding:
        text = _ocr_packet(pdf_path)
        if needs_image_unpaid:
            text = f"{text}\n{_ocr_fee_receipt_rois(pdf_path)}"
        if needs_manual_finding and not _finding_denied(text):
            text = f"{text}\n{_ocr_manual_adjudicator_rois(pdf_path)}"

    payload = row.to_dict()
    changed = False

    if needs_dip_sample_unpaid and payload.get("adjudication") == "NEEDS_REVIEW":
        if _red_channel_sample_denial(pdf_path) and not _has_fee_receipt_signal(
            pdf_path, native=native
        ):
            payload["fee_status"] = "unpaid"
            payload["adjudication"] = "DENIED"
            payload["confidence"] = 0.98
            changed = True

    if not text.strip() and not changed:
        return row
    if not text.strip() and changed:
        return PredictionRow.from_mapping(payload, fallback_case_id=row.case_id)

    fee = _fee_from_ocr(text)
    if fee and fee != payload.get("fee_status"):
        # Prefer OCR waived over a serialized paid guess when receipt is image-only.
        # Allow paid→unpaid only on the SAMPLE-gated image-only path (decoy guard).
        # Never let OCR waived clobber layout-proven Amount $809 paid.
        layout_paid = bool(
            re.search(r"Amount\s*\$?\s*809(?:\.\d+)?\b", native, re.I)
        )
        if fee == "waived" and payload.get("fee_status") == "paid" and layout_paid:
            pass
        elif fee == "waived" or payload.get("fee_status") in {"unknown", "unpaid"}:
            payload["fee_status"] = fee
            changed = True
        elif fee == "paid" and payload.get("fee_status") == "unknown":
            payload["fee_status"] = fee
            changed = True
        elif fee == "unpaid" and needs_image_unpaid and sample_denial:
            payload["fee_status"] = "unpaid"
            changed = True

    if needs_purpose:
        purpose = _purpose_from_ocr(text)
        if purpose and purpose != payload.get("declared_purpose"):
            payload["declared_purpose"] = purpose
            changed = True

    risk = _risk_tokens(text)
    if risk and (
        payload.get("risk_flags") in {None, "", "none"}
        or payload.get("risk_flags") == "none"
    ):
        payload["risk_flags"] = risk
        changed = True

    finding_deny = needs_deny and _finding_denied(text)
    if finding_deny and payload.get("adjudication") != "DENIED":
        payload["adjudication"] = "DENIED"
        payload["confidence"] = 0.98
        # Manual note "mandatory fee unpaid" on SAMPLE image packets → unpaid.
        if (
            sample_denial
            and (not native_has_fee)
            and payload.get("fee_status") == "paid"
            and re.search(
                r"(unpaid|enpaid|wepuil|wnpell|umgpae|feo\s*un|fe\s*un|fee\s*un)",
                re.sub(r"\bsamp\w*\s*denia\w*\b", "", text, flags=re.I),
                re.I,
            )
        ):
            payload["fee_status"] = "unpaid"
        changed = True
    elif (
        needs_image_unpaid
        and payload.get("fee_status") == "unpaid"
        and payload.get("adjudication") == "NEEDS_REVIEW"
    ):
        # Unpaid without selectable waiver on SAMPLE-gated image receipt → DENY.
        payload["adjudication"] = "DENIED"
        payload["confidence"] = 0.98
        changed = True
    elif needs_review_finding and _finding_needs_review(text):
        # Exact Finding:NEEDS_REVIEW only — demote DENIED → REVIEW, never approve.
        payload["adjudication"] = "NEEDS_REVIEW"
        payload["confidence"] = max(float(payload.get("confidence") or 0), 0.85)
        changed = True
    elif risk:
        disq = {
            "biohazard_red",
            "memory_tampering",
            "active_warrant",
            "planetary_embargo",
        }
        if set(risk.split("|")) & disq and payload.get("adjudication") in {
            "NEEDS_REVIEW",
            "APPROVED",
        }:
            payload["adjudication"] = "DENIED"
            payload["confidence"] = 0.98
            changed = True

    if not changed:
        return row
    return PredictionRow.from_mapping(payload, fallback_case_id=row.case_id)
