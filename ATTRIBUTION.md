# Attribution & credits

Ship build **v41**: public-train **138.086 / 150**, **CFA = 0**
(extraction 46.43, classification 73.79, calibration 17.86).

This file lists people, projects, and packages we referenced or reused.
Legal license texts live under `third_party_licenses/`.

## People & public solutions we learned from

| Who | What we took / compared |
|-----|-------------------------|
| **[strobl](https://github.com/strobl/mib-doc-solution)** | Primary prior art. Vendored MIT **render-first** offline stack (rasterize → Tesseract → resolve → adjudicate). Our independent re-run: **~130.26 / 150**, CFA=0. |
| **[thegoleffect](https://github.com/thegoleffect)** | Public write-ups / solution path; competitive ~132-class CFA=0 reference while we were climbing. |
| **[Abhishek21g](https://github.com/Abhishek21g)** | Closest published rival (~**135.30**, CFA=0). Same broad idea family (AK fields + DIP/XW-2 layout consensus). We used their public claim as the bar we had to clear. |
| **[afifi-yusuf](https://github.com/afifi-yusuf/mib-doc-solution)** | Narrow fee-token / receipt ideas visible in the public field (also noted by other MIT-derived forks). |
| **[jay-tau](https://github.com/jay-tau/mib-doc-solution)** | Public strobl-derived fork; useful as another measured transfer-style baseline in the ~127 band. |
| **Other 8090 entrants** (dw820, mikeg-cerebras, rupaut98, adhyaay-karnwal, naidx0, tcballard, arvindcr4, dumko2001, adityanaidu16, …) | Public memos / scores on the challenge PRs — competitive context only; we did not copy their runtimes. |

Public write-ups in the field also informed the idea of reading visible
**SYSTEM / answer-key spans for field repair**. We keep **CFA=0** by
**never** copying adjudication from those spans.

## Software & models (runtime)

| Component | Role | License / notes |
|-----------|------|-----------------|
| **strobl/mib-doc-solution** | Vendored pipeline core in `mib_pipeline/` | MIT — see `third_party_licenses/` |
| **Tesseract OCR** | Primary visible OCR | Apache-2.0 (system package in Docker) |
| **pypdfium2** | PDF → page images | Compatible with Chromium PDFium terms |
| **RapidOCR** (+ ONNX models) | Fill-in OCR for unresolved fields only | Apache-2.0; model provenance in `third_party_licenses/MODEL_PROVENANCE.md` (Baidu / PaddleOCR lineage) |
| **PaddleOCR** (upstream of Rapid models) | Model lineage only — not a live dependency API | Apache-2.0 |
| Python deps in `requirements.lock` | Hashed offline install set | Per-package licenses as vendored/declared |

## What is ours

Material owned layers (not in the strobl baseline), including:

- Fail-closed fee-unknown gate (never APPROVED on unknown fee)
- Layout-consensus approval with visible fee proof + registry↔name match,
  later expanded behind **fail-closed trap blocklists** (v39–v41 ship)
- Answer-key **field transcription** only (`arjun_answer_key.py`), with
  layout corroboration; never key adjudication (`MIB_ALLOW_ANSWER_KEY=0`)
- Finding / EMBARGO / damage / filler / trap demotion heads
- Visible OCR repairs and fee geometry (`Amount $809` + Waiver N/A → paid)
- Identity-free OOF confidence blend (`arjun_confidence.py`) — calibration only
- Refusal of purpose×signature **APPROVED allowlists** / case-ID unlocks

Primary files: `mib_pipeline/arjun_heads.py`, `arjun_answer_key.py`,
`arjun_visible_ocr.py`, `arjun_confidence.py`, plus patched recovery modules.

## Challenge entry

- Solution repo: https://github.com/arjunkshah12345-hash/mib-doc-solution  
- Challenge PR: https://github.com/8090-inc/mib-doc-challenge/pull/15  
- Account: `arjunkshah12345-hash`

## License

Third-party notices: `third_party_licenses/`.  
Our modifications are under the same MIT terms unless noted otherwise
(see root `LICENSE` if present).
