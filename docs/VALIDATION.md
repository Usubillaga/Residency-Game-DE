# Validation record

## Questions on current guideline topics — 10 October 2026

The user supplied photos of journal pages, slides and posters. They served only to pick topics; no figure, table or text was copied, and no author is named. One image, a treatment algorithm with garbled drug names and labels, was not used as a source; its topics were checked against the guidelines themselves.

- **Writing and review:** 25 single questions in 7 batches (metastatic prostate cancer, PARP inhibitor toxicity and early detection, stone metaphylaxis, NMIBC and UTUC, priapism, andrology, kidney). Each was written by one author with its hint, checked against EAU 2026, the German S3 prostate cancer guideline and EU product information, and then reviewed by an independent reviewer acting as urologist, and for drug questions also as clinical pharmacologist. None was dropped; reviewers fixed 19. Examples:
  - the triplet is an option, not generally preferred over ADT plus an ARPI;
  - a PSMA-negative liver lesion counts from 1 cm (VISION exclusion);
  - a confirmed PSA of 3 ng/ml or more leads to a short-term recheck, not a fixed 3-month interval;
  - a hint that almost spelled out the haemoglobin thresholds for talazoparib was rewritten;
  - the ED screening answer now allows treatment alongside the basic work-up.
- **Conflicts with existing cases:** reviewers compared each question with the cases on the same topic.
  - *Priapism:* the existing case said an immediate prosthesis is discussed after about 36 hours; the new one said 48. The AUA/SMSNA guideline uses 36 hours, while the European text puts the limit of benefit from interventions at 48–72 hours. Both cases now say "about 36–48 hours"; the new question is decided by MRI-proven necrosis, so its answer does not depend on the exact hour.
  - *Early detection:* bank-uro-pca-00004 said the rectal examination complements the PSA test. Under the German S3 guideline 8.1 it is no longer part of early detection but stays relevant for local staging; the explanation was corrected through the correction layer.
  - The other overlaps (ARPI switch after abiraterone, thiazide dose, uric acid dissolution, cardiovascular work-up for ED, biopsy before surveillance, belzutifan on the protocol page) agree in content and were left unchanged.
- **Links:** 17 links from protocol regimens and 2 from radiotherapy schemes lead to the new questions, so *Practise questions* finds them.

## Protocols, radiation oncology, new questions and the attending's hints — 9–10 October 2026

**Network limits.** EMA, fachinfo.de, PubMed and uroweb.org cannot be downloaded from the build environment. Every number was therefore checked through web-search results, label copies (emc, DailyMed, company HCP pages) and trial reports. Where the EU text itself was not returned, the record below says which other source was used.

**Systemic therapy protocols (`data/protocols.json`, 58 regimens).**
- *Research:* one clinical pharmacist per tumour group wrote the regimens with doses, cycles, support, cautions, EU approval status and sources.
- *Verification:* an independent verifier re-derived every dose, schedule and cycle count with fresh searches and corrected the file. Urothelial carcinoma and intravesical therapy were verified twice, because an interrupted run was resumed.
  - Corrections at this step included the NYHA ≥ III wording for cisplatin ineligibility and the dd-MVAC cycle range (3–6).
  - Durvalumab under 30 kg (20 mg/kg) was added.
  - The EU indication of EV + pembrolizumab in first line was restricted to patients eligible for platinum.
  - Nivolumab maintenance runs up to 24 months from the first dose.
  - Erdafitinib phosphate steps and the epirubicin and BCG Fachinformation wording were corrected.
- *Tables:* an editor shortened the table cells and moved explanations to support and cautions. A script compared each file with its verified version and refused any change that lost a number.
- *Review findings fixed in the protocols:* the question reviewers found four further points, all fixed:
  - abiraterone is taken fasting (no food 2 h before and 1 h after, EU SmPC; the fixed niraparib/abiraterone tablet keeps its own label wording);
  - primary G-CSF with cabazitaxel is *recommended* for high-risk patients, not mandatory;
  - Lu-PSMA is stopped if a further dose reduction would be needed;
  - the mesna rule is sourced to the mesna Fachinformation.
- *Non-EU sources:* where the EU text was not returned, US label wording was used. This applies to the erdafitinib step above 10 mg/dl, pembrolizumab 400 mg every 6 weeks in the adjuvant part of EV-303, and the weight-based durvalumab dose (HCP page).
- *Left out:* chemoradiation for urethral and penile squamous cell carcinoma has no protocol entry, because its doses could not be confirmed.

