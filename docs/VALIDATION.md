# Validation record

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
