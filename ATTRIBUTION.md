# Attribution & credits

Ship build **v42 (transfer-first)**. Prior v41 public-train **138.086 / 150**
(CFA=0) overfit layout-consensus + trap cells and ranked **#5** on unofficial
private board #3. v42 studies rivals who beat that peak with lower train scores.

This file lists people, projects, and packages we referenced or reused.
Legal license texts live under `third_party_licenses/`.

## People & public solutions we learned from

| Who | What we took / compared |
|-----|-------------------------|
| **[strobl](https://github.com/strobl/mib-doc-solution)** / @SWFactoryGuy | Primary prior art (vendored MIT render-first stack). Rejected 138 answer-key/allowlist peaks; clean finalizer — private #2 on unofficial #3. |
| **[tylergibbs1](https://github.com/tylergibbs1/mib-doc-challenge-solution)** / @Tylerbryy | Emitted-policy re-pass + OOF/EV discipline — private #1 unofficial #3. We independently added a one-way emitted guardrail. |
| **[zubalr](https://github.com/zubalr/mib-intake)** / @zubair__ | OOF-first reporting (128.5) + payoff EV — private #3. Informed transfer stance, not copied runtime. |
| **[thegoleffect](https://github.com/thegoleffect/mib-doc-challenge-solution)** | Scoped hi-res OCR / strong extraction — private #4. |
| **[Abhishek21g](https://github.com/Abhishek21g)** | Public-train claim **138.62** with disclosed transfer risk; absent from unofficial private top-9 (classic overfit). |
| **[afifi-yusuf](https://github.com/afifi-yusuf/mib-doc-solution)** | Narrow fee-token / receipt ideas visible in the public field. |
| **[jay-tau](https://github.com/jay-tau/mib-doc-solution)** | Public strobl-derived fork; transfer-style baseline in the ~127 band. |
| **Other 8090 entrants** (dw820/@WeiTu_, arvindcr4/@TipsCsharp, rupaut98/@rupakrt, adityanaidu16, …) | Public memos / scores — competitive context only. |

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