**Radiotherapy schemes (`data/radiotherapy.json`, 42 schemes).** The same two steps, research and independent verification, ran per group. Validation rejects a phase whose total dose is not dose per fraction × fractions; continuous low-dose-rate brachytherapy (permanent seeds or a temporary LDR/PDR implant) has a total dose only. An independent radiation oncologist re-checked every scheme and changed one dose statement: the salvage range for the prostate bed is 64–70 Gy, not 64–72 Gy (70 Gy was no better than 64 Gy in SAKK 09/10, with more late bowel toxicity). The verifiers also corrected evidence and toxicity statements, among them the PACE-B late urinary toxicity (cumulative grade 2+ 26.9% vs 18.3%, not the year-5 prevalence), the BC2001 late toxicity figures, BCON's 10-year result, the STAMPEDE toxicity figures, the ASTRO bone metastasis update year (2017) and the vertebral fracture rate after spine SBRT (11% vs 17%). The brain metastasis scheme no longer offers 15 Gy single fraction for 3–4 cm lesions, where multifraction stereotactic radiotherapy is recommended. Seminoma stage IIB is 30 Gy to the dog-leg field plus a 6 Gy nodal boost, consistent with the corrected cases. Statements that could not be confirmed were removed rather than kept.

**New questions (82 in total).** Each batch was written by one author and checked by an independent specialist: a urologist, plus a clinical pharmacist for drug questions or a radiation oncologist for radiotherapy questions. A script then checked the rules:
- one step with four or five options, exactly one scoring 10;
- critical flags only on wrong options;
- new, unique patient names;
- a guideline reference, plus EU product information for drug questions;
- no authors;
- the full game validation.

None of the 62 questions on protocols, side effects, incontinence and priapism was dropped; reviewers fixed 35 of them. Examples:
- a phenylephrine timeline that did not add up;
- a cystoscopic clock position on the wrong side;
- a CTCAE audiogram grade;
- a mesh exposure size that sat exactly on a threshold;
- split-dose cisplatin, which was penalised in one protocol question although it is the right answer in another;
- the EU fasting wording for abiraterone.

Protocol questions use the doses of the protocol page; reviewers recomputed every body surface area, mg/kg dose, cap and Calvert dose. The 20 radiotherapy questions were checked against the radiotherapy page by an independent radiation oncologist; none was dropped and 16 were fixed. Examples: 60 Gy in 20 fractions is an equivalent *alternative* to 76–78 Gy, not a proven equivalent; cT2c counts as a high-risk feature; SPPORT never tested pelvic radiotherapy without ADT; a vignette with IPSS 9 described as unremarkable now has IPSS 6; and a denosumab dose for skeletal events in hormone-sensitive disease was replaced by the osteoporosis dose, since the higher dose is indicated only in castration-resistant disease.

**The attending's hints (`data/attending-hints.json`, one per decision).** One author per batch wrote a hint for every decision; an independent urologist (a radiation oncologist for the 20 radiotherapy questions) reviewed each hint for:
- giveaways (a word that appears only in the keyed option);
- correctness;
- concreteness;
- language.

A script rejects hints that name an option letter, quote any option, announce the answer, name authors or fall outside 40–360 characters. Reviewers rewrote 83 hints, most of them for giveaways; 4 of them belong to the radiotherapy questions, which were only shortened. The cartoon tests check that every decision has a hint and that no hint quotes an option.

**Corrections found while writing hints.** The hint reviewers reported doubts about four existing cases; three were confirmed and corrected through the correction layer:
- uretero-ileal strictures are more common on the left (bank-uro-rek-00012);
- citrate 2.2 mmol/d is below the EAU threshold, so the explanation now asks for a repeat collection (bank-uro-lit-00003);
- a vignette now matches its explanation (bank-uro-rek-00013).

EV + pembrolizumab in an authored case now allows ECOG 0–2, as in EV-302. Eponyms such as Gleason, Galsky, Calvert and Clavien-Dindo remain as standard terms; the no-authors rule targets citations and mentions of authors or articles.

**Schema links.** Two urologists mapped the 18 priapism and incontinence questions to the anatomy schemas without seeing each other's work, and a judge reconciled them: 17 links, 12 of them agreed by both.

