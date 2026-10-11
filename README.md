# Night Shift Academy

> **Residency-Game-DE – Rollenspiel als Assistenzärztin oder Assistenzarzt der Urologie.** Öffne `standalone.html` im Browser, wähle **DE** und tritt deinen ersten Nachtdienst an.

A cartoon hospital comedy and urology decision game in **English, German and Spanish**, with **exactly 500 scored questions in 402 playable cases**: 30 original three-decision stories (90 questions), 20 oncology stories (58 questions), all 267 imported main-bank questions, 35 selected supplementary clinical questions and **50 new urological anatomy questions**. Choose an avatar, meet the cast, navigate illustrated departments, collect coffee quips and face the chief's morning-report quiz.

All 267 imported source questions remain present, with their original snapshots and the existing correction layer. The 30 original stories and 20 oncology stories remain present. It covers **16 source specialties** across five game departments. The supplied classic HTML games remain unchanged in `classic/`.

![Introduction preview](docs/preview.jpg)

## Start playing

1. Extract the ZIP to a folder.
2. Open **`standalone.html`** in a current browser. The complete game is embedded in one file and needs no installation or server.
3. Choose English, Deutsch or Español, select your avatar and start a department shift or mixed shift.
4. Browse the library by department, specialty or search. It shows **18 cases per page**.
5. Review each explanation and finish with the chief's quiz. Save your game file to carry on later or on another device (*Load game file* on the progress page).

`index.html` offers the same game with separate local assets. Keep the complete project for the original games, editable case data, import provenance and Python tools.

### English quick start

Open `standalone.html`, choose **English**, meet the cast and start a shift. Story cases contain three decisions, the new oncology cases two or three; the new single questions and the imported question-bank cases contain one question with four or five choices. Filter by specialty to focus your practice. The nurse offers an explicitly requested joker, coffee adds workplace comedy, and the chief gives a separate final quiz. Save your game file to continue later or on another device; the logbook inside can be analysed with Python.

### Deutsch – Schnellstart

Öffne `standalone.html`, wähle **Deutsch** und starte eine Schicht. Die aktive Bank enthält **genau 500 bewertete Fragen in 402 Fällen**: 30 ursprüngliche Geschichten mit 90 Entscheidungen, 20 Onkologie-Geschichten mit 58 Entscheidungen, sämtliche 267 importierten Fragen, 35 ausgewählte klinische Zusatzfragen und **50 neue urologische Anatomiefragen**. Alle 50 Anatomiefragen sind mit einem Eingriff (31) oder klinischen Fall (19) verbunden, etwa PCNL, HoLEP, Prostatektomie oder Hodentorsion. In der Bibliothek kannst du das Fachgebiet *Urologische Anatomie* auswählen. Entscheide selbst; Erklärungen und markierte Zeichnungen erscheinen nach der Antwort. Janas Joker bleibt auf ausdrücklichen Wunsch verfügbar. Cartoonstil, Dialoge, Kaffeepausen und Abschlussquiz bleiben erhalten. Speichere deinen Spielstand als Datei, um später oder auf einem anderen Gerät weiterzuspielen.

**Neu in diesem Update:** Nach jeder Antwort siehst du, welche Option richtig war und warum. „Alle Antworten erklärt“ begründet jede Option. Janas Joker streicht eine falsche Antwort. Richtige Serien bringen Sprüche und Konfetti. Eine Karriereleiter führt von Famulant:in bis zur Legende des Nachtdienstes, und ein Sticker-Album macht Fortschritt sichtbar. *Revanche* wiederholt deine Fehler, *Fachgebiete* zeigen deine Schwachstellen mit Trainingsknopf, und die *Blitzrunde* bietet fünf schnelle Fragen. Tastatur: A–E oder 1–5 wählt, Enter geht weiter.

### Español – Inicio rápido

Abre `standalone.html`, elige **Español** e inicia una guardia. Hay **exactamente 500 preguntas puntuables en 402 casos**: 30 historias originales con 90 decisiones, 20 historias oncológicas con 58 decisiones, las 267 preguntas importadas, 35 preguntas clínicas complementarias seleccionadas y **50 preguntas nuevas de anatomía urológica**. Las 50 preguntas anatómicas tienen contexto quirúrgico (31) o clínico (19). Filtra por *Anatomía urológica*, decide por ti mismo y consulta después las explicaciones y los dibujos. El comodín de enfermería sigue disponible si lo pides. Se conservan los dibujos, el humor y las pausas de café. Guarda tu partida para continuar más tarde o en otro dispositivo.

