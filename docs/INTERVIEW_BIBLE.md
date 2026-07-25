# The MIB Doc Challenge Bible

This book teaches one contest from **absolute zero**.

You do not need to know coding, PDFs, GitHub, Docker, or “AI.”  
Each chapter only uses ideas the earlier chapters already explained.  
If a sentence feels dense, the next one usually unpacks it like you’re five.

**Optional spoiler (ignore until Chapter 8):** we built a program, entered the
contest, and scored about **138 out of 150** on the practice homework without
making the worst kind of mistake. You will understand what that means after
Chapters 1–2.

**How to read:** start at Chapter 1. Go in order. Stop at any “you should feel”
checkpoint and say it out loud. Advanced appendices at the end are optional.

* * *
# Contents

1. [The contest](#1-the-contest) — what is this even?
2. [Scoring](#2-scoring) — how they count points
3. [Why PDFs lie](#3-why-pdfs-lie) — why “copy the text” fails
4. [The rulebook](#4-the-rulebook) — how a clerk is supposed to decide
5. [Our program, in English](#5-our-program-in-english) — the assembly line
6. [Extra safety gadgets](#6-extra-safety-gadgets) — the parts we invented
7. [How we hand it in](#7-how-we-hand-it-in) — the sealed box + homework
8. [How we improved each time](#8-how-we-improved-each-time) — the climb
9. [Same climb, more detail](#9-same-climb-more-detail)
10. [Things we refused to do](#10-things-we-refused-to-do)
11. [Who else is in the race](#11-who-else-is-in-the-race)
12. [What still breaks](#12-what-still-breaks)
13. [What we’re doing now](#13-what-were-doing-now) — waiting
14. [If someone asks you in a room](#14-if-someone-asks-you-in-a-room)
15. [Tiny dictionary](#15-tiny-dictionary)
16. [Optional advanced appendices](#deep-appendices)

* * *
# 1. The contest

*You are allowed to feel dumb. This chapter assumes you know nothing.*

## 1.0 The whole thing in five lines

1. A company called **8090** is running a public tryout (a hiring contest).
2. The theme is fake **Men in Black** paperwork for aliens.
3. Your job is **not** to roleplay an agent. Your job is to write a
   **computer program** that reads those paperwork files.
4. For each file, the program must say: **let them in**, **keep them out**,
   or **ask a human**.
5. Whoever’s program does this best — under strict rules — looks hireable.

That’s the entire movie trailer. Everything else is detail.

## 1.1 What’s actually happening

Imagine a stack of messy application forms. Each application is a **PDF** —
a digital document, like a multi-page scan on a laptop.

A real human clerk would:

- skim the pages,
- copy down facts (name, visa type, did they pay the fee…),
- look for danger marks (stamps, warnings),
- decide: approve, deny, or send to a supervisor.

8090 says: **build a robot clerk that does that job.**

The alien story is costume. The skill they want is:

> Can you make software that reads hard documents carefully and decides
> safely — without cheating and without calling the internet?

## 1.2 Words you’ll see (said slowly)

| Word | Pretend it means… |
|------|-------------------|
| **Contest / challenge** | The whole 8090 tryout |
| **Packet / case** | One alien’s paperwork = usually one PDF |
| **Field** | One fact to extract, like “name” or “fee paid?” |
| **Decision / adjudication** | Approve / deny / ask a human |
| **APPROVED** | Let them in |
| **DENIED** | Keep them out |
| **NEEDS_REVIEW** | Not sure — ask a human |
| **Offline** | While grading you, your program **cannot** use Wi‑Fi, ChatGPT, or cloud tools |
| **Score** | A number out of **150**. Higher is better |

## 1.3 What “winning” means

They give everyone the same messy PDFs.  
Your program writes answers.  
They compare to hidden correct answers and give points.

Three kinds of being right:

1. Did you copy the **facts** correctly?  
2. Did you pick the right **decision**?  
3. When you said “I’m 90% sure,” were you actually right about that often?

**Nightmare mistake** (later called **CFA**):

> Saying **APPROVED** when the truth was **DENIED**.

Like stamping “come in” on someone who should have been blocked.

## 1.4 The PDFs are mean on purpose

Not clean tax forms. They include:

- ink **stamps** you can’t copy-paste as text,
- fake “SAMPLE DENIAL” watermarks,
- washed / damaged fee receipts,
- planted “answer key” text that lies if you trust it blindly.

A program that only “selects all text” will fail. A serious program usually
**turns each page into a picture** and **reads the picture**. Chapter 3.

## 1.5 What you hand in (homework metaphor)

### Homework A — Public recipe book

A public code folder on GitHub, including a **Dockerfile** (recipe for a
sealed mini-computer image). Graded with the network unplugged.

### Homework B — Answer sheet for the big practice exam

A **pull request** (PR) on the official contest project — “please accept my
submission folder” — with:

1. **`predictions.jsonl`** — 5,000 lines of answers  
2. **`MEMO.md`** — short write-up  
3. **`SUBMISSION.md`** — links + claimed practice score  

### Homework C — A Google form

Code alone may not be enough.

## 1.6 What “running your program” means

> “Here’s a folder of PDFs. Write answers into this output file. Go.”

No human clicking. No internet. No downloading a smarter model mid-grade.

## 1.7 Practice homework vs the real final

| Pile | How many | See correct answers? | For |
|------|--------:|----------------------|-----|
| **Train** | 1,000 | Yes | Practice at home (“138 / 150” lives here) |
| **Validation** | 5,000 | No | Big practice exam in the PR |
| **Private** | Hidden | No | Real final grade / who is #1 |

Memorizing the 1,000 practice files can fake a high homework score and die
on the final. Later we talk about cheat sheets we refused.

> High practice score only counts if the method should work on new PDFs.

## 1.8 Checkpoint — say this to a friend

> “8090 is hiring with a Men-in-Black paperwork contest. You write a program
> that reads tricky PDFs and decides approve, deny, or ask a human — with no
> internet while they grade you. Score out of 150. Worst mistake: approving
> someone who should have been denied.”

Ready for Chapter 2.

* * *
# 2. Scoring

*Still dumbo. This is just “how the grade book works.”*

## 2.0 The report card has three sections

Total score is out of **150**:

| Section | Max points | Plain meaning |
|---------|----------:|---------------|
| **Extraction** | 50 | Did you copy the facts right? |
| **Classification** | 80 | Did you pick the right decision? |
| **Calibration** | 20 | Are your confidence numbers honest? |

Add them up (minus penalties if you skip cases). That’s your score.

## 2.1 The decision points (the biggest chunk)

For each case, imagine a mini-score for the decision.

| What happened | Rough vibe |
|---------------|------------|
| You matched the true decision | Best |
| You said “ask a human” when you weren’t sure | Okay / conservative |
| You said APPROVED but truth was DENIED | **Disaster** (CFA) |
| Other wrong | Bad / zero |

Turning a careful “ask a human” into a **correct** approve/deny is how you
climb. Doing it wrong once can wipe a lot of climbing.

**CFA** = Catastrophic False Approval = APPROVED when truth was DENIED.

## 2.2 Confidence points (calibration)

Your program also outputs a number from 0 to 1: “how sure am I?”

If you always say 99% and you’re often wrong, you lose calibration points.  
If your 70% cases are right about 70% of the time, you look honest.

You can improve calibration **without changing any decisions** — like
retuning a speedometer without changing where the car goes.

## 2.3 Our hard rule on the practice set

On the 1,000 practice cases we care about:

- **CFA = 0** (never approved a true DENIED)  
- Also no false APPROVED on true “needs review”  
- Final practice score we shipped: about **138.086 / 150**

You’ll see those numbers again in the climb chapter. For now just know:
**safe > flashy.**

## 2.4 Checkpoint

> “Grade is /150: facts, decisions, honest confidence. Approving a true deny
> is the nightmare. We kept that at zero on practice.”

* * *
# 3. Why PDFs lie

## 3.0 The trap

A PDF can contain:

- text you can highlight and copy, **and**
- pictures of text (stamps, handwriting, washed ink) with **no** copyable text.

Danger marks are often in the second pile.

So “extract text from PDF” can miss the stamp that says DENIED, and still
cheerfully read a fake line that says everything is fine.

## 3.1 What serious programs do instead

1. **Draw each page as an image** (like a screenshot of the page).  
2. **OCR** = Optical Character Recognition = “read the picture into letters.”  
3. Then decide using what the eyes would have seen.

We call that **render-first** (pictures first, not embedded text first).

## 3.2 Dumb ideas that die

| Idea | Why it dies |
|------|-------------|
| Only copy embedded text | Misses stamps; believes decoys |
| “If risk says none, approve” | “None” often means “I didn’t see anything,” not “safe” |
| Call ChatGPT / cloud vision during grading | Forbidden (offline) |
| Memorize practice answers | Dies on private final |

## 3.3 Checkpoint

> “These PDFs trick text-only programs. We screenshot pages and read the
> pictures. Silence is not safety.”

* * *
# 4. The rulebook

## 4.0 You don’t invent immigration law

8090 publishes a **field manual** — the clerk’s rulebook.

Your program must follow **their** rules, not vibes.

## 4.1 Fail closed (the personality of our clerk)

If evidence is missing or conflicting:

> Prefer **ask a human** over **approve**.

That’s **fail closed**.  
The opposite (guess approve) is how you create CFAs.

## 4.2 Who wins when pages disagree?

Rough trust order (high → low):

1. Clear official findings / stamps  
2. Registry / biometric extracts  
3. The main intake form  
4. Sponsor letters  
5. Suspicious planted text  

Crossed-out text is a retraction. Don’t treat it as the answer.

## 4.3 A few rules that matter for disasters

- If a **danger mark is visible**, don’t approve.  
- If danger might be there but you can’t see it (**silent**), don’t pretend
  you cleared it.  
- If you don’t even know whether the fee was paid, don’t approve.  
- Some visa types look “easy to auto-approve” and are exactly where silent
  danger stamps hide. We learned that the hard way (Chapter 8).

## 4.4 Checkpoint

> “We follow their manual. When unsure, ask a human. Never treat missing
> evidence as a green light.”

* * *
# 5. Our program, in English

## 5.0 We didn’t invent everything from scratch

A public engineer (**strobl**) already published a strong open-source starting
pipeline under MIT license. We reused it with credit, then added our own
safety layers on top.

Re-running that baseline alone scored about **130 / 150** with zero CFA.
That’s our floor story: stand on something measured, don’t rebuild OCR for ego.

## 5.1 The assembly line (one PDF)

Imagine a factory belt:

1. **Open the PDF and screenshot every page.**  
2. **Read the screenshots** with a text-from-image engine (Tesseract).  
3. If some fields are still blank, try a second reader **only for blanks**
   (RapidOCR) — it doesn’t get to outvote a good answer.  
4. **Resolve fights** when pages disagree (trust rules from Chapter 4).  
5. **Apply the field manual** to draft a decision.  
6. **Run our extra safety gadgets** (Chapter 6) — repairs, “are we sure
   enough to approve?”, demotions, confidence tuning.  
7. **Write one answer line** for that case.

Do that for every PDF in the folder.

## 5.2 Five commandments (tape these on the wall)

1. **Pictures first** — visible evidence beats embedded text.  
2. **Fail closed** — silence ≠ clearance.  
3. **Never CFA on purpose** — CFA=0 is a hard practice gate.  
4. **No cheat sheets of case IDs** — and don’t peek at the answer key file
   at scoring time.  
5. **Credit what you borrowed** — strobl base; we own the extra gadgets.

## 5.3 Checkpoint

> “Screenshot → read → resolve → rulebook → our safety extras → write
> answers. Borrowed a strong base, added fail-closed layers.”

* * *
# 6. Extra safety gadgets

*These are the “Arjun heads” — little post-steps after the base clerk.*

You can skim this once, then come back after Chapter 8.

## 6.1 Fix obvious fields when the page shows them

If the page clearly shows a fee amount or a name, repair the field.  
This alone does **not** mean “approve.”

## 6.2 The careful auto-approve gate (layout consensus)

Sometimes the base clerk says “ask a human,” but the packet looks clean.

We only flip to APPROVED if **many** visible checks pass, including things
like:

- fee really looks paid (often a visible **$809**),
- registry name matches applicant name,
- no visible danger,
- not a known dangerous pattern we quarantined.

We call this **layout consensus** (LC) — “the layout agrees it’s safe.”

## 6.3 The planted “answer key” text

Some PDFs contain a tiny planted SYSTEM “answer key” block.

**Trap:** if you copy its final decision blindly, you can CFA-bomb.  
**What we do:** maybe repair **fields** (name, fee…) when the rest of the
page agrees; **never** take its approve/deny as gospel.  
There’s a kill switch to turn this off.

## 6.4 Honor explicit findings

If the page literally says Finding: DENIED or NEEDS_REVIEW, listen.  
If registry status is EMBARGO, that’s a deny path.

## 6.5 Demote bad approvals

If we somehow approved but fee is unknown, packet is filler garbage, or
danger is visible — kick it back to “ask a human.”

## 6.6 Soften some denies to review (never invent approve)

Example vibes: a denial that was rescinded; some illegible-biometrics cases.
These move DENIED → REVIEW. They do **not** mint APPROVED.

## 6.7 Confidence blend

After the decision is frozen, retune the confidence number with a small
honest statistical blend. **Labels don’t change.** CFA risk from this step:
basically none by construction.

## 6.8 Checkpoint

> “Extra gadgets repair fields, carefully approve only with proof, fence the
> planted key, demote bad approvals, and retune confidence without changing
> decisions.”

* * *
# 7. How we hand it in

## 7.0 The sealed box

They build your Docker image and run it offline on limited CPUs/RAM.  
Your tools and calibration files must already be inside.

## 7.1 What is live right now

| Piece | Where |
|-------|--------|
| Solution recipe book | GitHub repo **`mib-doc-solution`** |
| Contest entry | Pull request **#15** on the official challenge repo |
| Practice claim | **138.086 / 150**, CFA = 0 |
| Validation answers | 5,000 / 5,000 lines, validator clean |

Account: **`arjunkshah12345-hash`**.

**Note:** there is also an experimental repo named `mib-challenge-v1`.  
That is a **side lab**. The contest PR points at **`mib-doc-solution`**, not v1.

## 7.2 Checkpoint

> “We shipped a public Dockerized recipe and a PR with 5,000 validation
> answers claiming ~138 with zero catastrophic false approvals.”

* * *
# 8. How we improved each time

*Now the story. You finally know what the numbers mean.*

## 8.0 How to read a score jump

Each row is: we changed the robot → practice score moved → was it honest?

**Transfer?** means “should this still work on new PDFs?”  
**Yes** = probably. **No** = cheat-sheet smell. **Bet** = honest but risky.

## 8.1 Scoreboard (practice / 150)

| Step | Score | What we did | Transfer? |
|-----:|------:|-------------|-----------|
| Start | — | Read rules; text-only dies | — |
| 1 | **130.26** | Reuse strobl picture-first base | Yes |
| 2–5 | **132.3 → 133.60** | Our first real ships + safety | Yes |
| 6–7 | **~135.1–135.4** | Stop approving our own mistakes | Yes |
| ✗ | **135.98 / 137.48** | Cheat-sheet approve lists | **No — deleted** |
| 8–10 | **135.27 → 135.56** | Integrity reset + honest confidence | Yes |
| ✗ | ~138 allowlists | Phonebook “approve these combos” | **Refused** |
| 11–13 | **~138.0 → 138.086** | Careful auto-approve expand + **block** lists + portable fixes | **Bet** |

## 8.2 The story in five phases

### Phase A — Stand up something real (→ 133.60)

Don’t reinvent OCR. Borrow strobl. Add: never approve if fee unknown;
careful auto-approve only for the safest visa types with visible proof;
fence the planted key; ship Docker.

**Lesson:** first points come from safety + evidence, not max approvals.

### Phase B — Tighten our own approvals (→ ~135.4)

The careful auto-approve was too eager. Demoting bad approvals **raised**
the score. Fixing a silly name-matching bug gave free honest points.

**Lesson:** sometimes “approve less” scores higher.

### Phase C — Temptation (137.48) then delete

We tried phonebook unlocks (“if this purpose + page pattern, approve”).  
Practice looked hot. It smelled like memorization. We deleted it. Score
fell to ~135.3 — **correct**.

**Lesson:** highest practice score ≠ what you should ship.

### Phase D — Honest 135.56 ship

Honor explicit DENIED / EMBARGO. Retune confidence without changing
decisions. This was the conservative ship. Closest rival later: ~**135.30**.

### Phase E — The 138 bet we actually shipped

Not the phonebook approve lists.

Instead:

1. Allow careful auto-approve on a few more visa types,  
2. Keep a **block list** of patterns that caused silent-stamp disasters
   (these **stop** approve — they don’t mint approve),  
3. Add portable fee / key-corroboration / confidence polish.

**Live: 138.086, CFA=0.**

Why not roll back to 135.56? Rival is too close. Rollback makes it easy for
them to beat us on the final. We accepted risk to chase #1.

## 8.3 What “the bet” means in one picture

If we expand careful auto-approve **without** the block lists:  
practice still looks high, but we get **many CFAs** (we measured **11**).

So the block lists are load-bearing for “high score + zero CFA” on practice.  
On the private final, they only help if similar traps appear again.

## 8.4 Checkpoint

> “We climbed 130 → 135.5 honestly, refused cheat-sheet 138, then shipped a
> different 138: expand careful approve behind block lists because the rival
> sits at 135.3.”

* * *
# 9. Same climb, more detail

## 9.1 Empty desk
Read their docs. Download data. Learn: fees and danger marks dominate errors;
silent stamps dominate CFA risk. Only the official scorer’s numbers count.

## 9.2 Borrow strobl → 130.26
Seniors reuse measured baselines.

## 9.3 First ships → 133.60
Versions v27→v30: fee gate, careful DIP/XW approve, fenced key fields, Docker.

## 9.4 Tighten → ~135.4
Demote false approvals; honor NEEDS_REVIEW findings; softens; regex fix.

## 9.5 Temptation → delete
Signature / purpose phonebooks to 137.48. Probe: expand visas alone → CFAs.
Deleted.

## 9.6 Integrity 135.56
Strip laundry; Finding DENIED + EMBARGO; confidence blend.

## 9.7 Ship bet 138.086
Expand visas + block lists (~+2.1) + small portable lifts.  
Rough private odds we told ourselves: favorite, not a lock; main upset path
is rival transferring cleaner while we eat a new silent-stamp CFA.

## 9.8 Checkpoint

You can narrate eras A→E without notes. That’s the interview chronicle.

* * *
# 10. Things we refused to do

| Temptation | Plain English | Status |
|------------|---------------|--------|
| Approve phonebooks | “If purpose+pattern matches, approve” | Refused forever |
| One-off combo unlocks | Tiny tables that only fit 1–2 practice cases | Refused forever |
| Case-ID cheat sheets | Hardcode answers for known IDs | Cheating |
| Peek at train answer file while scoring | Oracle | Worthless on private |
| “I didn’t see danger ⇒ safe” | Silence as clearance | CFA factory |
| Ship vanity 138 allowlists | Brag number | Refused |
| Roll back to 135.56 while rival ~135.3 | Safer ego | Refused (want to win) |

**Shipped block lists ≠ approve phonebooks.**  
Same family of tables, **opposite polarity**: stop approve vs mint approve.

## 10.1 Checkpoint

> “We refuse cheat-sheet approves. We shipped fail-closed blocks under a
> careful approve expand to stay ahead of a 135.3 rival.”

* * *
# 11. Who else is in the race

Published practice claims (approximate, from their submission files):

| Who | ~Practice | Notes |
|-----|----------:|-------|
| **Us** | **138.086** | CFA 0; the 138 bet |
| **Abhishek** | **135.30** | Closest real rival; CFA 0 |
| thegoleffect | ~132 | Solid |
| strobl | ~130 | Baseline author |
| Others | ≤~130 | Need a miracle for #1 |

Private final can reorder people. On **known** claims, we’re first; Abhishek
is the main person who can steal it if our bet backfires.

## 11.1 Checkpoint

> “Public board: we’re ahead. Private #1 still a fight, mostly vs Abhishek.”

* * *
# 12. What still breaks

1. Danger stamps with no readable text (eyes see ink; OCR sees nothing).  
2. Brand-new silent-stamp patterns on private that our block list never saw.  
3. Washed fee receipts.  
4. Filler junk packets that look completable.  
5. Planted SYSTEM decoys.  
6. Some true approves still stuck in “ask a human.”  
7. Some true denies still stuck in “ask a human.”

The honest next research step is better **stamp vision**, not another
purpose phonebook.

## 12.1 Checkpoint

> “Silent stamps still own the residual. That’s the cliff under our 138 bet.”

* * *
# 13. What we’re doing now

**Hold the ship.** Read. Wait.

Do not expand block lists for fun.  
Do not roll back unless the goal changes from winning to max safety.  
Only reopen if someone publishes clearly above ~138 with clean CFA=0, or
organizers ask for a fix.

## 13.1 Checkpoint

> “Shipped. Chilling. Bible time.”

* * *
# 14. If someone asks you in a room

**3-minute whiteboard:**  
PDF → pictures → read text → resolve fights → rulebook → safety gadgets →
confidence → answer file.  
Then the friend-pitch from §1.8. Then one refusal from §10. Stop.

| They ask | You say |
|----------|---------|
| Why pictures first? | Stamps/decoys; humans look with eyes. |
| How avoid the nightmare approve? | Fail closed; honor findings; no approve-phonebooks; block lists under expanded careful-approve; without blocks we measured many CFAs. |
| Why 138 after refusing 138? | Refused *approve* phonebooks. Shipped *block* lists + portable fixes. Rival ~135.3. |
| Private risk? | New silent stamps our blocks miss. |
| Is the planted key cheating? | Fields only, must match the page, never take its decision. |
| What’s next? | Wait. Real residual is stamp vision. |

* * *
# 15. Tiny dictionary

| Term | Meaning |
|------|---------|
| PDF | Digital multi-page document |
| OCR | Read letters from a page picture |
| Render-first | Screenshot pages before trusting embedded text |
| CFA | Approved a case that should have been denied |
| Fail closed | When unsure, ask a human — don’t approve |
| LC / layout consensus | Careful auto-approve only if many visible proofs agree |
| Allowlist / laundry | Cheat-sheet table that **creates** approvals — refused |
| Trap / block list | Table that **blocks** careful auto-approve on known disaster patterns — shipped |
| Offline | No internet during grading |
| Train / val / private | Practice with answers / practice exam / real final |
| Docker | Sealed runnable box built from a recipe file |
| JSONL | One answer per line in a text file |
| Transfer | Still works on PDFs you haven’t memorized |

* * *
# Deep appendices

**Optional. Advanced. Not required to understand the contest.**

These notes are denser (engineer dialect). Same shipped claim: **138.086 /
CFA=0** on practice; still refuse approve-phonebook 138; trap block lists are
the ship bet.

If Chapter 1–15 already make sense, you can stop. Come here only when you
want code-level or ablation-level detail.

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