**Code review.** A code review of the branch found ten points, all fixed: a duty without cases is no longer offered and cannot crash the game; the day clinic and radiotherapy duties have their own colour, with a grey fallback; long whiteboard labels are squeezed to the board; the protocol tabs use `aria-pressed`; practice questions are deduplicated and looked up in the table on screen; the attending's lines follow the time of day in a mixed rotation; the warning bubble's tail has the warning colour; validation rejects duplicate question links, numeric regimen ids and a regimen id used in both protocol files; and the importer accepts all six duties. A brachytherapy phase without fractions now reads *continuous (implant)* instead of *permanent implant*, because a temporary LDR/PDR implant for penile cancer has no fractions either.

## Oncology update, no authors in the game, save and load — 6–7 October 2026

**Sources.** The update uses the knowuro flowcharts 2026 (EAU-based; CC BY-NC-ND 4.0) for bladder, prostate, kidney, UTUC, testicular, penile and urethral cancer. Only their facts are used; nothing is copied or redrawn. Some flowcharts date from spring 2026, so approval statements were checked on the web on 6 October 2026. The checks covered:
- perioperative EV + pembrolizumab: EU approval in June 2026 for cisplatin-ineligible patients, a positive CHMP opinion on 18 September 2026 for all patients, FDA approval in July 2026;
- 177Lu-PSMA in the EU only after an ARPI and a taxane;
- durvalumab (NIAGARA) and erdafitinib approved in the EU.

**Audit of existing cases.** For each of five tumour groups, one auditor gave a verdict on every case (169 in total), and an independent skeptic tried to refute every finding.
- 45 cases were flagged; 43 findings were confirmed.
- Two were refuted. A bladder case had been called wrong because the flowchart lists EV + pembrolizumab as 'approval pending', but the EU approved it on 24 June 2026, so the case is right. A salvage-prostatectomy case fits the EAU selection criteria.
- A third proposal was overruled on the web check: making 177Lu-PSMA an option before a taxane is not correct in the EU.
- Examples of confirmed corrections:
  - CHAARTED high volume needs a lesion outside the spine and pelvis; the vignette had defined low volume.
  - Early detection is offered at a life expectancy over 15 years.
  - The PSA-density thresholds for PI-RADS 3 are 0.10 and 0.20.
  - A 2.4 cm node is N2, stage IIB, not IIA.
  - A stage IIB seminoma field gets 30 Gy plus a 6 Gy boost, not a 36 Gy field.
  - UTUC follow-up after kidney-sparing surgery relies on CT urography.
  - The pN2/pN3 threshold for pelvic dissection in penile cancer is three or more nodes or extranodal extension.
  - Duplicated sentences were removed.
- Each correction was written by a medical editor and then checked by an independent urologist and translator. Answer keys and scores were not changed; imported questions keep 0/10 scoring.

**Correction layer.** `data/case-updates.json` holds 68 entries:
- 43 medical updates, shown in the game with an *Updated* badge, reason and sources;
- 25 editorial ones, which change wording only.
Each change replaces a whole field, guarded by its exact old value, or one passage that must occur exactly once. If the text drifts, for example after a re-import, validation stops. The corrected case passes the same rules as every case.

**No authors in the game.**
- The build removes 648 author citations from play texts in three languages, for example (Dieckmann et al. 2025). Guideline citations such as (EAU 2026, 7.1) stay.
- 105 passages in 24 cases that named authors or “the article” were rewritten. Each was reviewed for unchanged meaning and equivalent DE/EN/ES.
- The catalog lists source titles without citation strings.
- Validation rejects any remaining mention, and a cartoon test fails on the previous catalog.

**New cases.** 20 multi-step oncology cases, with 58 decisions in DE/EN/ES:
- 5 bladder, 4 prostate, 3 testis, 5 kidney/UTUC, 3 penile/urethral.
- Each was drafted from a skeptic-checked gap list and run through the game validation plus extra rules: three options scored 10/3/0, new unique names, EAU and flowchart references, valid schema links.
- An independent urologist reviewer then checked each case and fixed what it found, for example the TNM boundary of regional pelvic nodes, the Galsky criteria, the EORTC limit for a single instillation and a dose-reduced first cycle in life-threatening germ cell cancer.
- Three near-identical patient names were changed.
- The library now has 317 cases (50 authored, 267 imported), 415 decisions and 1,556 options.

