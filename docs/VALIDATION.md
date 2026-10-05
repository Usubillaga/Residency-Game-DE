# Validation record

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