## Case library

| Department | Authored cases | Imported cases | Total | Scored questions |
| --- | ---: | ---: | ---: | ---: |
| Emergency | 9 | 26 | 35 | 51 |
| Ward | 10 | 23 | 33 | 45 |
| Clinic | 68 | 133 | 201 | 243 |
| Endoscopy | 15 | 22 | 37 | 53 |
| Theatre | 33 | 63 | 96 | 108 |
| **All departments** | **135** | **267** | **402** | **500** |

The active bank contains **500 scored decisions and 1,927 answer options**. One decision step counts as one question; a three-step story counts as three. The chief's quiz repeats bank questions, and atlas taps are separate game mechanics, so neither adds to the total. `data/question-contract.json` enforces the count at validation and build time and rejects exact duplicate question content in each language.

**71 supplementary questions are archived**, rather than deleted, in `data/archive/supplemental-questions.json`. Their completed logbook entries, XP, bookmarks and explanations remain reviewable and exportable. They do not enter the library, schedules, rematches or protocol practice. An unfinished old shift that includes archived questions cannot be resumed in this version; completed entries are retained. Keep the previous version to finish that old shift.

**No learning objectives are shown or shipped in the browser catalog.** Original source objectives remain only in the editable provenance data. There is no automatic goal-based hint; the nurse and consultant jokers must be requested. Case-wide correction notes, evidence notes and highlighted schemas wait until the final answer. See [docs/FRAGENBANK_500.md](docs/FRAGENBANK_500.md) for the source-backed content review and anatomy coverage.

The source specialties are andrology, functional urology, testicular cancer, infections, paediatric urology, muscle-invasive and non-muscle-invasive bladder cancer, renal cancer, operative urology, penile cancer, prostate cancer, reconstruction, trauma, urethral cancer, stones and upper-tract urothelial cancer. Department allocation follows the clinical task in each vignette; the source's oncology emphasis explains the larger clinic collection.

Imported cases show fictional patient names from `data/patient-names.json`. The case text alone determines sex, number of patients and age band. Two independent classifications of all 267 vignettes agreed on 265 cases; a judge resolved the other two. A review then corrected four more: a testicular-cancer case is male, and three intraoperative technique questions have a patient on the table. When the text does not state the sex (42 cases), the patient gets a gender-neutral first name. A vignette that compares several patients lists one surname per patient, for example *Weiß & Scholl*. The one question without any patient, a departmental meeting, shows a translated label and the head of department's portrait. Names are unique, age-appropriate and culturally consistent. They avoid the surnames of the story patients and the cast, famous people and medical puns. The 30 story patients now also record `sex`, taken from the pronouns in their texts or, where the text has none, from the original author's name choice; *Alex Morgan* stays unspecified. Portraits never give women or children stubble, and patients aged 75 or older get grey hair. No additional vital signs are invented. Missing or ambiguous ages remain unrecorded, and a case may have `patient.age: null` and `vitals: null`.

## Duties

A session no longer mixes every department. You choose a **duty**, and the session draws only that duty's cases, rotating through topics:

| Duty | Clock starts | Cases | Content |
| --- | ---: | ---: | --- |
| 🌙 Night shift (*Nachtdienst*) | 22:00 | 56 | Emergencies only: colic and obstructed or infected kidneys, retention, bleeding and clot retention, trauma, torsion, priapism, Fournier, acute infections, acute ward complications and emergency or consult surgery |
| 🎗️ Tumour board (*Tumorboard*) | Wed 15:30 | 103 | Oncological staging and treatment decisions, systemic and salvage therapy, metastatic disease, residual tumour |
| 🩺 Clinic (*Sprechstunde*) | 08:00 | 132 | Outpatient work-up, counselling and follow-up, including cancer follow-up, andrology, functional urology, stone metaphylaxis and elective paediatric urology |
| ✂️ Elective list (*OP-Programm*) | 07:30 | 90 | Planned operations and endoscopy: technique, anatomy, intraoperative findings and perioperative routine |
| 💉 Oncology day clinic (*Onkologische Tagesklinik*) | 08:30 | 11 | Therapy protocols: doses, caps, renal thresholds, cycles, mandatory support and maintenance, plus drug toxicities of systemic cancer therapy |
| ☢️ Radiation oncology (*Radioonkologie*) | 08:15 | 10 | Fractionation, ADT with radiotherapy, salvage after prostatectomy, trimodal bladder preservation, seminoma, palliative and stereotactic radiotherapy |