**Save and load.** The progress export is now a full game file (version 3) that *Load game file* reads back; older version-2 logbooks also load. It is described under *Save and continue* in the README.
- The file is untrusted input and passes the same checks as local storage, which are now shared code.
- A summary dialog comes before any change.
- Loading merges without losing or double-counting progress.
- A browser run covered play, save, clearing the browser, load and carrying on (also at 360 px). The Python analyser reads the new file.
- **Adversarial review.** Three reviewers attacked the feature in Chromium over http and file://:
  - untrusted input, with about 55 crafted files;
  - state correctness, against the previous release;
  - interface and wording in EN, DE and ES.

  A skeptic re-ran every report; 11 defects were confirmed and 6 refuted. All 11 are fixed:
  - Unknown fields in a loaded shift were kept and stored, which a 5 MB file could use to stop saving or to freeze clicks. A shift is now rebuilt from known fields only, and joker marks and morning reports are kept only if they fit.
  - Loading an older copy of the same shift logged an attempt twice and counted shifts and morning reports twice. Log entries now carry their shift and count once per patient. Counted shifts are remembered, and the copy that got further is kept.
  - A finished shift in the file replaced an open shift on the device. Now an open shift wins, and the dialog labels finished shifts.
  - Counters and the rank accepted absurd values. They are capped, and the rank is recalculated from the logbook.
  - The avatar was lost without a player name.
  - Progress without a logbook (stickers, bookmarks) could not be saved or loaded.
  - Singular forms were missing (“1 logbook entries”).
  - Focus was lost after loading.
  - On small phones the dialog opened scrolled to the bottom.
  - The download was named “logbook”.
  - The German help note was imprecise.

  The reviewers' scripts were run again on the fixed code and confirm each fix. The cartoon tests grew to 35; they cover the shift choice, the shift identity of log entries and the rebuilt shift.

**Checks.** All Python, engine and cartoon tests pass. The validation reports 317 valid cases, 43 of them updated. A browser run of new cases and corrected cases shows no console errors and no horizontal overflow.

## Integrity review after the schema release — 5 October 2026

The schema work had been interrupted several times (sub-agents stopped by rate limits, a rebuild that briefly lost CRLF endings, parallel edits). The merged state was therefore checked again:

- **Reproduction:** on a fresh clone of the merge commit, `validate`, all Python, engine and cartoon tests, `build` and `package` passed. A fresh build produced byte-identical `catalog.js` and `standalone.html` (apart from line endings). All 45 SHA256 entries matched, line endings were consistent, and no skip guards or debugging leftovers remained.
- **Review:** four independent reviewers covered:
  - app runtime in a real browser;
  - build and data;
  - artefacts of the interrupted edits in all 15 schemas, which were parsed, rendered and hit-tested part by part;
  - tests, CSS and translations.

  A separate skeptic tried to refute each finding. The artefact review found nothing. Eight findings were confirmed, all in code written for the release and none caused by the interruptions. All eight are fixed:
  1. The SVG safety check matched text patterns and could be bypassed (an event handler after a `>` inside an attribute value, or an unterminated `<img>`). `manage.py` now parses each schema as XML and whitelists the parsed elements and attributes. It rejects angle brackets, `url()` and `javascript:` in values, as well as comments and declarations. The cartoon test applies an equivalent strict grammar. The shipped schemas were clean before and after.
  2. A drawn structure written with single quotes escaped the "every structure has a label" check, and tapping it in the quiz froze the round. Structures are now read from the parsed tree, and the quiz ignores taps on anything that is not a listed structure.
  3. Malformed entries in `schemas.json` or `case-schemas.json` crashed `validate` with a Python traceback. They now produce a normal validation error.
  4. On laptop screens (1024×600 to 1366×657) the quiz verdict and its *Next* button were below the visible part of the dialog. The drawing now shrinks to fit, the fact a tap reveals sits directly under the drawing, and focus scrolls the button into view.
  5. The added *Atlas* menu entry made the header overflow at 761–816 px and at 424–432 px. The header now wraps in those ranges. A scan from 300 to 1100 px in EN, DE and ES shows no overflow on the introduction, library and atlas. The only exception is a 4-pixel overflow of the German introduction at 300 px, which predates the release.
  6. Keyboard focus was invisible on glowing (★) structures. Focus and selection now pause the glow and show a ring.
  7. On phones the splash punchline ran off the right edge. It is now kept on screen.
  8. The atlas said "1 Fälle". It now uses the singular.
