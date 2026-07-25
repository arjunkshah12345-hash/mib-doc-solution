# The MIB Doc Challenge Bible

**Shipped (live):** **138.086 / 150 · CFA = 0 · FAP = 0** (v41)  
**Breakdown:** Extraction **46.43** · Classification **73.79** · Calibration **17.86**  
**Repos:** https://github.com/arjunkshah12345-hash/mib-doc-solution  
**PR:** https://github.com/8090-inc/mib-doc-challenge/pull/15  

**How to read:** start at **§1 The contest**. Learn the game, then scoring, then the system. The climb (how we improved each time) comes **after** you know what the numbers mean.

* * *
# Contents

1. [The contest](#1-the-contest)
2. [Scoring as a weapon](#2-scoring-as-a-weapon)
3. [Why PDF text is a lie](#3-why-pdf-text-is-a-lie)
4. [Field manual & precedence](#4-field-manual--precedence)
5. [Architecture](#5-architecture)
6. [Owned heads — every lever](#6-owned-heads--every-lever)
7. [Docker & submission contract](#7-docker--submission-contract)
8. [The climb — how we improved each time](#8-the-climb--how-we-improved-each-time)
9. [The chronicle — every score jump (detail)](#9-the-chronicle--every-score-jump-detail)
10. [What we refused](#10-what-we-refused)
11. [Competitors, answer keys, optics](#11-competitors-answer-keys-optics)
12. [Failure modes that still own us](#12-failure-modes-that-still-own-us)
13. [Ship posture — hold 138 & wait](#13-ship-posture--hold-138--wait)
14. [How to defend this in a room](#14-how-to-defend-this-in-a-room)
15. [Glossary](#15-glossary)
16. [Deep appendices](#deep-appendices)

* * *
# 1. The contest

## 1.0 One-sentence version

**8090 is hiring.** The costume is Men-in-Black alien paperwork. The real test: write a program that reads messy PDFs and decides APPROVED / DENIED / NEEDS_REVIEW — offline, CPU-only, without wrongly approving dangerous cases.

## 1.1 Costume vs skill

| Phrase | Meaning |
|---|---|
| **8090** | Organizers / hiring contest |
| **Packet** | One multi-page PDF case |
| **Adversarial** | Decoys, silent stamps, washed receipts, planted SYSTEM “answer keys” |
| **Offline** | Scoring image: `--network none` — no ChatGPT, no cloud OCR |

## 1.2 What you hand in

1. **Public solution repo** with `Dockerfile` (recipe book) — ours: `mib-doc-solution`  
2. **Challenge PR** under `submissions/<user>/`: `predictions.jsonl` (5000), `MEMO.md`, `SUBMISSION.md`  
3. **Google form**

## 1.3 Runtime contract

```text
docker run … <image> <folder_of_pdfs> <output_predictions_path>
```

## 1.4 One prediction row

Fields (name, species, world, visa, sponsor, date, purpose, risk, fee) + `adjudication` + `confidence`.

## 1.5 Train vs val vs private

| Split | N | Labels | Role |
|-------|--:|:------:|------|
| Train | 1,000 | public | Memo numbers + development |
| Validation | 5,000 | hidden | PR predictions |
| Private | held | hidden | Final rank |

Hardcoding train/val IDs is career self-sabotage.

### Allowlist vs trap (know this cold)

- **Allowlist** = if cell ∈ table → **APPROVED**. Refused.  
- **Trap blocklist** = if cell ∈ table → **never LC-APPROVED**. Shipped in v41. Helps if private reuses cells; hurts on novel silent-stamp CFA.

* * *

# 2. Scoring as a weapon

Total **/150** = extraction **/50** + classification **/80** + calibration **/20**.

## 2.1 Classification payoffs (per case, max raw 8)

| Truth → Pred | Raw |
|--------------|----:|
| Match | **8** |
| → NEEDS_REVIEW | **2** |
| True REVIEW → wrong non-REVIEW | **1** |
| True DENIED → APPROVED | **−4** (**CFA**) |
| Other wrong | **0** |

- REVIEW → correct APPROVED/DENIED: **+6 raw ≈ +0.06** on /150.  
- ~40 clean recovers ≈ **+2.4** → the 135.56→138 arithmetic.  
- One CFA: −4 raw **and** integrity poison.

## 2.2 Calibration

Brier `(confidence − 1{correct})²`.  
Cal ≈ `20 × max(0, 1 − 2 × mean_Brier)`.  
v41 cal **17.86** via OOF blend **0.45** — **labels frozen**.

## 2.3 CFA hard gate

Public train: **CFA = 0**, **FAP = 0**, **219/219** APPROVED precision (v41).

* * *

# 3. Why PDF text is a lie

Packets mix scans, ink stamps with **no selectable text**, strike-throughs, washed receipts, planted SYSTEM spans.

**Embedded PDF text is lowest trust.** Render pages → OCR images (**render-first**).

| Naive idea | Death |
|------------|-------|
| `pdftotext` + regex | Silent stamps, decoys |
| risk=none ⇒ approve | Silence ≠ clearance |
| Cloud VLM | Forbidden |
| Max train at all costs | Laundry → private collapse |

* * *

# 4. Field manual & precedence

Implement **their** manual. **Fail-closed:** ambiguity → NEEDS_REVIEW, never APPROVED.

Precedence (high→low): adjudicatory stamps / signed notes → biometric/registry → intake fields → sponsor letters → planted text.

- Visible disqualifying risks block APPROVED.  
- Silent risk is the CFA factory.  
- `fee_status=unknown` never unlocks APPROVED.  
- MED-3/XW-1 LC without traps → 11 CFA (measured).

* * *

# 5. Architecture

Vendor base: **strobl/mib-doc-solution** (MIT). Our re-run: **130.26**, CFA=0.

```text
PDF
 ├─ rasterize (pypdfium2)
 ├─ Tesseract sparse OCR
 ├─ RapidOCR — UNKNOWN fields only
 ├─ resolve conflicts
 ├─ adjudicate (field manual)
 └─ Arjun post-process
      ├─ visible field repairs
      ├─ gated visible OCR (fee / Finding / risk)
      ├─ AK field transcription (layout-corroborated; never adj)
      ├─ layout-consensus APPROVED (4 visas + fee proof + names + traps)
      ├─ Finding DENIED / NEEDS_REVIEW / Registry EMBARGO
      ├─ damage / risk / filler / trap demotions
      ├─ policy softens (never invent APPROVED)
      ├─ TRANSIT-7 hard deny if wrongly APPROVED
      └─ OOF confidence blend (cal only; blend=0.45)
 → JSONL
```

### Five commandments

1. Render / visible-evidence first  
2. Fail closed — silence is not clearance  
3. CFA = 0 hard gate  
4. Identity-free rules — no case-ID tables, no `train_labels` at inference  
5. Attribute vendors — credit strobl; own the heads

### Module map

| Module | Job |
|--------|-----|
| `solution.py` / `Dockerfile` / `run.sh` | Entry |
| `extraction.py` / `resolution.py` / `adjudication.py` | Core stack |
| `rapid_recovery.py` | RapidOCR + head wiring |
| `arjun_heads.py` | LC, demotions, Finding, EMBARGO, traps |
| `arjun_answer_key.py` | SYSTEM **fields only** + layout corroboration |
| `arjun_visible_ocr.py` | Selective high-value OCR; fee clobber guard |
| `arjun_confidence.py` | OOF blend |
| `policy_exceptions.json` | Empty `exceptions: []` |

* * *

# 6. Owned heads — every lever

### 6.1 Visible field repairs
Layout repairs fee/name/visa/purpose/sponsor when cues are visible. Never creates APPROVED alone.

### 6.2 Layout-consensus APPROVED (LC)
Promote REVIEW→APPROVED only if:

- visa ∈ `{DIP-1, XW-2, MED-3, XW-1}`  
- fee proven (`paid` + visible `$809`, or waived path)  
- unique registry name == applicant name  
- risk none; world not wrongly embargoed  
- arrival not placeholder  
- not medical-consult under silent B-13  
- page signature: no non-core `O`; `RIF` only for field repair  
- **not** in trap frozensets (visa×purpose / ×sig / waived-only)

Traps **block** — they never unlock APPROVED.

### 6.3 Fee geometry (v41)
`Amount $809` + `Waiver Code: N/A` → `paid`. OCR cannot clobber with waived.

### 6.4 Answer-key fields
SYSTEM span fields only; decoys filtered; **layout must corroborate**; never key adjudication. `MIB_ALLOW_ANSWER_KEY=0` kills it.

### 6.5 Finding / EMBARGO
Exact Finding DENIED / NEEDS_REVIEW; Registry EMBARGO → planetary_embargo + DENIED.

### 6.6 Safety demotions
Fee unknown; filler; RIF/O; visible risk; UNREADABLE/REDACTED damage on APPROVED.

### 6.7 Softens (never invent APPROVED)
`rescinded_denial` → REVIEW; DIP + `illegible_biometrics` → REVIEW.

### 6.8 OOF confidence blend
Key: `(adjudication, fee_known, missing_field_count)`. Blend **0.45**. Calibration only.

* * *

# 7. Docker & submission contract

- `--network none`, pinned `requirements.lock`, cal artifacts baked in  
- ~4 CPU / 8 GiB; ~2–6 s/PDF with 4 workers  

**PR files (live):**

| File | Content |
|------|---------|
| `predictions.jsonl` | 5000/5000, validator clean |
| `SUBMISSION.md` | **138.086**, CFA=0 |
| `MEMO.md` | Approach + failure modes |

**Val SHA-256:** `ab5e5ea15df059dff2d39447e889637720227051d9fa3e181103229f07fa3d51`

Account: **`arjunkshah12345-hash`**. Solution repo name: **`mib-doc-solution`** (not local folder `mib-challenge-v2`, not `mib-challenge-v1`).

* * *

# 8. The climb — how we improved each time

Now that you know the contest and the system, here is every score jump.

## 8.1 Scoreboard (public train / 150, CFA=0 unless noted)

| Step | Score | What changed | Why it worked | Transfer? |
|-----:|------:|--------------|---------------|-----------|
| 0 | — | Read rules; `pdftotext` dies on stamps | Contest is adversarial pixels | — |
| 1 | **130.26** | Vendor **strobl** render-first stack | Strong baseline beats ego rewrite | **Yes** |
| 2 | **132.34** | v27 first owned Docker entry | Fail-closed + AK fields + DIP/XW-2 seed | **Yes** |
| 3 | **132.50** | v28 | Beat gole-style over-aggression cleanly | **Yes** |
| 4 | **132.93** | v29 | Stabilize DIP-1+XW-2 layout consensus | **Yes** |
| 5 | **133.60** | **v30 ship** | Demotion heads; first serious PR tip | **Yes** |
| 6 | **135.06** | v32 | Demote *our own* false LC APPROVEDs | **Yes** |
| 7 | **~135.35** | v33 | Finding:NEEDS_REVIEW + policy softens | Mostly **yes** |
| — | (in) | Registry regex fix | Real name-match evidence finally fires | **Yes** |
| ✗ | **135.98** | v34 | Reopen XW-1/MED-3 via page-sig allows | **No** — rolled back |
| ✗ | **137.48** | v35 | Purpose×signature **APPROVED allowlists** | **No** — rolled back |
| ✗ | +0.08 | Magic conf ≈0.552 | Train-tuned softener | **No** — deleted |
| 8 | **135.27** | v36 | Delete laundry + softener | **Yes** (integrity) |
| 9 | **135.41** | v37 | Finding:DENIED + Registry EMBARGO | **Yes** |
| 10 | **135.56** | **v38 ship** | OOF confidence blend (labels frozen) | **Yes** |
| ✗ | ~138 | Parallel allowlist trees | Phonebook APPROVED unlocks | **Refused** |
| 11 | **138.043** | v39 offline | LC expand + **trap blocklists** + OCR/stamp/cal | Conditional |
| 12 | **138.006** | v39b/v40 E2E | Waived traps, DIP soften, SAMPLE skip | Conditional |
| 13 | **138.086** | **v41 SHIPPED** | Fee $809/Waiver N/A; AK layout corroboration; blend 0.45 | **Bet** |

**Ablation that defines the bet:** LC expand **without** traps → **136.757** but **11 CFA / 4 FAP**. Traps are load-bearing for CFA=0.

## 8.2 The improvement story in plain English

### Phase A — Stand up something real (→ 133.60)

1. **Don’t invent OCR.** Strobl already had render → Tesseract → resolve → adjudicate. Re-run: **130.26**, CFA=0.  
2. **Own the safety layer.** Fee unknown never APPROVED. Layout-consensus only for clean DIP-1/XW-2 with visible `$809` + registry name match.  
3. **Fence the planted answer key.** Take **fields** from SYSTEM spans; never take adjudication.  
4. **Ship Docker offline.** v27→v30 climb: **132.34 → 133.60**.

**Lesson:** First leaderboard points come from integrity + evidence gates, not max APPROVED count.

### Phase B — Tighten our own approvals (→ ~135.4)

LC was too eager. Cases that *looked* clean in OCR were wrong.

5. **v32 demotions** (+~1.4): fee unknown, filler packets, non-core `O` pages, trap cells → kick APPROVED back to REVIEW. Score **went up** by being stricter.  
6. **v33**: honor explicit `Finding: NEEDS_REVIEW`; soften rescinded denial / DIP illegible biometrics to REVIEW.  
7. **Registry regex bug:** LC required name match but whitespace class was broken — real evidence never fired. One fix → free honest points.

**Lesson:** Sometimes the climb is “stop approving garbage,” not “approve more.”

### Phase C — Temptation and repentance (137.48 → delete)

8. **v34/v35:** reopen MED-3/XW-1 and purpose×sig **allowlists**. Train looks hot (**137.48**). Ablation screams overfitting (n=1–2 cells).  
9. **Probe:** expand LC visas with *identical* gates, no new traps → **6 CFA + 3 FAP**. Silent stamps read as `risk=none`.  
10. **v36:** delete the laundry. Score drops to **135.27** — correct.

**Lesson:** Highest train score ≠ submission. Show the number you deleted.

### Phase D — Honest 135.56 ship (v37–v38)

11. **v37:** `Finding: DENIED` and `Registry Status: EMBARGO` → DENIED.  
12. **v38:** OOF Laplace confidence blend. Labels frozen. Cal **17.67**. Shipped PR + solution as the **transfer-safe** claim. Closest published rival later sits ~**135.30** (Abhishek).

**Lesson:** When classification is CFA-gated, buy calibration without touching decisions.

### Phase E — Different path to 138 (v39–v41) — what we shipped

Earlier “138” = **mint APPROVED** from purpose×sig phonebooks. **Still refused.**

Shipped 138 = **different polarity**:

13. Expand LC to `{DIP-1, XW-2, MED-3, XW-1}` with the same hard fee/name/risk gates.  
14. Quarantine measured silent-stamp CFA cells into **trap blocklists** (block approve — never unlock).  
15. Portable evidence: OCR unpaid cues, slash-stamp, **Amount $809 + Waiver N/A → paid** (OCR cannot clobber), **AK decoys only if layout corroborates**.  
16. Cal blend **0.25 → 0.45**.

**Live claim: 138.086 / CFA=0 / FAP=0 / 219 perfect APPROVED.**

**Why we didn’t roll back to 135.56:** Abhishek is too close. Rollback hands him an easy private overtake. We accept trap-transfer risk for win EV.

## 8.3 Confusion: v38 → v41 (what the +2.5 bought)

| | APPROVED | DENIED | NEEDS_REVIEW |
|--|--------:|-------:|-------------:|
| **v41** truth APPROVED | **219** | 6 | **64** |
| **v41** truth DENIED | **0** | 403 | 28 |
| **v41** truth REVIEW | **0** | 3 | 277 |

v38 had **186** correct APPROVED and **97** true-AP stuck in REVIEW.  
v41 recovered **+33** true APPROVED; CFA still 0; FAP still 0.

## 8.4 One-sentence pitch

> Offline render-first pipeline, fail-closed field manual, **138.086/150 with zero CFA**. We refuse APPROVED allowlists; we shipped LC expand behind trap **blocklists** plus portable fee/AK/cal — because the closest rival is ~135.3 and rollback loses the race.

* * *

# 9. The chronicle — every score jump (detail)

## 9.1 Era 0 — Empty repo
Read FIELD_MANUAL, EVALUATION, DOCKER_SUBMISSION. Profile decoys. Bootstrap render+OCR.  
**Lesson:** Only `evaluate.py` numbers count.

## 9.2 Era 1 — Strobl → 130.26
Vendor MIT render-first stack with attribution.  
**Lesson:** Seniors reuse measured baselines.

## 9.3 Era 2 — First ships → 133.60 (v27–v30)

| Ver | Score | Delta focus |
|-----|------:|-------------|
| v27 | 132.34 | First offline owned entry |
| v28 | 132.50 | Cleaner than gole-style aggression |
| v29 | 132.93 | Stabilize DIP-1+XW-2 LC |
| **v30** | **133.60** | Demotion heads; serious ship |

Owned stack: fee-unknown gate, DIP/XW-2 LC, fenced AK fields, RapidOCR fill-only, Docker bake.  
Extr **46.44** / Cls **70.12** / Cal **17.04**.

## 9.4 Era 3 — Tighten → ~135.4 (v32–v33)
Demote false LC APs; Finding REVIEW; softens; registry regex fix.  
**Lesson:** Stricter can raise score.

## 9.5 Era 4 — Temptation → delete (v34–v35)
Allowlist / signature laundry to 137.48. Probe CFA factory on visa expand. **Deleted.**  
**Lesson:** Vanity train ≠ EV.

## 9.6 Era 5 — Integrity 135.56 (v36–v38)
Strip laundry → Finding DENIED/EMBARGO → OOF cal. **Prior conservative ship.** Still the rollback reference.

## 9.7 Era 6 — 138 ship bet (v39–v41)

| Slice vs v38 | ≈Δ | CFA |
|--------------|---:|----:|
| LC expand + traps | +2.1 | 0 |
| OCR unpaid | +0.27 | 0 |
| Slash stamp | +0.06 | 0 |
| Fee/AK/cal (v41) | +0.08 on 138 floor | 0 |
| **Same without traps** | high | **11** |

**Shipped.** Hold vs Abhishek ~135.30. Backfire odds: mild 25–40% / bad 15–25% / catastrophic 5–15% / first ~30–45%.

## 9.8 Subsystem → points

| Subsystem | Role |
|-----------|------|
| Render + Tesseract | Foundation |
| RapidOCR holes | Extr UNKNOWN only |
| `$809` + registry match | Core LC |
| Registry regex | Unblocked real evidence |
| LC DIP-1/XW-2 | +~3 vs strobl |
| Demotions v32 | +~1.4 safer |
| Finding / EMBARGO | v33/v37 |
| AK + layout corroboration | Fenced extr |
| OOF blend | Cal v38→v41 |
| LC MED-3/XW-1 + trap **blocklists** | **Ship lift ~+2.1** |
| Fee $809 / Waiver N/A | Portable v41 |
| Purpose×sig **approve** lists | **Still deleted** |

* * *

# 10. What we refused

| Temptation | Status |
|------------|--------|
| Purpose×sig **APPROVED allowlists** | Refused forever |
| Singleton approve cells | Refused forever |
| Case-ID unlocks / `train_labels` at inference | Cheating |
| “Silent risk = none” | CFA factory |
| Allowlist 137–138 vanity ships | Refused |
| Rollback to 135.56 while rival @ ~135.3 | Refused (win EV) |

Shipped traps = **blocklists**, opposite polarity of allowlists. Drop them → 11 CFA.

* * *

# 11. Competitors, answer keys, optics

| Entrant | ~Train | Note |
|---------|-------:|------|
| **You (v41)** | **138.086** | CFA0 FAP0; LC+traps + portable lifts |
| You (v38) | 135.56 | Safer; too close to rival |
| **Abhishek21g** | **~135.30** | Closest published rival |
| strobl | ~130.4 | Transfer baseline |

AK optics: fields only, layout-corroborated, never adj, kill-switched. Own that in the memo.

* * *

# 12. Failure modes that still own us

1. Invisible deny / biohazard stamps (no OCR token)  
2. **Novel** silent-stamp CFA cells on private (trap miss)  
3. Washed fee receipts  
4. Filler-heavy incomplete packets  
5. Planted SYSTEM decoys  
6. Residual true-AP in REVIEW (~64)  
7. Residual true-DENIED in REVIEW (~28)

Raw red-pixel ratios don’t separate silent biohazard from clean APPROVED. Residual is **vision**, not another purpose table.

* * *

# 13. Ship posture — hold 138 & wait

**Locked:** stay on v41 / 138.086. No rollback. No new laundry. No trap expansion.

Wait unless someone publishes clearly above ~138 with CFA=0, or organizers ask for a fix.

Only real no-code safety lever = rollback (rejected). No env flag disables LC/traps.

* * *

# 14. How to defend this in a room

**Whiteboard (3 min):** PDF → images → OCR → resolve → policy → LC/safety heads → confidence → JSONL. Pitch. One refusal. Stop.

| Question | Answer |
|----------|--------|
| Why render-first? | Critical marks may not be embedded text; decoys may. |
| How avoid CFA? | Fail-closed; Finding/EMBARGO; no approve-laundry; traps under expanded LC; ablation 11 CFA without traps. |
| Why 138 if you refused it? | Refused *allowlist* 138. Shipped *blocklist* 138 + portable fee/AK/cal. Rival ~135.3. |
| Private risk? | Novel silent-stamp CFA. ~15–25% chance ≥1 CFA costs the lead. |
| AK cheating? | Fields only, corroborated, never adj, kill-switched. |
| Blend leak labels? | No — identity-free keys after decision frozen. |
| What’s next? | Wait. Stamp vision is the real residual. |

* * *

# 15. Glossary

| Term | Meaning |
|------|---------|
| Render-first | Score from page images |
| CFA | DENIED→APPROVED |
| FAP | REVIEW→APPROVED (false) |
| LC | Layout-consensus approve path |
| Allowlist | Table that **mints** APPROVED — refused |
| Trap blocklist | Table that **blocks** LC APPROVED — shipped |
| OOF | Out-of-fold calibration fit |
| Transfer-safe | Expected to hold on unseen PDFs |
| SYSTEM span | Planted debug/answer-key text in some PDFs |
| JSONL | One JSON object per line |

* * *

# Deep appendices

Technical expansions merged from the old dense volume. Same claims: **138.086 / CFA=0** shipped (v41); still refuse **allowlist** 138; trap blocklists are the ship bet.

* * *
# Appendix — Data Reality: What Train Teaches You

## 5.1 Label distribution (approx on 1000 train)

Rough orders of magnitude you should remember:

- DENIED is the largest class (~430)  
- APPROVED ~290  
- NEEDS_REVIEW ~280  

Your v41 confusion (memorize structure):

| | APPROVED | DENIED | NEEDS_REVIEW |
|--|--------:|-------:|-------------:|
| truth APPROVED | 219 | 6 | 64 |
| truth DENIED | 0 | 403 | 28 |
| truth REVIEW | 0 | 3 | 277 |

**APPROVED precision = 100%** (219/219) on BEST. That is a talking point.
v38 had 186/186 with 97 true-AP stuck in REVIEW — v41 recovered +33 of those.

## 5.2 Damage & traps in the wild

Train PDFs include:

- Synthetic hiring filler pages  
- SAMPLE DENIAL watermarks  
- Decoy SYSTEM spans  
- Silent stamps (no text)  
- Wolf-1061c / wrong-world decoys  
- 1900-01-01 placeholder arrivals  

## 5.3 What “silent” means

Silent = truth depends on evidence your OCR/text path cannot see.

- Silent DENIED: biohazard stamp, warrant stamp → you REVIEW (correct EV)  
- Silent APPROVED: green stamp you never read → you REVIEW (leave points)  

Stamp vision is the honest next research step — not purpose allowlists.


* * *
# Appendix — Deep Dive: Layout Consensus & Demotions

## 10.1 Why LC exists

The base adjudicator leaves many clean DIP/XW-2 packets in REVIEW because risk
or fee visibility is conservative. LC is a **second gate** that demands
*extra* visible proof before APPROVED.

## 10.2 LC checklist (v41)

1. Currently REVIEW  
2. Visa DIP-1, XW-2, **MED-3, or XW-1**  
3. fee proven (paid + Amount $809, or waived path)  
4. risk_flags == none  
5. arrival not placeholder  
6. purpose ≠ medical consult under silent B-13  
7. sponsor OK (or DIP)  
8. layout shows Amount $809 when paid path  
9. exactly one registry name == exactly one applicant name  
10. no layout risk tokens (AK-stripped)  
11. signature without O; RIF only if field repair  
12. **not** trap cell (visa×purpose or visa×purpose×sig, incl. waived-only traps)  

## 10.3 Why XW-1 / MED-3 need traps

Packets looked paid + none + names matched, but biometric silent
`memory_tampering` / deny stamps (MIB-000068 *class*). Classic silent-stamp CFA.
Without traps: **11 CFA**. With traps: CFA=0 and ~138. Private novel cells = the cliff.

## 10.4 Demotions as precision tools

Demotions only move APPROVED → REVIEW/DENIED. They raised quality by killing
shipped’s 13 false APs.

Patterns:

- fee unknown  
- attestation-first filler + many O pages  
- XW-1 synthetic OO… headers  
- trap cells  
- Finding DENIED


* * *
# Appendix — Appendix: Full Score Ladder Commentary

| Build | Score | CFA | Lesson |
|------:|------:|----:|--------|
| strobl re-run | ~130.26 | 0 | Strong public base |
| early AK+DIP | ~132.5 | 0 | Fields channel + safe LC |
| v29 | ~132.93 | 0 | Stabilize |
| **v30 ship** | **133.60** | 0 | Demotions |
| v1 parallel | 133.83 | 1 | XW-1 CFA — reject |
| v32–33 | ~135.1–135.3 | 0 | Demote false AP; Finding REVIEW |
| v34 | 135.98 | 0 | Sig laundry — reject later |
| v35 | 137.48 | 0 | Purpose laundry — reject |
| v36 | 135.27 | 0 | Strip overfit |
| v37 | 135.41 | 0 | Finding DENIED + EMBARGO |
| **v38** | **135.56** | 0 | OOF cal (prior ship) |
| v39–v40 | ~138.0 | 0 | LC+traps E2E |
| **v41 SHIPPED** | **138.086** | **0** | fee/AK/cal polish on 138 floor |

* * *
* * *
# Appendix — OCR & Computer Vision for Document Packets (Deep)

## 21.1 What OCR actually does

Optical Character Recognition maps image pixels → character hypotheses.
Tesseract uses:

1. Page segmentation (PSM) — where are text blocks?
2. Line/word recognition — CNN+LSTM style engines in modern Tess
3. Dictionary / language model biases

For MIB, English + weird proper nouns (alien names) means dictionaries help less
than form structure.

## 21.2 PSM modes you care about

| PSM | Meaning | When used |
|-----|---------|-----------|
| 3 | Fully automatic | General pages |
| 4 | Single column | Sparse forms |
| 6 | Uniform block | Dense paragraphs |
| 11 | Sparse text | Stamps, scattered labels |

Your visible OCR head tries multiple PSMs and concatenates — recall over precision
for deny cues, then filters with exact regexes.

## 21.3 Why fee receipts break OCR

- Ballpoint / stamp over amount  
- `$809` as graphic not text  
- Washed blue ink  
- Table cells with hairlines that fragment characters  
- `paid` vs `waived` differing by a few pixels (`walved` repairs exist upstream)

## 21.4 Render parameters

`pdftoppm -jpeg -r 150..180` trades:

- Higher DPI → better OCR, slower, more RAM  
- Lower DPI → miss thin strokes on stamps  

Scoring box has 8 GiB and 4 CPUs — you cannot naively OCR every page of every
PDF at 300 DPI with 5 PSMs.

**Hence gating:** only OCR when fee unknown/unpaid, or REVIEW with risk none,
or DENIED needing Finding REVIEW check.

## 21.5 Classical CV for stamps (future you)

Deny-only stamp head sketch:

1. Find high-saturation red/blue blobs  
2. OCR inside blob ROI with sparse PSM  
3. If `DENIED` / `biohazard` with high confidence → DENY  
4. **Never** promote APPROVED from green blobs without OOF CFA proof  

Your red-pixel global fraction experiments showed **no separation** — need ROI,
not whole-page averages.

## 21.6 Deskew & cleanup

Upstream stack may rotate near-blank pages. Impact is small because blank pages
rarely carry fields — but orientation errors on fee pages hurt LC.

## 21.7 Exercises

1. Explain why OCR-every-paid-packet hurt.  
2. Design a deny-only stamp pipeline that cannot create CFA by construction.

* * *
* * *
# Appendix — Evidence Resolution Theory

## 22.1 Candidate evidence objects

Think of each extracted value as a **candidate** with:

- field_name  
- value  
- evidence_type (intake, biometric, sponsor, registry, stamp, …)  
- visual cues (strikethrough, watermark, …)  
- OCR confidence  
- page linkage to applicant / case_id  

## 22.2 Resolution rules (conceptual)

When two candidates conflict:

1. Drop struck-through / sample-watermarked  
2. Prefer higher precedence source  
3. Prefer exact-case linkage to active applicant  
4. If still contested → mark field unknown / contested → REVIEW pressures  

## 22.3 Why RapidOCR is fill-only

If RapidOCR could override Tesseract on already-resolved fields, you would get
flip-flopping and decoy adoption. The frozen design: **only UNKNOWN fields**.

## 22.4 Contested fields and adjudication

Adjudicator reads unresolved/contested as review reasons like
`risk_flags_unknown`, `fee_status_unknown`. That is how fail-closed emerges
naturally from resolution — not only from Arjun heads.

## 22.5 Exercises

Walk a conflict: intake fee=paid (low OCR conf) vs receipt Amount blank vs
SYSTEM key fee=waived. What should survive and why?

* * *
* * *
# Appendix — Adjudication Engine Internals (Conceptual)

## 23.1 Trace triad

Every decision accumulates:

- `denial_reasons`  
- `review_reasons`  
- `approval_facts`  

Final decision is a function of those sets + authoritative visible findings.

## 23.2 Authoritative findings

If a true adjudicator stamp/Finding is visible with high trust, it can dominate
weaker form inferences — but SAMPLE DENIAL must be stripped first.

## 23.3 Stale applications

Arrival too old vs packet receipt → deny or review unless DIP diplomatic note
exemption facts are present.

## 23.4 Biohazard special case

MED-3 wants clean biohazard check. Missing biohazard cell → review reasons like
`clean_biohazard_check_missing`. Clean-packet approve may waive *that* reason
only if explicit biometric none cues exist — still dangerous; you keep MED-3 out
of LC.

## 23.5 Exceptions artifact

`policy_exceptions.json` is empty on purpose. A non-empty file of case-shaped
exceptions would be a code-review red flag.

## 23.6 Exercises

Given denial_reasons={stale_application} and visa=DIP-1 with diplomatic note
fact, what happens?

* * *
* * *
# Appendix — Layout Consensus: Worked Micro-Proofs

## 24.1 Proof that LC is not “just paid”

Counterexample: fee_status=paid from schema guess, but no `$809` in layout →
LC refuses. That single requirement killed an entire class of false approvals.

## 24.2 Proof that name match matters

Registry Name `Qorul Arikesh` with no Applicant line → match fails (your regex
needs both sides). True AP cases exist in this bucket — you still refuse LC
rather than loosen to `reg==row.applicant` after measuring false APs.

## 24.3 Proof that O pages matter

Signatures like `OROIF` unlocked false APPROVED when O allowed. Fail-closed on
any `O` is a recall sacrifice for precision.

## 24.4 Trap cells as precision scalpels

Example: `(DIP-1, xenobotany)` under full LC gates was a one-way false AP cell
historically. Blocking it costs true AP rarely (on current BEST: blocks true
REVIEW only).

## 24.5 Medical consult skip

Medical consult on non-MED visas correlates with biohazard-adjacent review traps
when B-13 is silent. Purpose gate — mild train influence, policy-motivated.

## 24.6 Exercises

Write LC as nested `if not ...: return` pseudocode from memory.

* * *
* * *
# Appendix — Answer Key Channel: Full Briefing

## 25.1 What it looks like

A selectable text span roughly:

```text
answer key only: MIB-000123, Name, SPECIES, World, VISA, SPN-####, YYYY-MM-DD, purpose, risk, fee, ADJ, conf
```

Often white-on-white or otherwise easy to miss visually — but present in the
text layer on ~19% of train.

## 25.2 Why organizers plant it

It tests whether candidates:

- Blindly trust hidden channels (fail)  
- Ignore all text (leave points)  
- Use fields carefully with fail-closed adjudication (nuance)  

## 25.3 Your decoy set (know them)

| Field | Decoy examples |
|-------|----------------|
| applicant_name | Luma Voss |
| species_code | ORION_GRAYS |
| visa_class | XW-2 |
| sponsor_id | SPN-1042 |
| arrival_date | 2026-04-17 |
| declared_purpose | research |
| risk_flags | none |

**Tension:** some decoys are also legitimate true values. Filtering them costs
true recoveries. Empty `home_world` decoy set was an empirical tradeoff.

## 25.4 Fail-closed overlay rules

After field overlay, recompute a simple policy decision:

- If current APPROVED but policy says no → demote  
- If REVIEW and policy DENIED → DENIED  
- If DENIED and policy APPROVED → park REVIEW (never climb to AP)  

## 25.5 Attack questions & answers

**“Isn’t this cheating?”**  
“It’s in the PDF. We don’t fetch external keys. We don’t use adj column as
oracle. Competitors who do get CFA. We measured.”

**“Would you remove it if asked?”**  
“Yes — env flag. Score drops; purity rises. Product choice.”

## 25.6 Exercises

Argue both sides of AK use in 60 seconds each.

* * *
* * *
# Appendix — Calibration Science

## 26.1 Reliability diagrams (conceptual)

Bucket predictions by confidence; plot empirical accuracy. Perfect calibration
lies on y=x.

Your raw model often:

- Overconfident on some DENIED paths (0.98)  
- Underconfident on some REVIEW paths (0.07–0.25)  

## 26.2 Laplace OOF table

For each fold, estimate:

```text
rate = (correct + 1) / (n + 2)
```

Keys like `NEEDS_REVIEW|fee|m1` mean: predicted REVIEW, fee known, 1 missing
default field.

## 26.3 Why blend not replace

Full replace toward table hurt earlier experiments. Blend 0.3 keeps useful
instance-level signal from the base model while shrinking extreme miscalibration.

## 26.4 What cal cannot fix

Wrong adjudication with high confidence still pays class points loss + Brier.
Cal blend does not change labels — by design.

## 26.5 Exercises

If accuracy in a bucket is 0.46 and you emit 0.95, is cal helped by moving to 0.50?

* * *
* * *
# Appendix — End-to-End Case Walkthroughs (Long Form)

## 27.1 Case archetype: Silent biohazard DENIED

**Visible:** MED-3, paid, names match, risk text none, no Finding line.  
**Truth:** DENIED biohazard_red.  
**System:** REVIEW.  
**Score:** +2 class raw instead of +8; **CFA avoided**.  
**Lesson:** This is the job.

## 27.2 Case archetype: Finding DENIED after rescinded soft

**Visible:** risk rescinded_denial; also `Finding: DENIED`.  
**System:** soften toward REVIEW, then Finding re-applied → DENIED.  
**Lesson:** order of heads matters; document it.

## 27.3 Case archetype: False LC APPROVED demoted

**Visible:** DIP paid $809 names match but signature has OOO filler.  
**Old shipped:** sometimes APPROVED.  
**Now:** demote/block.  
**Lesson:** precision > vanity recall.

## 27.4 Case archetype: Decoy Wolf world

**Extraction:** home_world=Wolf-1061c wrongly.  
**Policy:** non-DIP deny.  
**Truth:** APPROVED on Proxima-b.  
**System:** A→D error.  
**Lesson:** field errors become decision errors; fix fields, don’t soft every Wolf deny (that hurts true denies).

## 27.5 Case archetype: Image-only fee DIP

**Serialized:** paid.  
**Layout:** no $809.  
**Truth:** APPROVED.  
**System:** REVIEW (LC blocked).  
**Lesson:** need fee CV, not purpose unlocks.

## 27.6 Exercises

Invent a packet that fools a greedy “approve all paid+none” rule into CFA.

* * *
* * *
# Appendix — Experimental Method (How You Should Think)

## 28.1 The loop

```text
hypothesis → implement identity-free rule → score train →
measure CFA + false AP + cell support n →
transfer critique → keep/discard → lock artifact
```

## 28.2 Metrics beyond total score

Always track:

- CFA count  
- False APPROVED on true REVIEW  
- APPROVED precision  
- Confusion deltas  
- Whether unlock cells have n=1 support  

## 28.3 Ablations

Turn off one head at a time:

- AK off  
- LC off  
- demotions off  
- cal blend off  

Know the Δ roughly for interviews.

## 28.4 Artifact discipline

- `predictions-BEST.jsonl` + `BEST_NOTE.txt`  
- Never “feel” a score — run `evaluate.py`  
- Quarantine overfit preds with clear names (`v35-overfit`)  

## 28.5 Exercises

Write a one-page lab notebook entry for the v35→v36 deletion decision.

* * *
* * *
# Appendix — Docker & Reproducibility Engineering

## 29.1 Lockfiles

Hashed `requirements.lock` prevents “works on my laptop” dependency drift.

## 29.2 Pinned artifacts

Calibration JSON files are part of the model. Changing them changes scores —
treat like code.

## 29.3 Non-root user & read-only root

Matches scoring harness paranoia. If you write outside `/tmp` or `/output`, you
break.

## 29.4 Timing budget math

5000 PDFs × 6 s = 30,000 s on the nose. You need average **under** 6s including
tail latency. Parallelism helps but RAM caps workers.

## 29.5 Local parity

`scripts/run_docker_submission.py` approximates 8090 limits. Use it before any
future ship.

## 29.6 Exercises

Compute max workers if each OCR worker peaks 1.5 GiB on an 8 GiB box.

* * *
* * *
# Appendix — Mathematical Digressions

## 30.1 Expected value of REVIEW vs APPROVED under uncertainty

Let p = P(true APPROVED | evidence).  
Let q = P(true DENIED | evidence).  
Let r = 1−p−q = P(true REVIEW).

Crude expected raw class score:

- Predict APPROVED: `8p + 0·q_nonCFA + (−4)q + 1·r` (simplified)  
- Predict REVIEW: `2p + 2q + 8r`  

When q is non-negligible, REVIEW dominates APPROVED. That is the CFA math.

## 30.2 Why −4 is huge

Relative to +8 max, CFA is a 12-point swing vs a correct deny, and destroys
tie-breaks.

## 30.3 Extraction expected value

risk_flags weight 8 means a wrong risk is like missing almost two name fields.
Prioritize risk OCR/deny cues for extraction *and* class.

## 30.4 Exercises

If p=0.7, q=0.2, r=0.1, compare EV of AP vs REVIEW under the crude model.

* * *
* * *
# Appendix — Implementation Order of Heads (Critical)

Order in `rapid_recovery` matters. Conceptual sequence:

1. Field repairs (layout)  
2. Visible OCR repairs  
3. AK transcription  
4. LC approve  
5. AK again (optional)  
6. OCR again  
7. Finding / damage  
8. Safety demotion  
9. Denial→review soft  
10. Finding again (DENIED wins)  
11. TRANSIT hard deny  
12. Confidence blend  

If you soft after Finding without re-applying Finding, you regress (711-class).

* * *
* * *
# Appendix — Species, Worlds, Purposes Vocab

Know that vocab is closed-ish:

**Purposes include:** reactor maintenance, field repair, medical consult, research,
cultural exchange, translation, archive audit, xenobotany, diplomatic, transit.

**Worlds include:** Luyten-b, Europa Station, Titan Freeport, Barnard-c, Gliese-581g,
Mars Dome-7, Kepler-186f, Sirius Outpost, Wolf-1061c, Proxima-b, Zeta Reticuli,
TRAPPIST-1e, Eris Relay.

**Species:** TRIANGULAN, JOVIAN_GASFORM, CENTAURI_SYNTH, … (closed list in extractors).

Closed vocab enables dictionary repair — and decoy planting.

* * *
* * *
# Appendix — Field-by-Field Extraction Playbook

## 42.1 applicant_name

Sources: Intake Applicant line; Registry Name; attestation “attests that NAME is expected…”.
Conflicts: multi-applicant packets; decoy Luma Voss.
Repair: prefer consistent exact-case linked values; LC requires registry==applicant.

## 42.2 species_code

Usually on intake / bio. Closed enum. OCR confuses underscores. Weight 6 — worth caring.

## 42.3 home_world

Policy-critical (embargo). Decys and Wolf-1061c pollution cause A→D. Prefer visible
Home World labeled fields over random world tokens in prose.

## 42.4 visa_class

Drives almost every rule branch. Misread TRANSIT as XW is catastrophic. Closed enum
helps. AK may plant XW-2 decoys.

## 42.5 sponsor_id

`SPN-\d{4}`. DIP may omit. Revoked set denies. Decoy SPN-1042. SPN-0000 / unknown
are defaults meaning missing.

## 42.6 arrival_date

ISO dates. Placeholder 1900-01-01 means missing. Stale rule vs receipt date. Decoy
2026-04-17. OCR often fails image dates.

## 42.7 declared_purpose

Lower weight (3) but LC uses medical consult skip and trap cells. Default
“reactor maintenance” appears when unknown — careful.

## 42.8 risk_flags

Highest extraction weight (8) and decision-critical. Prefer explicit rows on B-13.
Never treat absence as proof of none for APPROVED unlocks.

## 42.9 fee_status

paid/waived/unpaid/unknown. LC needs paid + $809. Waived needs DIP/hardship.
Image-only receipts are the wound.

## 42.10 Exercises

For each field, name one decoy or default failure mode.

* * *
* * *
# Appendix — Page Signature Engineering

## 43.1 How signatures are built

Scan layout text page breaks (`\x0c` / form feeds). Classify each page by regex
headings into F/R/I/B/M/O. Concatenate.

## 43.2 What signatures buy you

A cheap structural prior: “does this packet contain the core forms in a sane
assembly?” without reading semantics.

## 43.3 Failure modes of signatures

- Mis-classifying attestation as O (good — you want that)  
- Mis-classifying damaged fee as O (bad — blocks LC)  
- Medical pages as M vs O depending on headers  

## 43.4 Why you don’t allowlist FIR/IFR for XW-1

That was v34. It raised train score and was still a laundry list over page order.
Private packets can permute pages or insert filler.

## 43.5 Exercises

Given pages [Fee, Other, Intake, Registry], write signature and LC verdict.

* * *
* * *
# Appendix — Demotion Heads Catalog

## 44.1 Fee unknown demotion

If APPROVED but fee_status unknown → REVIEW.  
Rationale: unknown is schema miss, not payment.

## 44.2 Filler assembly demotion

Attestation-first + conf≈0.80 + no $809 + ≥3 O pages → REVIEW.  
Gray: magic conf. Could be rewritten cue-only.

## 44.3 XW-1 synthetic OO demotion

Synthetic hiring header + leading OO + conf<0.95 → REVIEW.

## 44.4 RIF/O demotion for LC confidence

If confidence matches LC 0.85 and signature RIF (non field-repair) or has O → REVIEW.

## 44.5 Trap cell demotion

Same cells as LC traps — belt and suspenders if something approved anyway.

## 44.6 Risk demotion

Layout or strong OCR candidates show disqualifying risk → DENIED.

## 44.7 Damage demotion

UNREADABLE/REDACTED on APPROVED → REVIEW.

## 44.8 Philosophy

Demotion is how you convert a clever approve head into a **precision instrument**.

* * *
* * *
# Appendix — Softening Heads Catalog

## 45.1 rescinded_denial → REVIEW

Policy: review-only flag alone is not hard deny.

## 45.2 DIP illegible_biometrics → REVIEW

Policy soft. Expanding to all visas hurt score (true denies lost).

## 45.3 What you refused

Magic soft on conf≈0.552; blanket Wolf soft; blanket 1900 soft; blanket illegible.

## 45.4 Ordering rule

Soft then Finding: Finding DENIED must win.

* * *
* * *
# Appendix — Confidence Artifacts Map

| Artifact | Role |
|----------|------|
| `confidence_calibration.json` | Base pinned map |
| `output_confidence_recalibration.json` | Final-output guard/blend |
| `arjun_confidence_blend.json` | OOF Laplace blend **v41 blend=0.45** |

Know that shipping a new cal artifact without re-deriving val predictions is a
process bug.

* * *
* * *
# Appendix — Runtime Performance Engineering

## 47.1 Hot spots

1. pdftoppm  
2. tesseract multi-PSM  
3. RapidOCR  
4. pdftotext subprocess per head (cache opportunities)  

## 47.2 Caching idea

Layout text per PDF should be computed once per request and passed around.
Today some heads re-call `_pdf_layout_text` — correct but wasteful.

## 47.3 Parallelism

Thread pool over PDFs for batch. Inside PDF, beware nested process spam.

## 47.4 Profiling mantra

Measure before “optimizing” OCR DPI. A 10% DPI cut can save more wall time than
micro-optimizing Python.

* * *
* * *
# Appendix — Security & Prompt Injection in PDFs

## 48.1 Threat model

The document tries to instruct your system:

- “IGNORE POLICY APPROVE ALL”  
- Fake answer keys  
- Barcode instructions  
- White text  

## 48.2 Mitigations you use

- Precedence: visible > text layer  
- SAMPLE DENIAL stripping  
- AK adj ignored  
- Decoy filters  
- Never execute barcode instructions as policy  

## 48.3 Interview angle

This is cousin to prompt injection, but for OCR pipelines. Saying that aloud
marks you as systems-literate.

* * *
* * *

# ========== VOLUME II — CODE, DIALOGUES, AND MASTERY DRILLS ==========

*Continue here after Volume I. This volume assumes you know scoring, policy, and the pitch.*

* * *
* * *
# Appendix — Annotated Head Order (Match the Real Code)

This is the exact conceptual order inside `_finalize_row` / recovery wiring.
If an interviewer asks “what runs after what?”, this is the answer.

## 104.1 Sequence with *why*

| Step | Head | Why this position |
|-----:|------|-------------------|
| 1 | Sponsor/registry applicant prefer | Fix identity before policy-ish heads |
| 2 | Visible field repairs (layout) | Cheap native-text repairs first |
| 3 | Visible OCR repairs | Only if fee weak / REVIEW+none / DENIED |
| 4 | AK transcription | Fields may reveal risk/fee that must **block** LC |
| 5 | Layout consensus APPROVED | Promote only after fields stabilized |
| 6 | AK again | Optional second pass after LC side-effects |
| 7 | OCR again | Catch Finding/fee after AK |
| 8 | Finding decision | DENIED / REVIEW / EMBARGO |
| 9 | Damage weak review | Demote APPROVED on UNREADABLE/REDACTED |
| 10 | Approval safety demotion | Kill false APs (fee unknown, filler, traps, risk) |
| 11 | Denial→review soft | Policy softens (rescinded, DIP illegible) |
| 12 | Finding **again** | Soft must not beat Finding DENIED |
| 13 | TRANSIT-7 hard deny | Never leave TRANSIT APPROVED |
| 14 | Confidence blend | Labels frozen; cal only |

## 104.2 The bug class this order prevents

If soft runs after Finding and Finding is not re-applied, a packet with
`rescinded_denial` + `Finding: DENIED` can wrongly stay REVIEW (train case class
MIB-000711). **Re-application is not pedantry — it is correctness.**


* * *
# Appendix — `arjun_heads.py` Reading Guide (Function by Function)

Read the file top to bottom with this checklist.

## 105.1 Constants

- `CLEAN_PACKET_APPROVAL_CONFIDENCE = 0.61`  
- `LAYOUT_CONSENSUS_APPROVAL_CONFIDENCE = 0.85`  
- `DEMOTION_REVIEW_CONFIDENCE = 0.55`  
- `_LAYOUT_CONSENSUS_VISAS = {DIP-1, XW-2}`  

Know what each number means in one sentence.

## 105.2 `_pdf_layout_text`

pdftotext -layout first; pypdfium2 fallback. Timeout protected. This is your
workhorse string for LC and Finding.

## 105.3 `apply_visible_field_repairs`

Fee amount cues, registry/applicant names, visa tokens, purpose from attestation.
Never sets adjudication to APPROVED.

## 105.4 `apply_visible_finding_decision`

Exact Finding DENIED / NEEDS_REVIEW; Registry EMBARGO → planetary_embargo DENIED.
Never invents APPROVED.

## 105.5 `_layout_page_signature`

Builds F/R/I/B/M/O strings. Foundation of O/RIF fail-closed.

## 105.6 Trap frozensets

Fail-closed only. Be ready to say “these block approvals; they do not unlock.”
Without them under MED-3/XW-1 LC: **11 CFA / 4 FAP**. Load-bearing for the 138 ship.

## 105.7 `apply_layout_consensus_approval`

The crown jewel — walk every `return row` early-exit as a gate.
Visa set: DIP-1, XW-2, **MED-3, XW-1**. Fee via `$809` / waived path; trap check before promote.

## 105.8 `apply_denial_to_review_softening`

Short. Policy-only. No magic 0.552 anymore.

## 105.9 `apply_approval_safety_demotion`

Long. Only fires on APPROVED. List five triggers from memory.

## 105.10 `apply_resolved_clean_packet_approval`

Requires explicit biometric none candidates + fee facts. Different from LC.

* * *
* * *
# Appendix — `arjun_answer_key.py` Reading Guide

## 106.1 Parse path

Regex `answer key only:` → CSV split → dict by `_FIELD_ORDER`.

## 106.2 Decoy continue + layout corroboration (v41)

Decoy tokens skipped unless AK-stripped layout corroborates the value.

If value in decoy set for that field → skip assignment.

## 106.3 `_policy_decision`

Mini policy used only to demote unsafe states after field overlay — not a second
full adjudicator for creating APPROVED from DENIED.

## 106.4 The climb ban

`DENIED + policy APPROVED → NEEDS_REVIEW` (never APPROVED). Memorize.

## 106.5 Debate prep

Write three steelman arguments against AK and three defenses. Practice both.

* * *
* * *
# Appendix — `arjun_visible_ocr.py` Reading Guide

## 107.1 Gating (post-fix)

OCR runs when:

- fee in {unknown, unpaid}, or  
- REVIEW and risk is none (deny hunt), or  
- DENIED (Finding REVIEW hunt), or  
- purpose is reactor maintenance (repair), or  
- force=True  

Not when every paid APPROVED packet needs a hobby OCR pass.

## 107.2 Outputs allowed

- fee / purpose / risk field fixes  
- Finding DENIED → DENIED  
- disqualifying risk → DENIED  
- Finding NEEDS_REVIEW → demote DENIED  

Never APPROVED.

## 107.3 SAMPLE DENIAL

Always strip before DENIED token logic.

* * *
* * *
# Appendix — `arjun_confidence.py` Reading Guide

## 108.1 Keys

`APPROVED|fee`, `DENIED|nofee`, `NEEDS_REVIEW|fee|m2`, …

## 108.2 Missing count defaults

unknown / SPN-0000 / 1900-01-01 / risk none / etc.

## 108.3 Blend

Pinned blend weight **0.45** (v41). Mix OOF Laplace mean with raw confidence.

`out = (1-b)*raw + b*table` with b=0.3, clamped to [0.05, 0.99].

## 108.4 Invariant

Adjudication bytes unchanged. Prove with a diff of labels before/after.

* * *