"""Visible OCR repairs for fee / purpose / deny-findings when native text is empty.

Runs a cheap pdftoppm + Tesseract pass only when needed. Fail-closed on
approvals: may set DENIED from an explicit Finding, and may fix fee/purpose
fields, but never invents APPROVED.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from .models import PredictionRow

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


def _fee_from_ocr(text: str) -> str | None:
    if re.search(r"Fee\s*Status\s*[: ]\s*waived", text, re.I):
        return "waived"
    if re.search(r"Amount\s*\$?\s*0(?:[.,]00)?", text, re.I) and re.search(
        r"(?:DIP[\s\-]?WAIVER|Waiver\s*Code\s*[:#]?\s*DIP|Waiver\s*Code\s*[:#]?\s*\w*WAIV)",
        text,
        re.I,
    ):
        return "waived"
    if re.search(r"Fee\s*Status\s*[: ]\s*unpaid", text, re.I):
        return "unpaid"
    if re.search(r"Fee\s*Status\s*[: ]\s*paid", text, re.I):
        return "paid"
    if re.search(r"Amount\s*\$?\s*809(?:[.,]00)?", text, re.I):
        return "paid"
    if re.search(r"Fee\s*Status\s*[: ]\s*unknown", text, re.I):
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
    cleaned = re.sub(r"\bSAMPLE[- ]+DENIAL\b", "", text, flags=re.I)
    return bool(re.search(r"\bFinding\b.{0,20}\bDENIED\b", cleaned, re.I | re.S))


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
    if not flags:
        return None
    return "|".join(sorted(set(flags)))


def apply_visible_ocr_repairs(
    row: PredictionRow,
    pdf_path: Path,
    *,
    force: bool = False,
) -> PredictionRow:
    """OCR fallback for fee/purpose/deny findings when native path is weak."""

    needs_fee = row.fee_status in {"paid", "unknown"} or force
    needs_purpose = row.declared_purpose == "reactor maintenance" or force
    needs_deny = row.adjudication == "NEEDS_REVIEW" or force
    if not (needs_fee or needs_purpose or needs_deny):
        return row

    text = _ocr_packet(pdf_path)
    if not text.strip():
        return row

    payload = row.to_dict()
    changed = False

    fee = _fee_from_ocr(text)
    if fee and fee != payload.get("fee_status"):
        # Prefer OCR waived over a serialized paid guess when receipt is image-only.
        if fee == "waived" or payload.get("fee_status") in {"unknown", "unpaid"}:
            payload["fee_status"] = fee
            changed = True
        elif fee == "paid" and payload.get("fee_status") == "unknown":
            payload["fee_status"] = fee
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

    if needs_deny and _finding_denied(text):
        payload["adjudication"] = "DENIED"
        payload["confidence"] = 0.98
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