- **Tests:** each fix has a regression test that fails on the previous code and passes now: 10 bypass payloads plus malformed entries in Python, and the strict SVG grammar, the quiz with an unknown tap and the singular label in the cartoon suite. Browser re-check (Chromium): the quiz verdict and button were visible at 1366×657, 1280×720 and 1024×600; the splash stayed inside at 320, 375 and 414 px; a Tab-focused glowing structure showed a distinct ring; no console errors.
- **Re-check of the fixes (6 October 2026):** two further agents attacked the merged fixes.
  - The validator agent tried 15 bypasses (CDATA, comments, namespaced and duplicate attributes, encoded brackets, quotes inside values and others). Every payload was rejected or rendered inert, and all 15 schemas still render unchanged.
  - The interface agent confirmed fixes 4, 5 and 7 at 14 screen sizes. It found five side effects of moving the fact under the drawing and of the new focus ring:
    - on phones a fact opened from a legend chip could sit under the sticky header;
    - the legend jumped under the finger;
    - in the quiz the focus ring replaced the green or red verdict;
    - a focused structure stayed dimmed while another one was selected;
    - the legend touched the note.
  - All five are fixed. A fact opened from the drawing still appears under the drawing, but a fact opened from a chip appears under the legend, as before the release, and any shift of the legend is scrolled back. Scrolling to a fact on the page now stops below the sticky header. A focused quiz answer keeps its verdict colour inside the ring.
  - The interface agent's browser scripts were run again: 0 of 11 chip taps move the chip, and the fact is visible after a tap on the drawing at every size. A cartoon test pins the CSS order.

## Teaching schemas, anatomy atlas and urine splash — 5 October 2026

- **Feedback:** confetti now appears only for correct answers, streak milestones and promotions. Previously a sticker earned after a missed case also fired confetti; stickers now show as a toast. A wrong answer in a case, in the chief's quiz or in the anatomy quiz triggers a cartoon urine splash: droplets, a puddle, a random word such as "Platsch!" and a short splash sound. Reduced-motion settings suppress both splash and confetti.
- **Schemas:** 15 cartoon teaching drawings with 189 tappable structures, drawn as inline SVG for this game: urinary tract overview, kidney section with envelopes, obstructed kidney with stent and nephrostomy, kidney transplant, bladder wall with T stages, urinary diversion (conduit and neobladder), neural control of micturition, prostate zones, male urethra and penis, female pelvis, pelvic side wall, scrotum and inguinal canal, retroperitoneal lymph nodes, hypothalamic-pituitary-testicular axis and VUR grades. No external or photographic images are used.
- **Drawing and review:**
  - An illustrator agent drew each schema in a render-and-check loop.
  - A separate anatomy reviewer then checked relations, labels, notes, all three translations and tap size, and fixed what it found.
  - An independent skeptic re-checked the result without editing it, and its findings were then applied and confirmed in renders.
  - Examples of what was fixed:
    - Pelvic side wall: the ureter had been painted behind the common iliac artery.
    - Prostate: the urethra was interrupted at the bulbomembranous junction.
    - Urinary tract overview: the left renal artery ran into the adrenal.
    - Scrotum: the spermatic cord could not be tapped.
    - Neobladder: the retroperitoneal ureters ran in front of the ileum.
    - Female pelvis: the pubourethral ligament merged with the levator.
    - VUR grades: drawn Roman numerals gave away the quiz answer.
    - Urinary diversion: a Spanish note said "through the rectum" instead of "through the rectus muscle".
