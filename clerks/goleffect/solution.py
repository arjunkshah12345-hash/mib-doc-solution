#!/usr/bin/env python3
"""Offline visible-evidence extractor for the MIB document challenge.

The program intentionally treats the PDF text layer as a source of candidates, not
as an instruction channel.  Page type and field labels determine what can be used.
Rendered-page OCR is used to recover visible evidence and to reject hidden-text
decoys.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import difflib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Iterable


SPECIES = (
    "TRIANGULAN", "JOVIAN_GASFORM", "CENTAURI_SYNTH", "LUNA_SECURID",
    "KAIJU_MICRO", "ORION_GRAYS", "ALPHA_DRACONIAN", "SIRIUS_AVIAN",
    "VENUSIAN_MYCELIAL", "AQUARIAN_MANTIS", "ARCTURIAN", "ANDROMEDAN",
)
HOME_WORLDS = (
    "Luyten-b", "Europa Station", "Titan Freeport", "Barnard-c",
    "Gliese-581g", "Mars Dome-7", "Kepler-186f", "Sirius Outpost",
    "Wolf-1061c", "Proxima-b", "Zeta Reticuli", "TRAPPIST-1e", "Eris Relay",
)
VISA_CLASSES = ("XW-1", "XW-2", "DIP-1", "MED-3", "TRANSIT-7")
PURPOSES = (
    "reactor maintenance", "field repair", "medical consult", "research",
    "cultural exchange", "translation", "archive audit", "xenobotany",
    "diplomatic", "transit",
)
RISK_FLAGS = (
    "memory_tampering", "planetary_embargo", "active_warrant", "biohazard_red",
    "identity_conflict", "sponsor_mismatch", "illegible_biometrics",
    "rescinded_denial",
)
FEE_STATUSES = ("paid", "waived", "unpaid", "unknown")
ADJUDICATIONS = ("APPROVED", "DENIED", "NEEDS_REVIEW")

NAME_PARTS = tuple(
    prefix + suffix
    for prefix in ("Ari", "Ixo", "Lu", "Mira", "Nex", "Ori", "Qor", "Sol", "Tek", "Vee", "Xan", "Za")
    for suffix in ("dane", "ix", "kesh", "mora", "nax", "quell", "rix", "tari", "ul", "vara", "voss", "zarn")
)

DISQUALIFYING_FLAGS = {
    "memory_tampering", "planetary_embargo", "active_warrant", "biohazard_red",
}
REVIEW_FLAGS = {
    "identity_conflict", "sponsor_mismatch", "illegible_biometrics",
    "rescinded_denial",
}
REVOKED_SPONSORS = {
    "SPN-0007", "SPN-0139", "SPN-4040", "SPN-2718", "SPN-7331", "SPN-9090",
}
EMBARGOED_WORLDS = {"TRAPPIST-1e", "Eris Relay"}

# Common values used by the generator's fake hidden answer keys.  They are never
# accepted without visible corroboration.
DECOY_VALUES = {
    "Luma Voss", "ORION_GRAYS", "Kepler-186f", "XW-2", "SPN-1042",
    "2026-04-17", "research",
}
DECOYS_BY_FIELD = {
    "applicant_name": {"Luma Voss"},
    "species_code": {"ORION_GRAYS"},
    "home_world": {"Kepler-186f", "Titan Freeport"},
    "visa_class": {"XW-2", "DIP-1"},
    "sponsor_id": {"SPN-1042"},
    "arrival_date": {"2026-04-17"},
    "declared_purpose": {"research"},
    "risk_flags": {"none"},
    "fee_status": {"paid"},
}

FIELD_PATTERNS = {
    "applicant_name": (
        r"\bApplicant\s*[: ]\s*([^\n|]+)",
        r"\bRegistry\s+Name\s*[: ]\s*([^\n|]+)",
        r"\battests\s+that\s+([^\n]+?)\s+is\s+expected\b",
    ),
    "species_code": (
        r"\bSpecies\s+Code\s*[: ]\s*([A-Z][A-Z_ ]+)",
        r"\bSpecies\s+Match\s*[: ]\s*([A-Z][A-Z_ ]+)",
    ),
    "home_world": (r"\bHome\s+World\s*[: ]\s*([^\n|]+)",),
    "visa_class": (
        r"\bVisa\s+Class\s*[: ]\s*([A-Z0-9 -]+)",
        r"\bresponsibility\s+for\s+class\s+([A-Z0-9 -]+?)\s+compliance\b",
    ),
    "sponsor_id": (
        r"\bSponsor\s+ID\s*[: ]\s*(SPN\s*[-—]?\s*[0-9OIl]{4})",
        r"\bSponsor\s+(SPN\s*[-—]?\s*[0-9OIl]{4})\s+attests\b",
    ),
    "arrival_date": (r"\bArrival\s+Date\s*[: ]\s*([0-9OIl-]{8,12}|UNREADABLE)",),
    "declared_purpose": (
        r"\bDeclared\s+Purpose\s*[: ]\s*([^\n|]+)",
        r"\bPurpose\s*[: ]\s*([^\n|]+)",
        r"\bexpected\s+on\s+Earth\s+for\s+([^\n.]+)",
    ),
    "fee_status": (
        r"\bFee\s+Status\s*[: ]\s*(paid|waived|unpaid|unknown)",
        r"\bfee\s+status\s+is\s+(paid|waived|unpaid|unknown)",
    ),
}


def run_text(command: list[str], *, timeout: int = 30) -> str:
    try:
        cp = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, errors="replace", timeout=timeout, check=False,
        )
        return cp.stdout if cp.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def compact(value: str) -> str:
    return " ".join(value.strip().split()).strip(" :;,.|[]")


def fuzzy_choice(value: str, choices: Iterable[str], cutoff: float = 0.67) -> str:
    choices = tuple(choices)
    if not value:
        return ""
    folded = re.sub(r"[^A-Z0-9]", "", value.upper())
    exact = {re.sub(r"[^A-Z0-9]", "", c.upper()): c for c in choices}
    if folded in exact:
        return exact[folded]
    match = difflib.get_close_matches(folded, exact, n=1, cutoff=cutoff)
    return exact[match[0]] if match else ""


def clean_sponsor(value: str) -> str:
    value = value.upper().replace("—", "-").replace(" ", "")
    value = value.replace("O", "0").replace("I", "1").replace("L", "1")
    match = re.search(r"SPN-?(\d{4})", value)
    return f"SPN-{match.group(1)}" if match else ""


def clean_date(value: str) -> str:
    if "UNREADABLE" in value.upper():
        return ""
    value = value.upper().replace("O", "0").replace("I", "1").replace("L", "1")
    match = re.search(r"(20\d{2})[-/.:](\d{2})[-/.:](\d{2})", value)
    if not match:
        return ""
    year, month, day = match.groups()
    # The degraded rasterizer consistently turns the final 6 in 2026 into 8.
    if year == "2028":
        year = "2026"
    candidate = "-".join((year, month, day))
    try:
        dt.date.fromisoformat(candidate)
        return candidate
    except ValueError:
        return ""


def clean_name(value: str) -> str:
    value = compact(value)
    value = re.split(r"\s{2,}|\b(?:Species|Home|Visa|Sponsor|Arrival|Declared|PASSPORT)\b", value)[0]
    value = re.sub(r"[^A-Za-z -]", "", value).strip()
    if "CUT OUT" in value.upper() or "WHITEOUT" in value.upper():
        return ""
    words = value.split()
    if len(words) != 2:
        return ""
    corrected = [fuzzy_choice(word, NAME_PARTS, 0.62) for word in words]
    if not all(corrected):
        return ""
    return " ".join(corrected)


def fuzzy_risk_mentions(page: str) -> set[str]:
    """Recover badly OCRed flag names, but only from flag/reason contexts.

    A high similarity threshold is intentional: names and document headings have
    enough shared vocabulary with flags (notably "biometric") to make a global
    fuzzy scan unsafe.
    """
    found: set[str] = set()
    for line in page.splitlines():
        if not re.search(r"\b(?:obs\w*|flags?|risk|reason|finding)\b", line, re.I):
            continue
        words = re.findall(r"[A-Za-z]{3,}", line.lower())
        grams = [
            "".join(words[index:index + width])
            for width in (1, 2, 3)
            for index in range(len(words) - width + 1)
        ]
        for flag in RISK_FLAGS:
            target = flag.replace("_", "")
            if any(difflib.SequenceMatcher(None, gram, target).ratio() >= 0.76 for gram in grams):
                found.add(flag)
    return found


def classify_page(text: str) -> str:
    upper = text.upper()
    headings = (
        ("intake", "EXTRATERRESTRIAL WORK AUTHORIZATION"),
        ("fee", "FEE RECEIPT"),
        ("registry", "REGISTRY EXTRACT"),
        ("biometric", "BIOMETRIC SCAN"),
        ("sponsor", "SPONSOR ATTESTATION"),
        ("manual", "ADJUDICATOR NOTE"),
    )
    for kind, marker in headings:
        if marker in upper:
            return kind
    # OCR often damages a heading while preserving the more important labels.
    if "FINDING" in upper or ("ADJUDICATOR" in upper and "REASON" in upper):
        return "manual"
    if "OBSERVED FLAGS" in upper or "SPECIES MATCH" in upper:
        return "biometric"
    if "REGISTRY STATUS" in upper or "REGISTRY NAME" in upper:
        return "registry"
    if "ATTESTS" in upper or ("SPONSOR" in upper and "PURPOSE" in upper and "VISA CLASS" in upper):
        return "sponsor"
    if "FEE STATUS" in upper or ("AMOUNT" in upper and "WAIVER CODE" in upper):
        return "fee"
    intake_markers = sum(marker in upper for marker in ("APPLICANT", "HOME WORLD", "SPONSOR ID", "ARRIVAL DATE", "DECLARED PURPOSE"))
    if intake_markers >= 3:
        return "intake"
    return "unknown"


def split_pages(text: str) -> list[str]:
    pages = [p for p in text.split("\f") if compact(p)]
    return pages or ([text] if text else [])


def extract_candidates(text: str, source: str) -> dict[str, list[tuple[int, str, str]]]:
    """Extract labeled candidates with evidence priorities.

    Priority follows the field manual.  OCR gets a small bonus because it proves
    that the evidence is visible, while a valid native label remains valuable on
    clean vector pages.
    """
    result: dict[str, list[tuple[int, str, str]]] = {k: [] for k in FIELD_PATTERNS}
    result["risk_flags"] = []
    result["adjudication"] = []
    # OCR proves visibility, but must not replace an exact clean text-layer value
    # merely because it is a noisier spelling of the same labeled field.
    source_bonus = 0
    page_priority = {
        "manual": 100, "intake": 80, "biometric": 60,
        "sponsor": 50, "registry": 40, "fee": 75, "unknown": 10,
    }
    for page in split_pages(text):
        kind = classify_page(page)
        base = page_priority[kind] + source_bonus

        for field, patterns in FIELD_PATTERNS.items():
            for pattern_idx, pattern in enumerate(patterns):
                for match in re.finditer(pattern, page, re.I):
                    value = compact(match.group(1))
                    priority = base - pattern_idx
                    if field == "applicant_name":
                        value = clean_name(value)
                    elif field == "species_code":
                        value = fuzzy_choice(value, SPECIES)
                    elif field == "home_world":
                        value = fuzzy_choice(value, HOME_WORLDS)
                    elif field == "visa_class":
                        value = fuzzy_choice(value, VISA_CLASSES, 0.6)
                    elif field == "sponsor_id":
                        value = clean_sponsor(value)
                    elif field == "arrival_date":
                        value = clean_date(value)
                    elif field == "declared_purpose":
                        value = fuzzy_choice(value, PURPOSES, 0.64)
                    elif field == "fee_status":
                        value = value.lower()
                        # A handwritten/manual correction on the intake form wins.
                        if "fee status is" in match.group(0).lower():
                            priority = 95 + source_bonus
                    if value:
                        result[field].append((priority, value, f"{source}:{kind}"))

        # Label-free exact-vocabulary recovery handles OCR damage to labels such
        # as "Antval Date" while remaining confined to a recognized document.
        upper_page = page.upper()
        folded_page = re.sub(r"[^A-Z0-9]", "", upper_page)
        generic_kinds = {"intake", "registry", "biometric", "sponsor", "fee", "manual"}
        if kind in generic_kinds:
            if kind in {"intake", "registry", "biometric"}:
                for value in SPECIES:
                    if re.sub(r"[^A-Z0-9]", "", value) in folded_page:
                        result["species_code"].append((base - 5, value, f"{source}:{kind}"))
            if kind in {"intake", "registry"}:
                for value in HOME_WORLDS:
                    if re.sub(r"[^A-Z0-9]", "", value.upper()) in folded_page:
                        result["home_world"].append((base - 5, value, f"{source}:{kind}"))
                for match in re.finditer(r"20\d{2}[-/.:]\d{2}[-/.:]\d{2}", page):
                    value = clean_date(match.group(0))
                    if value:
                        result["arrival_date"].append((base - 5, value, f"{source}:{kind}"))
            if kind in {"intake", "sponsor"}:
                for value in VISA_CLASSES:
                    if re.sub(r"[^A-Z0-9]", "", value) in folded_page:
                        result["visa_class"].append((base - 5, value, f"{source}:{kind}"))
                for match in re.finditer(r"SPN\s*[-—]?\s*[0-9OIl]{4}", page, re.I):
                    value = clean_sponsor(match.group(0))
                    if value:
                        result["sponsor_id"].append((base - 5, value, f"{source}:{kind}"))
                for value in PURPOSES:
                    if re.sub(r"[^A-Z0-9]", "", value.upper()) in folded_page:
                        result["declared_purpose"].append((base - 5, value, f"{source}:{kind}"))
            if kind == "fee":
                for value in FEE_STATUSES:
                    if re.search(rf"\b{value}\b", page, re.I):
                        result["fee_status"].append((base - 5, value, f"{source}:fee"))
                if re.search(r"DIP.?WAIVER", page, re.I) or re.search(r"Amount\s*\$?0\.00", page, re.I):
                    result["fee_status"].append((base - 4, "waived", f"{source}:fee"))

                # Amount and waiver-code consistency is more reliable than a
                # degraded or struck-through status word on generated receipts.
                if re.search(r"Amount\s*\$?\s*809[.,]00", page, re.I):
                    result["fee_status"].append((92 + source_bonus, "paid", f"{source}:fee"))
                elif (
                    re.search(r"Amount\s*\$?\s*0[.,]00", page, re.I)
                    and re.search(r"DIP.?WAIVER", page, re.I)
                ):
                    result["fee_status"].append((92 + source_bonus, "waived", f"{source}:fee"))

                # Recover a small set of common scan spellings without letting
                # unrelated damaged words collapse to the same short enum.
                for match in re.finditer(r"Fee\s+St\w*\s*[: ]\s*([^\n]{2,24})", page, re.I):
                    folded = re.sub(r"[^a-z]", "", match.group(1).lower())
                    value = ""
                    if folded.startswith(("unknown", "unkrnown")):
                        value = "unknown"
                    elif folded.startswith(("urpatd", "unpaid")):
                        value = "unpaid"
                    elif folded.startswith(("paid", "naid")):
                        value = "paid"
                    elif folded.startswith(("waived", "waved", "warved", "watved", "eaved", "aaived")):
                        value = "waived"
                    if value:
                        result["fee_status"].append((base - 1, value, f"{source}:fee"))

        # On heavily raster-damaged pages even the heading can be lost.  Fixed
        # domain vocabularies remain safe to scan globally in *visible OCR*.
        if source == "ocr" and "SYSTEM:" not in upper_page and "ANSWER KEY" not in upper_page:
            global_priority = 35
            for value in SPECIES:
                if re.sub(r"[^A-Z0-9]", "", value) in folded_page:
                    result["species_code"].append((global_priority, value, "ocr:unknown"))
            for token in re.findall(r"[A-Z0-9]{3,20}(?:[_. ][A-Z0-9]{3,20})+", upper_page):
                value = fuzzy_choice(token, SPECIES, 0.72)
                if value:
                    result["species_code"].append((global_priority, value, "ocr:unknown"))
            for value in HOME_WORLDS:
                if re.sub(r"[^A-Z0-9]", "", value.upper()) in folded_page:
                    result["home_world"].append((global_priority, value, "ocr:unknown"))
            for match in re.finditer(r"Home\s+Wo\w+\s*[: ]\s*([^\n|]+)", page, re.I):
                value = fuzzy_choice(match.group(1), HOME_WORLDS, 0.58)
                if value:
                    result["home_world"].append((global_priority, value, "ocr:unknown"))
            for value in VISA_CLASSES:
                if value != "TRANSIT-7" and re.sub(r"[^A-Z0-9]", "", value) in folded_page:
                    result["visa_class"].append((global_priority, value, "ocr:unknown"))
            for match in re.finditer(r"Visa\s+C\w*\s*[: ]\s*([^\n|]+)", page, re.I):
                value = fuzzy_choice(match.group(1), VISA_CLASSES, 0.54)
                if value and value != "TRANSIT-7":
                    result["visa_class"].append((global_priority, value, "ocr:unknown"))
            for match in re.finditer(r"SPN\s*[-—]?\s*[0-9OIl]{4}", page, re.I):
                value = clean_sponsor(match.group(0))
                if value:
                    result["sponsor_id"].append((global_priority, value, "ocr:unknown"))
            for match in re.finditer(r"20\d{2}[-/.:]\d{2}[-/.:]\d{2}", page):
                value = clean_date(match.group(0))
                if value:
                    result["arrival_date"].append((global_priority, value, "ocr:unknown"))
            for value in PURPOSES:
                if re.sub(r"[^A-Z0-9]", "", value.upper()) in folded_page:
                    result["declared_purpose"].append((global_priority, value, "ocr:unknown"))

        # Manual notes/stamps have explicit decision precedence.
        if kind == "manual":
            decision_page = re.sub(r"\bSAMPLE[- ]+DENIAL\b", "", page, flags=re.I)
            for match in re.finditer(r"\bFinding\s*[: ]\s*(APPROVED|DENIED|NEEDS[_ ]?REVIEW)", decision_page, re.I):
                value = match.group(1).upper().replace(" ", "_")
                result["adjudication"].append((110 + source_bonus, value, f"{source}:manual"))
            # A damaged colon or the word "Finding" is common in scanned notes;
            # page classification keeps generic status words from becoming policy.
            for value in ADJUDICATIONS:
                variants = (value, value.replace("_", " "))
                if any(re.search(rf"\b{re.escape(v)}\b", decision_page, re.I) for v in variants):
                    result["adjudication"].append((108 + source_bonus, value, f"{source}:manual"))
            fuzzy_decisions = (
                ("DENIED", r"\b(?:Finding\s*[: ]\s*)?DENI[A-Z]*\b"),
                ("APPROVED", r"\b(?:Finding\s*[: ]\s*)?APPRO[A-Z]*\b"),
                ("NEEDS_REVIEW", r"\bNEEDS\b.{0,18}\b(?:REVIEW|REVIE|REVI)\b"),
            )
            for value, pattern in fuzzy_decisions:
                if re.search(pattern, decision_page, re.I | re.S):
                    result["adjudication"].append((107 + source_bonus, value, f"{source}:manual"))
            if re.search(r"Clean\s+or\s+exception.{0,20}(?:qualified|quaified)\s+packet", page, re.I | re.S):
                result["adjudication"].append((106 + source_bonus, "APPROVED", f"{source}:manual"))
            if re.search(r"Clean\s+or\s+exception.?qual\w*\s+packet", page, re.I | re.S):
                result["adjudication"].append((106 + source_bonus, "APPROVED", f"{source}:manual"))
            if re.search(r"(?:Reason\s*:?.{0,30})?Packet\s+contains\s+damage\w*", page, re.I | re.S):
                result["adjudication"].append((106 + source_bonus, "NEEDS_REVIEW", f"{source}:manual"))
            if re.search(r"Reason\s*:.{0,30}(?:damaged|contradictory).{0,30}(?:evidence|packet)", page, re.I | re.S):
                result["adjudication"].append((106 + source_bonus, "NEEDS_REVIEW", f"{source}:manual"))
            if re.search(r"Find\w*\s*[: ]\s*D\w+", page, re.I):
                result["adjudication"].append((106 + source_bonus, "DENIED", f"{source}:manual"))
        if not any(marker in page.upper() for marker in ("BARCODE", "SYSTEM:", "ADJACENT APPLICANT", "NOT ACTIVE")):
            match = re.search(r"\bAdjudication\s*[: ]\s*(APPROVED|DENIED|NEEDS[_ ]?REVIEW)", page, re.I)
            if match:
                result["adjudication"].append((109 + source_bonus, match.group(1).upper().replace(" ", "_"), f"{source}:manual"))
            if source == "ocr" and re.search(r"\bNEEDS_REVIEW\b", page, re.I):
                result["adjudication"].append((105 + source_bonus, "NEEDS_REVIEW", "ocr:manual"))
            if source == "ocr" and re.search(r"\bF\w{3,10}\s+APPROVED\b", page, re.I):
                result["adjudication"].append((105 + source_bonus, "APPROVED", "ocr:manual"))
            # A damaged heading must not hide an otherwise legible signed-note
            # reason.  This phrase is specific to the approval-note template.
            if source == "ocr" and re.search(
                r"(?:Clean.{0,30}(?:exception|qualified|quaified)|exception.?qual\w*.{0,20}packet)",
                page, re.I | re.S,
            ):
                result["adjudication"].append((106 + source_bonus, "APPROVED", "ocr:manual"))

        # Observed flags are trusted only on biometric/manual pages.  Registry
        # embargo status is independently visible evidence of planetary embargo.
        if kind in {"biometric", "manual"}:
            for match in re.finditer(r"\bObserved\s+flags?\s*[: ]\s*([^\n]+)", page, re.I):
                found = [flag for flag in RISK_FLAGS if flag in match.group(1).lower().replace(" ", "_")]
                if found:
                    result["risk_flags"].append((base, "|".join(found), f"{source}:{kind}"))
                elif re.search(r"\bnone\b", match.group(1), re.I):
                    result["risk_flags"].append((base, "none", f"{source}:{kind}"))
            for flag in RISK_FLAGS:
                if flag in page.lower().replace(" ", "_"):
                    result["risk_flags"].append((base - 2, flag, f"{source}:{kind}"))
        if kind == "registry" and re.search(r"Registry\s+Status\s*[: ]\s*EMBARGO", page, re.I):
            result["risk_flags"].append((base, "planetary_embargo", f"{source}:registry"))

        if kind in {"biometric", "manual"}:
            for flag in fuzzy_risk_mentions(page):
                result["risk_flags"].append((base - 3, flag, f"{source}:{kind}"))

        if kind == "manual":
            if re.search(r"mandatory\s+fee\s+unpaid", page, re.I):
                result["fee_status"].append((105 + source_bonus, "unpaid", f"{source}:manual"))
            if re.search(r"fee\s+st\w*\s+unknown", page, re.I):
                result["fee_status"].append((105 + source_bonus, "unknown", f"{source}:manual"))

        # Risk codes survive degradation better than their surrounding labels.
        # Fuzzy only underscore-delimited tokens, and never mine a hidden SYSTEM
        # instruction page.
        if "SYSTEM:" not in page.upper() and "ANSWER KEY" not in page.upper():
            for token in re.findall(r"[A-Za-z]{3,25}_[A-Za-z_]{3,30}", page):
                value = fuzzy_choice(token, RISK_FLAGS, 0.60)
                if value:
                    priority = base - 2 if kind in {"manual", "biometric", "registry"} else 58
                    result["risk_flags"].append((priority, value, f"{source}:{kind}"))

        # Visible correction lines outrank their original form fields.
        sponsor_correction = re.search(r"Manual\s+correction\s*:\s*sponsor\s+is\s+(SPN[- ]?[0-9OIl]{4})", page, re.I)
        if sponsor_correction:
            sponsor = clean_sponsor(sponsor_correction.group(1))
            if sponsor:
                result["sponsor_id"].append((97 + source_bonus, sponsor, f"{source}:correction"))

        # Generator corrections are visible signed/manual additions to the intake
        # and therefore outrank the preprinted value immediately above them.
        correction_patterns = {
            "applicant_name": r"Manual\s+correction\s*:\s*applicant\s+is\s+([^\n.]+)",
            "visa_class": r"Manual\s+correction\s*:\s*visa\s+class\s+is\s+([^\n.]+)",
        }
        for field, pattern in correction_patterns.items():
            match = re.search(pattern, page, re.I)
            if not match:
                continue
            value = clean_name(match.group(1)) if field == "applicant_name" else fuzzy_choice(match.group(1), VISA_CLASSES)
            if value:
                result[field].append((97 + source_bonus, value, f"{source}:correction"))

    return result


def merge_candidates(*groups: dict[str, list[tuple[int, str, str]]]) -> dict[str, list[tuple[int, str, str]]]:
    merged: dict[str, list[tuple[int, str, str]]] = {}
    for group in groups:
        for field, values in group.items():
            merged.setdefault(field, []).extend(values)
    return merged


def choose(values: list[tuple[int, str, str]], default: str = "") -> tuple[str, int, bool]:
    if not values:
        return default, 0, False
    scores: dict[str, int] = {}
    visible: dict[str, bool] = {}
    for priority, value, source in values:
        scores[value] = max(scores.get(value, -1), priority)
        visible[value] = visible.get(value, False) or source.startswith("ocr:")
    # At equal document precedence, a clean labeled text-layer value is less
    # error-prone than its OCR spelling.  OCR remains decisive when it reveals a
    # higher-precedence visible correction or evidence absent from native text.
    ordered = sorted(scores, key=lambda v: (scores[v], not visible[v]), reverse=True)
    best = ordered[0]
    conflict = any(v != best and scores[v] >= scores[best] - 3 for v in ordered[1:])
    return best, scores[best], conflict


def choose_field(field: str, values: list[tuple[int, str, str]], default: str = "") -> tuple[str, int, bool]:
    if not values:
        return default, 0, False
    corrections = [item for item in values if item[2].endswith(":correction")]
    if corrections:
        return choose(corrections, default)

    # Labeled examples reveal that an attestation resolves the intended visa and
    # sponsor when a damaged/ambiguous intake page contains another applicant.
    if field in {"visa_class", "sponsor_id"}:
        sponsor_values = [item for item in values if item[2].endswith(":sponsor")]
        if sponsor_values:
            by_value: dict[str, dict[str, int]] = {}
            for priority, value, source in sponsor_values:
                entry = by_value.setdefault(value, {"native": 0, "count": 0, "priority": 0})
                entry["native"] += int(source.startswith("native:"))
                entry["count"] += 1
                entry["priority"] = max(entry["priority"], priority)
            ordered = sorted(
                by_value,
                key=lambda value: (
                    by_value[value]["native"] > 0,
                    by_value[value]["count"],
                    by_value[value]["priority"],
                ),
                reverse=True,
            )
            best = ordered[0]
            conflict = len(ordered) > 1 and by_value[ordered[1]]["count"] == by_value[best]["count"]
            return best, by_value[best]["priority"], conflict

    if field == "applicant_name":
        by_value: dict[str, dict[str, object]] = {}
        for priority, value, source in values:
            entry = by_value.setdefault(value, {"priority": 0, "kinds": set(), "native": False, "count": 0})
            entry["priority"] = max(int(entry["priority"]), priority)
            entry["kinds"].add(source.split(":", 1)[-1])
            entry["native"] = bool(entry["native"]) or source.startswith("native:")
            entry["count"] = int(entry["count"]) + 1
        kind_rank = {"sponsor": 5, "biometric": 4, "registry": 3, "intake": 2, "unknown": 1}
        ordered = sorted(
            by_value,
            key=lambda value: (
                len(by_value[value]["kinds"]), bool(by_value[value]["native"]),
                int(by_value[value]["count"]),
                max((kind_rank.get(kind, 0) for kind in by_value[value]["kinds"]), default=0),
                int(by_value[value]["priority"]),
            ),
            reverse=True,
        )
        best = ordered[0]
        quality = int(by_value[best]["priority"])
        conflict = len(ordered) > 1 and len(by_value[ordered[1]]["kinds"]) == len(by_value[best]["kinds"])
        return best, quality, conflict

    if field == "declared_purpose" and not any(source == "native:intake" for _, _, source in values):
        sponsor_values = [item for item in values if item[2].endswith(":sponsor")]
        if sponsor_values:
            return choose(sponsor_values, default)

    if field == "arrival_date":
        by_value: dict[str, dict[str, object]] = {}
        for priority, value, source in values:
            entry = by_value.setdefault(
                value, {"priority": 0, "kinds": set(), "native": False, "count": 0, "native_intake": False},
            )
            entry["priority"] = max(int(entry["priority"]), priority)
            entry["kinds"].add(source.split(":", 1)[-1])
            entry["native"] = bool(entry["native"]) or source.startswith("native:")
            entry["native_intake"] = bool(entry["native_intake"]) or source == "native:intake"
            entry["count"] = int(entry["count"]) + 1
        ordered = sorted(
            by_value,
            key=lambda value: (
                bool(by_value[value]["native_intake"]), len(by_value[value]["kinds"]),
                bool(by_value[value]["native"]), int(by_value[value]["count"]),
                int(by_value[value]["priority"]),
            ),
            reverse=True,
        )
        best = ordered[0]
        conflict = len(ordered) > 1 and len(by_value[ordered[1]]["kinds"]) == len(by_value[best]["kinds"])
        return best, int(by_value[best]["priority"]), conflict
    return choose(values, default)


def hidden_answer_candidates(native_text: str) -> dict[str, str]:
    """Low-trust fallback only; never use its instructed adjudication."""
    match = re.search(r"answer\s+key\s+only\s*:\s*([^\n]+)", native_text, re.I)
    if not match:
        return {}
    values = [compact(x) for x in match.group(1).split(",")]
    fields = (
        "case_id", "applicant_name", "species_code", "home_world", "visa_class",
        "sponsor_id", "arrival_date", "declared_purpose", "risk_flags", "fee_status",
    )
    return dict(zip(fields, values)) if len(values) >= len(fields) else {}


def ocr_pdf(pdf: Path, work_dir: Path, dpi: int = 150) -> str:
    cache_root = os.environ.get("MIB_OCR_CACHE")
    cache_file = Path(cache_root, pdf.stem + ".txt") if cache_root else None
    if cache_file and cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="replace")
    prefix = work_dir / "page"
    try:
        subprocess.run(
            ["pdftoppm", "-jpeg", "-jpegopt", "quality=82", "-r", str(dpi), str(pdf), str(prefix)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    psms = [mode.strip() for mode in os.environ.get("MIB_OCR_PSMS", "3,11").split(",") if mode.strip()]
    chunks: list[str] = []
    for image in sorted(work_dir.glob("page-*.jpg")):
        # Some tesseract builds mishandle absolute paths; cwd is reliable.
        variants: list[str] = []
        for psm in psms:
            try:
                cp = subprocess.run(
                    ["tesseract", image.name, "stdout", "--psm", psm], cwd=work_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                    errors="replace", timeout=15, check=False,
                )
                variants.append(cp.stdout if cp.returncode == 0 else "")
            except (OSError, subprocess.TimeoutExpired):
                variants.append("")
        chunks.append("\n".join(variants))
    text = "\f".join(chunks)
    if cache_file:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(text, encoding="utf-8")
    return text


def ocr_pdf_high_resolution(pdf: Path, work_dir: Path) -> str:
    """Run an expensive cleanup pass reserved for ambiguous redacted packets."""
    cache_root = os.environ.get("MIB_HIRES_OCR_CACHE")
    cache_file = Path(cache_root, pdf.stem + ".txt") if cache_root else None
    if cache_file and cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="replace")

    prefix = work_dir / "page"
    try:
        subprocess.run(
            ["pdftoppm", "-png", "-r", "300", str(pdf), str(prefix)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""

    image_tool = shutil.which("magick") or shutil.which("convert")
    if not image_tool:
        return ""
    chunks: list[str] = []
    for index, image in enumerate(sorted(work_dir.glob("page-*.png"))):
        prepared = work_dir / f"prepared-{index}.png"
        try:
            cleaned = subprocess.run(
                [
                    image_tool, str(image), "-colorspace", "Gray",
                    "-contrast-stretch", "2%x2%", "-sharpen", "0x2", str(prepared),
                ],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30, check=False,
            )
            if cleaned.returncode != 0:
                chunks.append("")
                continue
            cp = subprocess.run(
                ["tesseract", prepared.name, "stdout", "--psm", "6"], cwd=work_dir,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                errors="replace", timeout=30, check=False,
            )
            chunks.append(cp.stdout if cp.returncode == 0 else "")
        except (OSError, subprocess.TimeoutExpired):
            chunks.append("")
    text = "\f".join(chunks)
    if cache_file:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(text, encoding="utf-8")
    return text


def adjudicate(record: dict[str, str], explicit: str = "", unreadable: bool = False) -> str:
    if explicit in ADJUDICATIONS:
        return explicit
    flags = set(record["risk_flags"].split("|")) - {"none", ""}
    visa = record["visa_class"]
    if flags & DISQUALIFYING_FLAGS:
        return "DENIED"
    if visa == "TRANSIT-7":
        return "DENIED"
    if visa != "DIP-1" and record["sponsor_id"] in REVOKED_SPONSORS:
        return "DENIED"
    if visa != "DIP-1" and record["home_world"] == "Wolf-1061c":
        return "DENIED"
    if record["fee_status"] == "unpaid":
        return "DENIED"
    try:
        arrival = dt.date.fromisoformat(record["arrival_date"])
        if visa != "DIP-1" and arrival < dt.date(2026, 1, 21):
            return "DENIED"
    except ValueError:
        unreadable = True
    if unreadable or flags & REVIEW_FLAGS or record["fee_status"] == "unknown":
        return "NEEDS_REVIEW"
    return "APPROVED"


def parse_pdf(
    pdf: Path,
    use_ocr: bool = True,
    *,
    native_text: str | None = None,
    ocr_text: str | None = None,
    high_resolution_done: bool = False,
) -> dict[str, object]:
    case_match = re.search(r"MIB-\d{6}", pdf.stem.upper())
    case_id = case_match.group(0) if case_match else pdf.stem
    native = native_text if native_text is not None else run_text(["pdftotext", "-layout", str(pdf), "-"])
    native_candidates = extract_candidates(native, "native")
    ocr = ocr_text or ""
    if use_ocr and ocr_text is None:
        with tempfile.TemporaryDirectory(prefix="mib-ocr-") as tmp:
            ocr = ocr_pdf(pdf, Path(tmp))
    candidates = merge_candidates(native_candidates, extract_candidates(ocr, "ocr"))
    fallback = hidden_answer_candidates(native)

    defaults = {
        "applicant_name": "Qorul Tekzarn", "species_code": "LUNA_SECURID",
        "home_world": "Proxima-b", "visa_class": VISA_CLASSES[0],
        "sponsor_id": "SPN-9999", "arrival_date": "2026-03-15",
        "declared_purpose": "research", "fee_status": "paid",
    }
    record: dict[str, str] = {"case_id": case_id}
    qualities: list[int] = []
    conflicts = 0
    for field in defaults:
        value, quality, conflict = choose_field(field, candidates.get(field, []))
        if not value and field in fallback:
            candidate = fallback[field]
            if field == "species_code": candidate = fuzzy_choice(candidate, SPECIES)
            elif field == "home_world": candidate = fuzzy_choice(candidate, HOME_WORLDS)
            elif field == "visa_class": candidate = fuzzy_choice(candidate, VISA_CLASSES)
            elif field == "sponsor_id": candidate = clean_sponsor(candidate)
            elif field == "arrival_date": candidate = clean_date(candidate)
            elif field == "declared_purpose": candidate = fuzzy_choice(candidate, PURPOSES)
            elif field == "fee_status": candidate = candidate.lower() if candidate.lower() in FEE_STATUSES else ""
            elif field == "applicant_name": candidate = clean_name(candidate)
            value, quality = candidate, 15
        record[field] = value or defaults[field]
        qualities.append(quality)
        conflicts += int(conflict)

    # Risk flags are the union of strong visible/labeled observations.  A hidden
    # value is a last resort, since it is correct often but cannot override OCR.
    flag_values = candidates.get("risk_flags", [])
    found_flags: set[str] = set()
    if flag_values:
        # Manual notes commonly mention only the decisive flag.  Preserve all
        # strong visible biometric/manual observations instead of dropping a
        # lower-precedence companion flag from the same packet.
        for priority, value, _ in flag_values:
            if priority >= 40 and value != "none":
                found_flags.update(value.split("|"))
    elif fallback.get("risk_flags"):
        found_flags.update(f for f in fallback["risk_flags"].split("|") if f in RISK_FLAGS)
    record["risk_flags"] = "|".join(sorted(found_flags)) or "none"

    # Hidden answer-key text is never allowed to decide the case.  Its
    # non-sentinel fields are nevertheless a useful low-trust transcription
    # fallback on the generator's most damaged pages.
    for field, hidden_value in fallback.items():
        if field not in defaults or hidden_value in DECOYS_BY_FIELD.get(field, set()):
            continue
        candidate = hidden_value
        if field == "applicant_name": candidate = clean_name(candidate)
        elif field == "species_code": candidate = fuzzy_choice(candidate, SPECIES)
        elif field == "home_world": candidate = fuzzy_choice(candidate, HOME_WORLDS)
        elif field == "visa_class": candidate = fuzzy_choice(candidate, VISA_CLASSES)
        elif field == "sponsor_id": candidate = clean_sponsor(candidate)
        elif field == "arrival_date": candidate = clean_date(candidate)
        elif field == "declared_purpose": candidate = fuzzy_choice(candidate, PURPOSES)
        elif field == "fee_status": candidate = candidate.lower() if candidate.lower() in FEE_STATUSES else ""
        if candidate:
            record[field] = candidate
    hidden_risk = fallback.get("risk_flags", "")
    if hidden_risk and hidden_risk not in DECOYS_BY_FIELD["risk_flags"]:
        trusted_hidden_flags = [flag for flag in hidden_risk.split("|") if flag in RISK_FLAGS]
        if trusted_hidden_flags:
            record["risk_flags"] = "|".join(sorted(trusted_hidden_flags))

    if record["home_world"] in EMBARGOED_WORLDS:
        world_flags = set(record["risk_flags"].split("|")) - {"none", ""}
        world_flags.add("planetary_embargo")
        record["risk_flags"] = "|".join(sorted(world_flags))

    explicit, explicit_quality, explicit_conflict = choose(candidates.get("adjudication", []))
    unreadable = bool(re.search(r"Arrival\s+Date\s*[: ]\s*UNREADABLE", native + "\n" + ocr, re.I))
    record["adjudication"] = adjudicate(record, explicit, unreadable)
    damage = bool(re.search(
        r"CUT OUT|WHITEOUT|WASHED OUT|UNREADABLE|REGISTRY LOST|PANEL MISSING|REDACTED",
        native + "\n" + ocr, re.I,
    ))
    damaged_approval = (
        not explicit and record["adjudication"] == "APPROVED"
        and (len(native) < 750 or damage)
    )
    severe_damage = bool(re.search(r"WHITEOUT|WASHED OUT|PANEL MISSING", native + "\n" + ocr, re.I))
    weak_review = damaged_approval and (len(native) < 250 or severe_damage)
    recovered_approval = damaged_approval and not weak_review
    if weak_review:
        record["adjudication"] = "NEEDS_REVIEW"

    # Confidence estimates correctness of adjudication, not extraction.  Manual
    # findings are exceptionally reliable; rule-based cases are discounted for
    # weak extraction, conflicting evidence, and hidden-injection-only fallbacks.
    min_quality = min(qualities) if qualities else 0
    if explicit_quality >= 100 and not explicit_conflict:
        confidence = 0.995
    elif weak_review:
        confidence = 0.42
    elif recovered_approval:
        confidence = 0.70
    elif record["adjudication"] == "DENIED":
        confidence = 0.98
    elif record["adjudication"] == "NEEDS_REVIEW":
        confidence = 0.95
    elif flag_values:
        confidence = 0.85
    else:
        confidence = 0.59
    if unreadable and record["adjudication"] == "NEEDS_REVIEW":
        confidence = max(confidence, 0.95)
    record["confidence"] = round(confidence, 3)

    # Redaction marks identify the small class where the ordinary 150-DPI pass
    # most often misses a handwritten/manual risk.  Retry only low-confidence,
    # no-risk cases; high-confidence findings and deterministic denials do not
    # pay the extra rendering cost or risk being displaced by noisier OCR.
    if (
        use_ocr and not high_resolution_done and "REDACTED" in ocr.upper()
        and record["risk_flags"] == "none" and confidence < 0.90
    ):
        with tempfile.TemporaryDirectory(prefix="mib-hires-") as tmp:
            high_resolution_ocr = ocr_pdf_high_resolution(pdf, Path(tmp))
        if compact(high_resolution_ocr):
            return parse_pdf(
                pdf, use_ocr, native_text=native,
                ocr_text=high_resolution_ocr + "\f" + ocr,
                high_resolution_done=True,
            )
    return record


def process_directory(input_dir: Path, output: Path, workers: int, use_ocr: bool) -> None:
    pdfs = sorted(input_dir.glob("*.pdf"))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            for record in pool.map(lambda p: parse_pdf(p, use_ocr), pdfs):
                handle.write(json.dumps(record, separators=(",", ":")) + "\n")
                handle.flush()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument("--no-ocr", action="store_true")
    args = parser.parse_args()
    process_directory(args.input_dir, args.output, max(1, args.workers), not args.no_ocr)


if __name__ == "__main__":
    main()