Each duty has its own briefing from the cast, whiteboard label and daylight or night window; the attending stays awake in the daytime. The tumour board meets in a conference room where the session's cases lie on the table as folders. The library filters by duty, every case card shows its duty, and the progress page reports performance by duty. Practice sessions started from the library, rematch or quick round take the duty of their cases, or a mixed rotation if the cases differ.

Every case's duty is stored as `duty` in `data/*.json`; imported questions take it from `data/import-selection.json`, so a re-import keeps it. The assignment classifies by the decision the question asks for, not only by the diagnosis: two independent classifications of all 297 cases agreed on 288, a judge resolved nine, and one review change moved autonomic dysreflexia during urodynamics from the night shift to the clinic. The oncology stories, selected supplementary questions and new anatomy questions carry an explicit duty. Historical allocation figures in the validation notes describe earlier versions. See [docs/VALIDATION.md](docs/VALIDATION.md).

## Protocol page, day clinic and radiation oncology

- **Protocol page (*Protokolle*):** a switch shows either **systemic therapy** or **radiotherapy**, with one tab per tumour group.
  - *Systemic therapy:* 53 current regimens for urothelial carcinoma (13), intravesical therapy (5), prostate (19), kidney (9), testis (6) and penis/urethra (1). Only the 28 **standards** (the guideline's first choice for a setting) are shown at first; *Show alternatives* adds the 25 regimens for patients who cannot receive the standard and for later lines. Each card is marked Standard or Alternative and gives indication, cycle length and number of cycles, and a drug table with dose, route and days. A fold-out adds support (premedication, hydration, G-CSF, mesna, monitoring), cautions (renal thresholds, cumulative limits, contraindications), evidence with the EU approval status, and sources.
  - *Radiotherapy:* 42 schemes in 6 groups (primary prostate radiotherapy, after prostatectomy and metastatic prostate cancer, bladder, seminoma, penile and urethral cancer, palliative and stereotactic), each with target volume, total dose, dose per fraction, number of fractions and schedule, plus technique, combined systemic therapy (for example ADT and its duration), planning, toxicity and evidence.
  - Every regimen or scheme with questions has a *Practise questions* button. On phones each table row becomes a small card, so doses never hide behind sideways scrolling.
  - The page always says it is a learning overview, not a prescription or treatment plan. `manage.py` refuses doses without a number, table cells longer than the table allows, radiotherapy phases whose total dose is not dose per fraction × fractions, sources that are not HTTPS, and any author mention.
- **Oncology day clinic (*Onkologische Tagesklinik*, from 08:30):** 11 active cases on selected protocols and systemic treatment toxicity.
- **Radiation oncology (*Radioonkologie*, from 08:15):** 10 selected active questions. The radiation oncologist briefs the duty, answers the phone and stands at the station instead of the attending.
- **35 selected clinical single questions:** 12 current guideline questions, 10 systemic protocol/toxicity questions, 10 radiotherapy questions and 3 functional urology questions. They complement the complete imported bank and multi-step stories.
- **Content refinements on 11 October 2026:** early terbutaline after injection therapy without delaying ischaemia treatment; individual counselling about early penile prosthesis; the specific S3 BRCA2 biopsy pathway; limitations of sestamibi and oncocytic biopsy findings; and an explicit S3 version for PSA screening intervals. Each correction records the old and new wording and precise sources in `data/case-updates.json`.
- **50 new anatomy questions:** kidney (10), ureter (8), bladder (6), prostate (7), penis/urethra (7), testis/scrotum (7), nerves and micturition (5). All have four shuffled options and a rationale for each in DE/EN/ES. Anatomy has its own library filter and mastery group.

## Schemas, anatomy atlas and own images

- **Teaching schemas:** 15 cartoon schematic drawings made for this game (`data/schemas.json`) with 189 tappable structures, from the urinary tract overview, kidney envelopes, prostate zones and bladder-wall T stages to urinary diversion, micturition control, the retroperitoneal lymph-node landing zones and VUR grades. 198 of the 402 active cases link to one; questions about drugs, laboratory values, counselling or guidelines deliberately have none. After the last decision of a case, the explanation shows the matching schema with the case's key structures glowing (★). Every structure is tappable and shows its name and one key fact. The debrief and the logbook review show it too. The links between cases and schemas are in `data/case-schemas.json`.
- **Anatomy atlas:** a new *Atlas* page lists all schemas. *Find the structure* is a five-round tap quiz on a schema. A right tap gives confetti, a wrong one the splash, and 5 of 5 earns the *Anatomy ace* sticker. Quiz results never change case scores.
- **Own images:** put licensed PNG, JPEG or WebP files in `media/` and list them in `data/case-media.json`, with alt text and caption in EN/DE/ES, `credit` and `license`. The build embeds them and refuses a file without credit or licence, a file outside `media/` or an SVG. See [media/README.md](media/README.md). Do not add identifiable patient images.

The schemas are simplified teaching drawings, not to scale, and were not reviewed clinically. See [docs/VALIDATION.md](docs/VALIDATION.md) for how they were checked.

## Characters and game mechanics

- **Avatars and cartoon rooms:** choose your character and move through the hospital with the original cast and translated comedy.
- **Nurse's joker (Grace / Jana / Lucía):** once per question, the nurse crosses out one of the weakest wrong answers. It costs five simulated minutes and never changes points. She never appends learning objectives or an automatic answer cue. After answering, she only gives advice.
- **Call the attending (Dr. Brennan / Dr. Brenner / Dr. Herrera):** three calls per shift, five simulated minutes each. The attending gives an optional written nudge for this decision. If no hint is available, the game asks you to reconsider the case yourself; it never falls back to a learning objective. Asking again about the same decision is free; after answering, the call is a free debrief. When the calls are used up, the nurse says so. Every decision of the game has its own hint in EN/DE/ES (`data/attending-hints.json`).
- **Radiation oncologist (Dr. Okoro / Dr. Falkner / Dra. Robledo):** a new cast member with her own portrait and lines. She answers the phone for radiotherapy questions (case field `consultant: "radiotherapist"`), shares the three calls of the shift and briefs the radiation-oncology duty.
- **"Important" after a dangerous answer:** when an answer would have harmed the patient, the attending (or, for radiotherapy questions, the radiation oncologist) steps in with the decisive rule instead of a joke.
- **Answer marking and explanations:** after each decision the correct option is marked ✓ and a wrong choice ✗ (◐ for a partly appropriate story choice). A missed question shows **why the preferred answer is right**, and **"Every option explained"** opens the source rationale for each choice. The debrief and the logbook review repeat this.
- **Right or wrong you can feel:** a right answer brings confetti. A wrong one gets a cartoon *urine splash*, with droplets, a puddle and a line such as *Post-void dribble!*, plus a splash sound when pager sounds are on. New stickers pop up as a sticker instead of confetti, so confetti never follows a wrong answer.
- **Streaks:** consecutive correct decisions build a 🔥 streak. Streaks of 3, 5, 10, 15 … earn a special line from the cast and confetti. A wrong source answer gets exam-style teasing that points to the explanation; safety feedback stays serious.
- **Career ladder:** XP is the sum of your best score per case, so replaying a case improves XP, but repeating it does not inflate XP. Nine ranks lead from medical student to night-shift legend, each with its own joke and a promotion scene.
- **Sticker album:** 14 collectable stickers, e.g. for streaks, a perfect session, a perfect chief's quiz, a case in every department, a rematch at 100% or completing every case of a specialty. Locked stickers say how to earn them.
- **Targeted practice:** *Rematch* replays up to ten cases whose latest attempt was below 100%. The report can replay the current shift's misses. *Specialties* on the progress page lists mastery per source specialty, weakest first, with a *Train* button. The library can practise ten random cases from the current filter. The introduction offers a five-question *Quick round* that starts with unplayed cases.
- **Keyboard play:** A–F or 1–6 picks an answer, including in the chief's quiz; Enter continues.
- **Coffee:** during an unfinished session, a cup adds exactly **five simulated minutes** and a character quip. It changes no case score or vital signs. Outside an unfinished session, it only delivers a quip.
- **Pager sounds:** optional synthesised audio is off by default.
- **Chief's final quiz:** uses questions from completed case steps. Its results remain separate from saved case scores and CSV analysis.

Streaks, jokers, ranks and stickers are game motivation only. They are stored with local progress (`stats`, `badges`), derived from the logbook where possible, and never alter case scores, the exported `history` or the CSV analysis. Progress saved by the earlier release loads unchanged; existing achievements are credited quietly on first load. Confetti and animations respect the system setting for reduced motion.

Each source question gives 10 points for its original correct answer and 0 for another answer, with five fictional minutes per choice. The import does not invent clinical safety-error classifications. A source case has a maximum of 10 raw points; a three-step story has 30. Case results are displayed on a **0–100 scale**, so the two formats can be understood together. Source evidence flags and clinical review status are independent of game points.

The comedy and clock are fictional game mechanics. Points, coffee costs and simulated minutes are not clinical response times or a validated assessment of competence.

## Source import and review status

All 267 main-bank questions are included once, including **10 drafts** and **32 evidence-marked questions**. Draft and evidence notices remain visible. Of the imported questions, **51 carry an explicit source sign-off for German only**; the other **216 have no imported sign-off** (206 pending independent review and 10 drafts without a clinical review status). None has an imported English or Spanish sign-off. This expansion grants no new medical or translation approval.

Provenance is supplied in:

- `data/imported-source.json`: original DE/EN/ES content, option keys, explanations, citations, source version, language-specific sign-off information and content hashes.
- `data/import-selection.json`: the complete one-to-one source mapping and department allocation.
- `data/import-manifest.json`: archive name and SHA-256, selection hash, counts and import policy.
- [docs/QUELLENIMPORT.md](docs/QUELLENIMPORT.md): source inventory, duplicate-check method and allocation report.

The supplied archive's SHA-256 is `388ef0ed51fdd17971248bd3b7867fb35bf6d9622b2331464e6f9e1a9ece799b`. The importer checks unique IDs and normalized clinical text in each language; this catches exact repeated questions, not every possible semantic overlap between related topics.

To compare the delivered import with your original ZIP without writing files:

```text
python scripts/import_urofragen.py "Urofragen-GitHub-DE-EN-ES-2026-10-04.zip" --check
```

To reproduce the import, then rebuild the playable editions:

```text
python scripts/import_urofragen.py "Urofragen-GitHub-DE-EN-ES-2026-10-04.zip"
python scripts/manage.py build
```

Use the actual path to your original ZIP. The importer reads the domain metadata and main-bank JSON members only; it never executes scripts from the archive. It preserves the 30 existing story cases. Keep the supplied archive if you want to reproduce the source comparison later.

## Oncology update (October 2026)

The oncology cases were checked against the knowuro flowcharts 2026 for bladder, prostate, kidney, upper tract urothelial, testicular, penile and urethral cancer. These flowcharts are based on the EAU Guidelines and licensed CC BY-NC-ND 4.0. The game uses their facts only; it neither copies nor redraws them.

- **Audit:** an auditor per tumour group checked 169 cases, and an independent skeptic tried to refute every finding. 43 findings were confirmed and are corrected. The skeptics refuted two. One of them rested on a drug approval that came after the flowcharts went to press, so approval statements in the game were checked on the web on 6 October 2026.
- **Correction layer:** the corrections live in `data/case-updates.json`, not in the case files. Each change records the text it replaces, so a later re-import cannot silently overwrite or lose it. Corrected cases show an *Updated* badge; the reason and sources appear after the final answer.
- **20 new cases** cover decisions no case taught before, with two or three decisions each, in DE, EN and ES. Each was written from a reviewed gap list and then checked by an independent urologist reviewer. Topics: very high-risk NMIBC, single instillation and intermediate risk, positive cytology, first-line metastatic urothelial cancer, adjuvant therapy after cystectomy, BCR after prostatectomy, cN1 prostate cancer, BRCA2 mCRPC, mHSPC unfit for chemotherapy, life-threatening germ cell cancer, IGCCCG intermediate prognosis, stage I seminoma with risk factors, IMDC first line, cT2 renal cancer and cytoreductive nephrectomy, relapse after adjuvant pembrolizumab, metastatic UTUC, embolisation for haematuria, penile cancer cN1 and sentinel pN1, and locally advanced urethral cancer.
- **No authors in the game:** article citations such as “(Dieckmann et al. 2025)” are removed when the catalog is built, and sentences that named authors or “the article” were reworded. Validation rejects any new author mention.

## Python automation

Use **Python 3.10 or newer**. The tools use the standard library, with no package installation required. Run commands from the project folder; on Windows, `py` can replace `python`.

| Task | Command | Result |
| --- | --- | --- |
| Validate | `python scripts/manage.py validate` | Checks the 500-question contract, languages, answer markers, provenance, references, archived cases and local assets |
| Build | `python scripts/manage.py build` | Recreates `assets/catalog.js` and `standalone.html` |
| Serve locally | `python scripts/manage.py serve --port 8000` | Opens a local-only service at `http://127.0.0.1:8000/`; stop with Ctrl+C |
| Daily shift | `python scripts/manage.py schedule --date 2026-10-05 --seed team-a --duty night` | Creates 10 distinct cases of one duty (`night`, `board`, `clinic`, `elective`, `dayclinic` or `radiotherapy`), rotating through topics, in `outputs/daily-shift.json`; without `--duty`, two per department as before |
| Analyse progress | `python scripts/manage.py analyse session-export.json --output outputs/progress.csv` | Writes one CSV row per decision, preserving repeated attempts |
| Package | `python scripts/manage.py package --output dist/night-shift-academy.zip` | Rebuilds and creates a ZIP with fixed timestamps and a SHA-256 file manifest |
| Python checks | `python -m unittest discover -s tests -v` | Runs the automation and import regression suite |
| Game checks | `node tests/tests-engine.cjs` | Runs engine, save, score and mixed-format case checks |
| Cartoon checks | `node tests/tests-cartoon.cjs` | Checks translated cast, artwork, accessible room controls and game extras |

Daily shifts are reproducible for the same library, date, seed and duty. Without `--duty` they favour varied difficulty within each department. Import the generated JSON using the game's daily-shift control; change the seed for another roster.

**Save and continue:** *Save game file* on the progress page downloads a game file (`format: "night-shift-academy-save"`, `version: 3`). It holds the `history`, rank counters (`stats`), stickers (`badges`), bookmarks, player name and avatar, the last duty and any open `session`. *Load game file* reads it back, on the same or another device, and continues from that point. It also reads logbooks exported by earlier releases (`version: 2`, history only). The file is treated as untrusted: every entry passes the same checks as local storage, and changed scores, unknown cases and unknown keys are dropped. A dialog shows what the file contains before anything changes. Loading combines both logbooks, keeps the higher counters and joins stickers and bookmarks; the rank is recalculated from the combined logbook. Each logbook entry carries its shift, so the same patient of the same shift counts once, and a shift or morning report is counted once even when an older copy of it is loaded and finished again. Which shift continues: the same shift keeps whichever copy got further; otherwise an open shift wins over a finished one, and the file's shift wins when both are open, with a warning in the dialog. Without a name in the file, the avatar is only taken on a device without a player name.

The analyser reads the game file and the older `version: 2` export alike. Each completed attempt includes `caseId`, `area`, `score`, `maxScore`, `elapsed`, `criticalErrors`, `completedAt` and `answers`. The answer count follows the case: **one for an imported question, three for a story**. Each answer records `stepId`, `optionId`, `score` and `minutes`; the analyser validates these against the current library. CSV output has the same variable number of rows per attempt. `elapsed` sums case-decision minutes and excludes coffee and waiting on the overall game clock. Keep the matching library version if you alter a case after playing it.

Learner data stays in the local browser unless you export it. Back up progress before clearing storage or moving to another browser/device. Node.js is needed only for JavaScript development checks, not for playing or using the Python tools.

## Project structure and editing

```text
index.html                  Introduction and modern game interface
standalone.html             Generated complete single-file game
assets/styles.css           Base visual design
assets/cartoon.css          Cartoon scenes and game controls
assets/i18n.js              EN/DE/ES interface text
assets/banter.js             Translated dialogue and quips
assets/art.js                Original-style character and department artwork
assets/engine.js             Game and progress logic
assets/app.js                Interface, filters and pagination
assets/catalog.js            Generated case/reference library
data/emergency.json          35 active emergency cases
data/ward.json               33 active ward cases
data/clinic.json             201 active clinic cases
data/endoscopy.json          37 active endoscopy cases
data/theatre.json            96 active theatre cases
data/imported-source.json    Original question snapshot and provenance
data/import-selection.json   Source-to-case mapping
data/import-manifest.json    Import counts and hashes
data/case-updates.json       Reviewed corrections and editorial edits applied at build
data/protocols.json          Systemic and intravesical therapy protocols (protocol page)
data/radiotherapy.json       Radiotherapy schemes (protocol page)
data/attending-hints.json    The attending's hint for every decision
data/refs-*.json             Reference metadata and related-source links
data/question-contract.json  Exact 500-question target and minimum anatomy coverage
data/archive/               Historical supplementary questions for old logbook entries
scripts/import_urofragen.py  JSON-only source importer and comparison
scripts/manage.py            Build, validation, scheduling, analysis and packaging
tests/                      Regression checks
.github/workflows/check.yml GitHub checks and ZIP build
classic/                    Three unchanged supplied games
docs/                       Source and validation reports
outputs/daily-shift.json     Example daily shift
```

New questions require no `objectives`; any legacy objectives are stripped when building. Anatomy cases have `subject: "anatomy"`, an `anatomyGroup`, a translated topic and evidence metadata. Each also requires a `clinicalContext` with `kind: "operation"` or `"case"` and a translated `label`; the clinical situation appears in both the chart and question stem. All 50 new anatomy questions correlate with surgery (31) or a clinical case (19). Cases have a unique `id`, an `area`, difficulty `level` (1–3), game `acuity`, teaching `patient`, translated `title`, `presenting` and `takeaway`, decision `steps` and reference IDs. Imported cases additionally have translated `topic` and `source` provenance, and their `patient` adds `sex` (`female`, `male` or `null`), `ageBand` and, for the case without a patient, a translated `label`. To rename an imported patient, edit `data/patient-names.json` (keyed by source question ID) and apply it with the importer, or edit both files consistently. The importer retains the source vignette and does not fill absent vital signs or ages with invented numbers.

Each step has a unique `id`, `kind`, translated `prompt`, options and a `best` option ID. Options have unique IDs, translated text/feedback, points, fictional minutes and a Boolean `critical` marker. One option scores 10 and matches `best`. Legacy stories may award partial points and mark safety errors; imported MCQs preserve their single correct key and use no invented safety-error penalties.

After editing, run `validate` and `build`, then include generated files with the source. The standalone builder embeds all local stylesheets, scripts and the favicon in their declared order. Keep styles in the order `styles.css`, `cartoon.css`; scripts in the order `i18n.js`, `banter.js`, `art.js`, `catalog.js`, `engine.js`, `app.js`. No JavaScript bundler is required.

## GitHub-ready ZIP

This delivery contains repository-ready files. The included GitHub workflow validates, tests, rebuilds and creates a ZIP artifact on pushes and pull requests; it does not deploy a website. It uses GitHub's official [checkout](https://github.com/actions/checkout), [Python setup](https://github.com/actions/setup-python) and [artifact upload](https://github.com/actions/upload-artifact) actions.

For optional later publication, the root `index.html` can serve as a GitHub Pages entry point. See the [official Pages setup guide](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site). The ZIP and single-file game work independently of GitHub.

## Clinical scope and rights

This is an educational game for rehearsal and discussion, not a clinical protocol or credential. Clinical judgment, supervision, local policies and current specialist guidance remain necessary for real patients. The complete game and its translations have not received a new independent specialist review as part of this expansion.

Original source citations and review metadata remain available. Related EAU guideline index links were checked as primary reference metadata; **the 267 imported questions were not newly checked against every guideline or certified clinically**. Earlier oncology audits are documented separately. This revision checks the new anatomy content and the targeted clinical refinements against the linked sources; it does not confer a new clinical sign-off on all 500 questions. Such related links do not validate a specific dosing claim, translation, distractor or evidence level. See [docs/VALIDATION.md](docs/VALIDATION.md) for the distinction between software verification and medical review.

The original games in `classic/` retain their supplied medical claims, scoring, translations and notices unchanged. No ownership or licence has been inferred for either the games or the supplied question bank, and no invented licence is added. Check the applicable permissions before redistribution or public publication. Source links do not imply endorsement.