- **Safety:** the build accepts only plain shapes (`g`, `path`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`) with listed attributes. It rejects text, scripts, event handlers, links and `url()`. Every drawn structure needs a label and a note in EN, DE and ES, and every highlighted structure must exist.
- **Tap size:** a browser hit test every 2 viewBox units measured the largest free disc of each structure. Thin structures received invisible wider hit strokes. All structures have a free diameter of at least 16 units except the ureter underneath the stent in the obstructed-kidney schema, which has 12 units because the stent really runs inside it. On phones the drawing now uses nearly the full width: 284 instead of 222 pixels at a 360-pixel viewport.
- **Case links:**
  - Two independent classifiers chose one schema, or none, for each of the 297 cases. One read the decision first, the other the anatomy first. They agreed on 286 cases, and a judge decided the other 11.
  - The rule was to add a picture only where it explains the correct answer. Questions on drugs, laboratory values, counselling, imaging choice or guidelines get none.
  - Result: 133 cases are linked and 164 have no schema.
  - For each linked case, two independent pickers then chose the structures that glow. A case keeps only the structures both chose: 1 structure in 20 cases, 2 in 76, 3 in 35 and 4 in 2. The two pickers chose identical sets for 98 cases and overlapping sets for the rest, so no judge was needed.
- **Atlas and quiz:** the *Atlas* page lists all schemas. *Find the structure* asks for five different structures. A right tap gives small confetti and a wrong tap the splash, and 5 of 5 earns the *Anatomy ace* sticker. Screen-reader labels in the quiz do not name the structures, and the quiz has no legend.
- **Checks:** `manage.py validate`, `build` and `package` passed. 34 Python tests, 41 engine tests and 29 cartoon tests passed. Three new cartoon tests cover:
  - schema safety and coverage: drawn and explained structures match, links are valid, every schema explains at least one case, and at least 40 % of cases are linked;
  - glowing structures and the legend order, and that the quiz markup never reveals names;
  - quiz rounds, one-time scoring per round, the splash on a wrong tap and the perfect-run reward.
- **Browser** (Chromium, localhost, German, 1280 and 360 pixels):
  - After the last decision of a linked case, the schema appeared and exactly the linked structures glowed.
  - Tapping a structure showed its note. The atlas listed every schema.
  - The quiz showed no legend, and a right tap answered "Richtig!".
  - There was no horizontal overflow and there were no console errors.

The schemas, their notes and the case links were checked by AI agents and by automated tests, **not by a urologist**. They are simplified teaching drawings, not to scale, and need specialist review before formal teaching.

## Duties: night shift, tumour board, clinic and elective list — 5 October 2026

Sessions previously drew two cases from each department. A night shift could therefore contain oncology follow-up or elective operative technique. Every case now has one `duty`, and a session draws only that duty.

- **Rules:** classification follows the decision the question asks for. *Night* means acute situations that must be handled now. *Board* means oncological staging and treatment decisions. *Clinic* means outpatient work-up, counselling and follow-up, including oncology. *Elective* means planned surgery and endoscopy. Explicit tie-breaks cover oncology plus technique (elective), oncology plus follow-up (clinic), acute complications after elective surgery (night) and injuries found during another specialty's operation (night).
- **Classification:** two independent classifiers, one question-first and one setting-first, assigned all 297 cases. They agreed on 288; a judge resolved the other nine.
- **Review:** the night pool and all boundary groups were read in full: stones and infections outside the night shift, operative cases in the tumour board, and intraoperative complications. One change was made: `bank-uro-fun-00011`, autonomic dysreflexia during urodynamics, moved from night to clinic because it happens in the urodynamics laboratory.
- **Result:** night 52, tumour board 90, clinic 100, elective 55. Every duty has enough cases for several ten-case sessions.
- **Checks:** validation; 32 Python tests (duty validation and `schedule --duty` added); 41 engine tests (duty scheduling draws only its duty, is reproducible, rotates topics, rejects unknown duties, and every case has a duty); 26 cartoon tests (duty texts in EN/DE/ES, awake attending in daytime, conference room with every case as a folder and no doors).
- **Browser:** Chromium, DE. Each duty started with its own clock (22:00, 15:30, 08:00, 07:30) and drew ten cases of that duty only. The library's tumour-board filter showed 90 cases. There was no horizontal overflow at 360 pixels and no console errors.

The duty assignment is an educational sorting of the cases, not a clinical triage rule.

## Patient names for imported cases — 5 October 2026

The 267 imported questions previously showed numbered teaching identifiers (`Uro-001` …). They now show fictional names from `data/patient-names.json`, which the importer applies.

- **Classification:** two independent classifiers read every vignette in DE, EN and ES, one German-first and one English-first. They recorded the number of patients, sex and age band using only explicit words or sex-specific anatomy, never disease statistics. They agreed on 265 of 267 cases; a judge resolved the remaining two.
- **Review:** a review of the agreed results found two shared blind spots, and four cases were corrected:
  - `uro-hod-00019` (residual-mass resection after BEP in the testicular-cancer bank) is male.
  - `uro-op-00103` and `uro-op-00104` (steps of a radical prostatectomy) and `uro-rek-00014` (kidney transplantation) describe one patient on the table.
- **Text-pattern cross-check:** a regular-expression check in all three languages found no case whose recorded sex contradicts the text. The cases it flagged were partners mentioned in the text, generic masculine nouns (*Patient*, *Raucher*, *Motorradfahrer*, *el niño*), "no pregnancy" or anatomy the patterns did not cover. None needed a change.
- **Result:** 252 single patients (173 male, 37 female, 42 of unknown sex) and 14 vignettes with several patients (7 all male, 2 all female, 5 mixed or unstated). One question has no patient: a departmental meeting, shown with a translated label. Patients of unknown sex get gender-neutral German first names and German surnames.
- **Names:** all 297 case names are unique. First names suit the stated age, and first name and surname come from the same naming culture. The names avoid the story patients' and the cast's surnames, famous people, medical puns and surnames that read like first names.
- **Checks:** validation, 30 Python tests, 40 engine tests and 24 cartoon tests pass. The import test confirms the importer reproduces every imported case, names included. The new cartoon test checks name uniqueness, agreement with the mapping file, sex consistency with English sex words, and the absence of stubble on female and child portraits.

The 30 story patients also record `sex` now, from the pronouns in their texts or, without pronouns, from the original author's name choice; *Alex Morgan* stays unspecified. Three of them (Clara Hoffmann, Elena Fischer, Sofia Martín) previously had portraits with stubble; that is fixed.

The names are fictional display labels. They add no clinical information and were not reviewed clinically.

## Game-feel and learning update — 5 October 2026

Software changes only; **no case text, answer key, score, explanation or reference was changed**. `data/*.json` and the generated catalogue content are identical to the 297-case expansion; `assets/catalog.js` differs only in line endings after a rebuild on Linux.

- Interface: correct/wrong marking after each answer, the preferred answer's own rationale on a miss, a collapsible explanation of every option (chart, debrief and logbook review), the nurse's joker, streaks, career ranks from best-per-case XP, 13 stickers, rematch, specialty training, practice from the library filter, a five-question quick round and keyboard answers.
- Comedy: 6 more correct-answer lines, 4 more coffee lines, 8 lines for wrong source answers, 6 joker lines, 6 streak lines, 9 ranks with jokes, 4 promotion lines and 13 sticker texts, each in EN/DE/ES. Unsafe-choice feedback was left unchanged.
- Checks: `manage.py validate` and `build` passed; **29 Python tests**, **40 engine tests** and **23 cartoon tests** passed. The new cartoon tests cover translation parity of all interface labels and story structures, the joker (never strikes the correct answer, costs exactly five game minutes, leaves answers and points untouched, cannot be used twice or after answering, is reproducible per session seed) and streak/miss comment selection.
- Browser (Chromium, localhost): German play-through with joker, keyboard answers, marking, explanations, debrief, a ten-case perfect session with promotion, streak and perfect-session stickers, a perfect chief's quiz by keyboard, specialty training (10 urolithiasis cases), rematch of a missed case and the progress page in DE/EN/ES. A session saved by the previous release loaded and resumed. No console errors.
- At 360 and 375 pixels there was no document-level horizontal overflow on the introduction, library, play view, feedback or progress page. The previous release overflowed by 17 pixels at 360 pixels in German (navigation and department cards); this is fixed.

## Current 297-case expansion — 5 October 2026

The current source library contains **297 unique case IDs**: 30 existing three-step story cases and all 267 main-bank questions from `Urofragen-GitHub-DE-EN-ES-2026-10-04.zip`, each imported once. There are **357 steps and 1,382 options**. All case content is provided in English, German and Spanish.

| Department | Total cases |
| --- | ---: |
| Emergency | 32 |
| Ward | 29 |
| Clinic | 139 |
| Endoscopy | 28 |
| Theatre | 69 |

Source and provenance checks:

- All 267 source IDs are unique. Normalized vignette, lead-in, option text and correct-answer comparisons found no exact repeated questions in DE, EN or ES. This does not claim semantic duplicate detection.
- All 16 main-bank specialties are represented. Separate CME, update and generated HTML copies are not counted again.
- Each imported question retains its original medical text, answer key, option rationale, core explanation and teaching point in all three languages.
- 223 imported questions have four options and 44 have five, each with exactly one correct answer. The 30 existing cases retain three decisions with three choices each.
- Source status remains 257 published and 10 draft. Evidence flags remain 32 true and 235 false; 29 flagged questions are published and 3 are drafts.
- 51 source approvals explicitly cover German only. The other 216 questions have no imported sign-off: 206 pending independent review and 10 drafts without a clinical review status. No English or Spanish approval is inferred.
- Missing or ambiguous ages and vital signs remain unrecorded. Teaching identifiers do not claim that every vignette describes one patient.
- The provenance snapshot, source mapping, original archive hash and import manifest are included. The importer reads JSON only and never runs archive scripts. `--check` compares the existing import without rewriting files.

Software checks completed for this expansion:

- Source validation and build succeeded with the mixed one-step/three-step library, variable option counts and source metadata.
- **29 Python tests passed**: 19 automation tests and 10 importer regression tests. These cover mixed-format validation, UTF-8 preservation, unknown ages/vitals, variable choices and steps, exact source answer/translation mapping, duplicate rejection, complete coverage and inert archive scripts.
- **60 JavaScript tests/subtests passed** across the engine and cartoon suites, including the expanded catalogue and existing cast/game mechanics.
- Source cases use 10/0 knowledge points, without invented clinical safety-error classifications; one-step maxima are 10 and three-step story maxima are 30. Case display is normalized to 100. Progress export and CSV analysis follow each case's actual answer count.
- The expanded library uses translated topic filters and pagination of 18 cases per page.

Current browser and integration checks completed:

- The 297-case introduction and original cartoon cast render correctly. Library pagination, specialty filtering and original-question-ID search work; single results use the singular case label.
- A five-option imported case (`bank-uro-hod-00044`) was completed in German using original answer E. Its debrief and report showed 100%, and the chief's five-option quiz finished at 1/1. Both results survived reload.
- English case text and all five choices were inspected. Switching into Spanish during the same case preserved the question and choice order. An incorrect answer showed the original Spanish rationale, the preferred answer and a localized knowledge-feedback title.
- Source evidence notes and original citations are visible. The draft OP case `bank-uro-op-00101` shows its draft label and four answers; missing age and extra vital signs remain absent. Language-specific source approval is displayed without inferring approval.
- At a 360-pixel viewport, the source case, evidence details, search and pagination had no document-level horizontal overflow. The cartoon room retains its own horizontal scrolling panel. Temporary viewport overrides were reset.
- The rebuilt `standalone.html` was opened over localhost and displayed all 297 cases, the cartoon introduction and language controls with zero external script elements and no browser console errors.
- Concrete engine-to-Python export integration produced two CSV rows: original answer E in the five-choice case scored 10/10 (100%); an incorrect answer in a four-choice case scored 0/10 (0%). Each row contained exactly one decision. Engine save/restore checks passed. Browser download-event observation was unavailable in this test browser; the export data format and Python conversion were checked directly.
- `import_urofragen.py --check` matched all 267 imported cases and all three language versions against the actual supplied archive.
- The Python daily-shift example was regenerated for 5 October 2026 with 10 distinct cases, two per department.

**Final ZIP verification passed:** 40 delivered files plus SHA256.json; exact archive file list and all hashes matched the project. All 297 case IDs, 357 decisions, 1,382 choices, 267 original source question IDs, source content hashes and complete DE/EN/ES texts matched. The 30 earlier case objects and three supplied classic games remain unchanged. The playable catalogue and all six scripts/two stylesheets are embedded accurately in the standalone file; no temporary caches or external runtime assets are included.

Related EAU guideline index links were checked as primary reference metadata. This expansion did not newly validate all 267 imported medical questions, translations, evidence classifications or drug regimens against current clinical guidance. Software tests and imported German approvals do not certify the complete game or its other languages.

## Previous 30-case cartoon revision — earlier on 5 October 2026

The following checks were completed before the question-bank expansion:

- 30 story cases, six per department, with 90 steps and 270 options in EN/DE/ES.
- 24 linked primary clinical references with editorial check dates; source structure and asset validation passed.
- 11 Python automation tests, 36 JavaScript engine tests/subtests and 18 cartoon regression tests passed.
- Engine exports from all five departments were analysed with Python into 15 verified CSV decision rows.
- Localhost browser checks passed for the introduction, department filters, German case play, switching to Spanish during a case, completion, reload persistence, progress reset and the Python-generated daily-shift import.
- Cartoon play-through covered avatar selection, illustrated briefing, nurse advice, coffee accounting, three clinical decisions, character feedback and the morning-report challenge. The challenge survived reload without altering case scores. Illustrated department doors responded to keyboard activation; no browser errors were recorded.
- Original localized cast names, German and Spanish comedy, desktop rooms and mobile dialogue were inspected. At 360 pixels, the introduction and game had no document-level horizontal overflow; the room scrolled within its own panel.
- The standalone builder embedded both stylesheets, favicon, translations, artwork, comedy, catalogue and game scripts. The single-file introduction rendered over localhost without browser errors.

Direct `file://` browser testing was unavailable because the test browser accepts HTTP/HTTPS only. Single-file construction was checked automatically; direct offline launch should be checked in the recipient's own browser. This limitation is unchanged by the expansion.

These records describe software verification, not clinical accuracy, translation certification or suitability for formal medical teaching. The supplied games in `classic/` remain unchanged and their clinical logic was not systematically audited.
