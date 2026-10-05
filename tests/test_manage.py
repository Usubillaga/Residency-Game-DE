"""Public data-format and automation regression tests; no third-party packages."""

import copy
import csv
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("manage", Path(__file__).resolve().parents[1] / "scripts" / "manage.py")
manage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage)


def translated(text):
    return {language: text for language in manage.LANGUAGES}


def example_case(area, number):
    options = [
        {"id": "a", "text": translated("Safe action"), "score": 10, "minutes": 2, "feedback": translated("Appropriate"), "critical": False},
        {"id": "b", "text": translated("Incomplete action"), "score": 3, "minutes": 5, "feedback": translated("Review priorities"), "critical": False},
        {"id": "c", "text": translated("Unsafe action"), "score": 0, "minutes": 9, "feedback": translated("Seek support"), "critical": True},
    ]
    return {"id": f"{area}-fixture-{number}", "area": area, "level": number, "acuity": "routine", "patient": {"name": "Fictional Patient", "age": 45}, "title": translated("Fixture case"), "presenting": translated("Fictional presentation"), "vitals": {"bp": "120/80", "hr": 80, "temp": 37.0, "spo2": 98, "rr": 16}, "objectives": {language: ["Recognise priorities", "Practise handover"] for language in manage.LANGUAGES}, "steps": [{"id": f"step-{index}", "kind": "decision", "prompt": translated("Choose an action"), "options": copy.deepcopy(options), "best": "a"} for index in range(3)], "takeaway": translated("Use local guidance"), "references": ["fixture-source"]}


def imported_case(area="emergency"):
    case = example_case(area, 1)
    case["id"] = f"{area}-source-question"
    case["patient"]["age"] = None
    case["vitals"] = None
    case["steps"] = case["steps"][:1]
    options = case["steps"][0]["options"]
    options.append({"id": "d", "text": translated("Fourth original choice"), "score": 0, "minutes": 2, "feedback": translated("Original source rationale"), "critical": False})
    for option in options:
        option["critical"] = False
        option["score"] = 10 if option["id"] == "a" else 0
    case["source"] = {"questionId": "original-question-01", "archivePath": "data/fragen/andrology.json", "domain": "andrology", "version": 1, "contentSha256": "a" * 64, "reviewStatus": "not-clinically-validated", "clinicalSignoffLanguages": []}
    case["topic"] = translated("Source topic")
    return case


class AutomationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repository"
        (self.root / "data").mkdir(parents=True)
        (self.root / "assets").mkdir()
        for area in manage.AREA_IDS:
            manage.write_json(self.root / "data" / f"{area}.json", [example_case(area, number) for number in (1, 2, 3)])
        manage.write_json(self.root / "data" / "refs-fixture.json", [{"id": "fixture-source", "title": "Official fixture source", "url": "https://example.org/education", "checked": "2026-10-05", "scope": "Test source only."}])
        for filename in ("styles.css", "i18n.js", "engine.js", "app.js"):
            (self.root / "assets" / filename).write_text("/* fixture */\n", encoding="utf-8")
        (self.root / "assets" / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
        scripts = "".join(f'<script src="assets/{filename}"></script>' for filename in ("i18n.js", "catalog.js", "engine.js", "app.js"))
        (self.root / "index.html").write_text('<!doctype html><html><head><link rel="icon" href="assets/favicon.svg"><link rel="stylesheet" href="assets/styles.css"></head><body>' + scripts + "</body></html>", encoding="utf-8")

    def mutate_case(self, callback):
        path = self.root / "data" / "emergency.json"
        cases = manage.read_json(path)
        callback(cases[0])
        manage.write_json(path, cases)

    def add_cartoon_assets(self):
        for filename in ("i18n.js", "banter.js", "art.js", "engine.js", "app.js"):
            (self.root / "assets" / filename).write_text(f"/* marker-{filename} */\n", encoding="utf-8")
        (self.root / "assets" / "styles.css").write_text("/* marker-styles.css */\n", encoding="utf-8")
        (self.root / "assets" / "cartoon.css").write_text("/* marker-cartoon.css */\n.avatar { border-radius: 50%; }\n", encoding="utf-8")
        path = self.root / "index.html"
        markup = path.read_text(encoding="utf-8")
        markup = markup.replace('<link rel="stylesheet" href="assets/styles.css">', '<link rel="stylesheet" href="assets/styles.css"><link href="assets/cartoon.css" media="screen" rel="stylesheet">')
        markup = markup.replace('<script src="assets/catalog.js"></script>', '<script src="assets/banter.js"></script><script src="assets/art.js"></script><script src="assets/catalog.js"></script>')
        path.write_text(markup, encoding="utf-8")

    def add_imported_case(self, case=None):
        case = copy.deepcopy(case or imported_case())
        path = self.root / "data" / f"{case['area']}.json"
        cases = manage.read_json(path)
        cases.append(case)
        manage.write_json(path, cases)
        return case

    def test_schedule_is_reproducible_and_balanced(self):
        first = manage.schedule(self.root, "2026-10-05", "a seed", self.root / "outputs" / "one.json")
        second = manage.schedule(self.root, "2026-10-05", "a seed", self.root / "outputs" / "two.json")
        self.assertEqual(first, second)
        self.assertEqual(len(first["caseIds"]), 10)
        self.assertEqual(len(set(first["caseIds"])), 10)
        for area in manage.AREA_IDS:
            self.assertEqual(sum(case_id.startswith(area + "-") for case_id in first["caseIds"]), 2)
        self.assertEqual(first["version"], 2)

    def test_missing_locale_is_rejected(self):
        self.mutate_case(lambda case: case["steps"][1]["options"][2]["feedback"].pop("es"))
        with self.assertRaisesRegex(manage.ValidationError, "translations must contain exactly en/de/es"):
            manage.load_and_validate(self.root, check_assets=False)

    def test_invalid_best_answer_is_rejected(self):
        self.mutate_case(lambda case: case["steps"][0].update(best="missing"))
        with self.assertRaisesRegex(manage.ValidationError, "best: must identify"):
            manage.load_and_validate(self.root, check_assets=False)
        self.mutate_case(lambda case: case["steps"][0].update(best="c"))
        with self.assertRaisesRegex(manage.ValidationError, "best option must score 10"):
            manage.load_and_validate(self.root, check_assets=False)

    def test_build_embeds_the_complete_catalog_and_scripts(self):
        (self.root / "assets" / "app.js").write_text('const example = "</ScRiPt>";', encoding="utf-8")
        catalog = manage.build(self.root)
        expected_ids = {case["id"] for filename in manage.CASE_FILES for case in manage.read_json(self.root / "data" / filename)}
        self.assertEqual({case["id"] for case in catalog["cases"]}, expected_ids)
        standalone = (self.root / "standalone.html").read_text(encoding="utf-8")
        self.assertIn("window.NSA_CATALOG", standalone)
        self.assertNotIn('src="assets/', standalone)
        self.assertNotIn('href="assets/styles.css"', standalone)
        self.assertNotIn('href="assets/favicon.svg"', standalone)
        self.assertIn("data:image/svg+xml;base64,", standalone)
        self.assertIn(r"<\/ScRiPt>", standalone)
        manage.load_and_validate(self.root)

    def test_duty_schedule_draws_only_that_duty(self):
        for area in manage.AREA_IDS:
            path = self.root / "data" / f"{area}.json"
            cases = manage.read_json(path)
            for index, case in enumerate(cases):
                case["duty"] = "night" if area in ("emergency", "ward") or index == 0 else "clinic"
            manage.write_json(path, cases)
        first = manage.schedule(self.root, "2026-10-05", "seed", self.root / "outputs" / "night.json", "night")
        second = manage.schedule(self.root, "2026-10-05", "seed", self.root / "outputs" / "again.json", "night")
        self.assertEqual(first, second)
        self.assertEqual(first["duty"], "night")
        self.assertEqual(len(first["caseIds"]), 9, "Only the nine night cases of the fixture can be drawn")
        self.assertEqual(len(set(first["caseIds"])), 9)
        night = {case["id"] for area in manage.AREA_IDS for case in manage.read_json(self.root / "data" / f"{area}.json") if case["duty"] == "night"}
        self.assertTrue(set(first["caseIds"]) <= night)
        with self.assertRaisesRegex(manage.ValidationError, "No cases are assigned"):
            manage.schedule(self.root, "2026-10-05", "seed", self.root / "outputs" / "board.json", "board")

    def test_invalid_duty_is_rejected(self):
        self.mutate_case(lambda case: case.update(duty="weekend"))
        with self.assertRaisesRegex(manage.ValidationError, "duty: expected one of"):
            manage.load_and_validate(self.root, check_assets=False)

    def write_schema(self, svg_extra=""):
        parts = [{"id": f"p{index}", "label": translated(f"Part {index}"), "note": translated("A fact")} for index in range(4)]
        svg = "".join(f'<g data-part="p{index}"><circle cx="{50 + index * 60}" cy="100" r="20" fill="#e59a8c" stroke="#2a2442"/></g>' for index in range(4)) + svg_extra
        schema = {"id": "fixture-schema", "title": translated("Schema"), "caption": translated("Schematic"), "domains": ["andrology"], "viewBox": "0 0 600 420", "svg": svg, "parts": parts}
        manage.write_json(self.root / "data" / "schemas.json", [schema])

    def test_schemas_links_and_licensed_images_are_built_into_the_catalog(self):
        self.write_schema()
        manage.write_json(self.root / "data" / "case-schemas.json", {"emergency-fixture-1": {"schema": "fixture-schema", "parts": ["p1"]}})
        (self.root / "media").mkdir()
        (self.root / "media" / "sketch.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        row = {"case": "ward-fixture-2", "file": "media/sketch.png", "alt": translated("Sketch"), "caption": translated("Hand sketch"), "credit": "Own drawing", "license": "CC BY 4.0"}
        manage.write_json(self.root / "data" / "case-media.json", [row])
        catalog = manage.build(self.root)
        self.assertEqual(catalog["schemas"][0]["id"], "fixture-schema")
        linked = next(case for case in catalog["cases"] if case["id"] == "emergency-fixture-1")
        self.assertEqual(linked["schema"], {"id": "fixture-schema", "parts": ["p1"]})
        pictured = next(case for case in catalog["cases"] if case["id"] == "ward-fixture-2")
        self.assertTrue(pictured["media"][0]["src"].startswith("data:image/png;base64,"))
        self.assertEqual(pictured["media"][0]["license"], "CC BY 4.0")
        row.pop("license")
        manage.write_json(self.root / "data" / "case-media.json", [row])
        with self.assertRaisesRegex(manage.ValidationError, "license"):
            manage.build(self.root)
        (self.root / "media" / "drawing.svg").write_text("<svg/>", encoding="utf-8")
        manage.write_json(self.root / "data" / "case-media.json", [dict(row, license="CC0", file="media/drawing.svg")])
        with self.assertRaisesRegex(manage.ValidationError, "only PNG, JPEG or WebP"):
            manage.build(self.root)
        manage.write_json(self.root / "data" / "case-media.json", [dict(row, license="CC0", file="../outside.png")])
        with self.assertRaisesRegex(manage.ValidationError, "existing file in media/"):
            manage.build(self.root)

    def test_unsafe_schemas_and_unknown_highlights_are_rejected(self):
        for extra, message in (('<text x="1" y="1">label</text>', "element <text>"), ('<g data-part="p9" onclick="x()"></g>', "not allowed"), ('<g data-part="p9"><circle cx="1" cy="1" r="1"/></g>', "without a label")):
            self.write_schema(extra)
            with self.assertRaisesRegex(manage.ValidationError, message):
                manage.load_visuals(self.root, manage.load_and_validate(self.root, check_assets=False)[0])
        self.write_schema()
        manage.write_json(self.root / "data" / "case-schemas.json", {"emergency-fixture-1": {"schema": "fixture-schema", "parts": ["missing"]}})
        with self.assertRaisesRegex(manage.ValidationError, "unknown part"):
            manage.load_visuals(self.root, manage.load_and_validate(self.root, check_assets=False)[0])

    def test_schema_safety_check_parses_the_markup_instead_of_pattern_matching(self):
        # Each payload slipped past the earlier pattern-based check and would have run script or broken the quiz.
        bypasses = (
            ('<g data-part="p9"><circle cx="1" cy="1" r="1" fill="#f00>"/onclick="alert(1)"/></g>', "unsafe value|not well-formed"),
            ('<g data-part="p9"><circle cx="1" cy="1" r="1" fill="#f00>"onmouseover="alert(1)"/></g>', "not well-formed|unsafe value"),
            ('<img/src="x"/onerror="alert(document.domain)"', "not well-formed"),
            ('<g data-part="p0"><image href="x.png"/></g>', "element <image>"),
            ("<g data-part='ghost'><circle cx='1' cy='1' r='1'/></g>", "without a label"),
            ('<g data-part = "ghost"><circle cx="1" cy="1" r="1"/></g>', "without a label"),
            ('<!-- --><circle cx="1" cy="1" r="1"/>', "comments"),
            ('<circle cx="1" cy="1" r="1" fill="url(#x)"/>', "unsafe value"),
            ('<g data-part="p0"><g data-part="p1"/></g>', "nested"),
            ('<circle cx="1" cy="1" r="1" data-part="p9"/>', "<g> group"),
        )
        for extra, message in bypasses:
            with self.subTest(extra=extra):
                self.write_schema(extra)
                with self.assertRaisesRegex(manage.ValidationError, message):
                    manage.load_visuals(self.root, manage.load_and_validate(self.root, check_assets=False)[0])

    def test_malformed_schema_and_link_entries_are_reported_not_crashed(self):
        cases = manage.load_and_validate(self.root, check_assets=False)[0]
        self.write_schema()
        schema = manage.read_json(self.root / "data" / "schemas.json")
        manage.write_json(self.root / "data" / "schemas.json", [dict(schema[0], parts=["a", "b", "c", "d"])])
        with self.assertRaisesRegex(manage.ValidationError, r"parts\[0\]: expected an object"):
            manage.load_visuals(self.root, cases)
        self.write_schema()
        for link, message in (({"schema": ["fixture-schema"]}, "unknown schema"), ({"schema": "fixture-schema", "parts": [{"id": "p1"}]}, "up to 4 part ids")):
            with self.subTest(link=link):
                manage.write_json(self.root / "data" / "case-schemas.json", {"emergency-fixture-1": link})
                with self.assertRaisesRegex(manage.ValidationError, message):
                    manage.load_visuals(self.root, cases)

    def test_schedule_rejects_noncanonical_date(self):
        with self.assertRaisesRegex(manage.ValidationError, "YYYY-MM-DD"):
            manage.schedule(self.root, "20261005", "seed", self.root / "outputs" / "shift.json")

    def test_cartoon_assets_are_inlined_in_dependency_order(self):
        self.add_cartoon_assets()
        manage.build(self.root)
        standalone = (self.root / "standalone.html").read_text(encoding="utf-8")
        self.assertNotIn('src="assets/', standalone)
        self.assertNotIn('href="assets/', standalone)
        self.assertIn('<style media="screen">', standalone)
        script_markers = ("marker-i18n.js", "marker-banter.js", "marker-art.js", "window.NSA_CATALOG", "marker-engine.js", "marker-app.js")
        positions = [standalone.index(marker) for marker in script_markers]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(standalone.index("marker-styles.css"), standalone.index("marker-cartoon.css"))

    def test_duplicate_local_styles_and_scripts_are_rejected(self):
        manage.build(self.root)
        path = self.root / "index.html"
        original = path.read_text(encoding="utf-8")
        for tag, kind in (('<script src="./assets/i18n.js?cache=1"></script>', "script"), ('<link href="./assets/styles.css" rel="stylesheet">', "stylesheet")):
            with self.subTest(kind=kind):
                path.write_text(original.replace("</body>", tag + "</body>"), encoding="utf-8")
                with self.assertRaisesRegex(manage.ValidationError, f"duplicate {kind} reference"):
                    manage.validate_assets(self.root)
        for tag, kind in (('<script src="#missing-file"></script>', "script"), ('<link href="javascript:alert(1)" rel="stylesheet">', "stylesheet")):
            with self.subTest(invalid_kind=kind):
                path.write_text(original.replace("</body>", tag + "</body>"), encoding="utf-8")
                with self.assertRaisesRegex(manage.ValidationError, f"invalid {kind} reference"):
                    manage.validate_assets(self.root)

    def test_invalid_cartoon_dependency_order_is_rejected(self):
        self.add_cartoon_assets()
        manage.build(self.root)
        path = self.root / "index.html"
        original = path.read_text(encoding="utf-8")
        for first, second, kind in (("i18n.js", "art.js", "script"), ("styles.css", "cartoon.css", "stylesheet")):
            with self.subTest(kind=kind):
                swapped = original.replace("assets/" + first, "assets/swap-placeholder").replace("assets/" + second, "assets/" + first).replace("assets/swap-placeholder", "assets/" + second)
                path.write_text(swapped, encoding="utf-8")
                with self.assertRaisesRegex(manage.ValidationError, f"{kind} dependency order"):
                    manage.validate_assets(self.root)

    def test_package_is_reproducible_and_excludes_git(self):
        (self.root / ".git").mkdir()
        (self.root / ".git" / "private-config").write_text("private", encoding="utf-8")
        (self.root / "__pycache__").mkdir()
        (self.root / "__pycache__" / "cache.pyc").write_bytes(b"cache")
        first = Path(self.temporary.name) / "first.zip"
        second = Path(self.temporary.name) / "second.zip"
        manifest = manage.package(self.root, first)
        manage.package(self.root, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(first) as archive:
            self.assertTrue(all("/.git/" not in name and "__pycache__" not in name for name in archive.namelist()))
            hashes = json.loads(archive.read("night-shift-academy/SHA256.json"))
            self.assertEqual(hashes, manifest)
            for relative, digest in hashes.items():
                self.assertEqual(manage.hashlib.sha256(archive.read("night-shift-academy/" + relative)).hexdigest(), digest)

    def test_unknown_reference_and_missing_asset_are_rejected(self):
        self.mutate_case(lambda case: case.update(references=["not-a-source"]))
        with self.assertRaisesRegex(manage.ValidationError, "unknown reference id"):
            manage.load_and_validate(self.root, check_assets=False)
        self.mutate_case(lambda case: case.update(references=["fixture-source"]))
        manage.build(self.root)
        (self.root / "assets" / "app.js").unlink()
        with self.assertRaisesRegex(manage.ValidationError, "missing local file"):
            manage.load_and_validate(self.root)

    def test_analysis_keeps_all_attempts_and_rejects_modified_scores(self):
        case = example_case("emergency", 1)
        answers = [{"stepId": step["id"], "optionId": option["id"], "score": option["score"], "minutes": option["minutes"]} for step in case["steps"] for option in step["options"] if option["id"] == step["best"]]
        record = {"caseId": case["id"], "area": case["area"], "score": sum(answer["score"] for answer in answers), "maxScore": sum(max(option["score"] for option in step["options"]) for step in case["steps"]), "elapsed": sum(answer["minutes"] for answer in answers), "criticalErrors": 0, "completedAt": "2026-10-05T09:00:00Z", "answers": answers}
        source = self.root / "session.json"
        output = self.root / "progress.csv"
        manage.write_json(source, {"version": 2, "history": [record, copy.deepcopy(record)]})
        self.assertEqual(manage.analyse(source, output, self.root), len(case["steps"]) * 2)
        with output.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual({row["attempt"] for row in rows}, {"1", "2"})
        record["answers"][0]["score"] = 9
        manage.write_json(source, {"version": 2, "history": [record]})
        with self.assertRaisesRegex(manage.ValidationError, "score/minutes do not match"):
            manage.analyse(source, output, self.root)

    def test_source_mcq_with_four_original_options_and_unknown_vitals_builds(self):
        imported = self.add_imported_case()
        catalog = manage.build(self.root)
        built = next(case for case in catalog["cases"] if case["id"] == imported["id"])
        self.assertEqual(built, imported)
        self.assertIsNone(built["patient"]["age"])
        self.assertIsNone(built["vitals"])
        self.assertEqual(len(built["steps"]), 1)
        self.assertEqual(len(built["steps"][0]["options"]), 4)
        self.assertEqual(built["source"]["clinicalSignoffLanguages"], [])
        standalone = (self.root / "standalone.html").read_text(encoding="utf-8")
        self.assertIn('"questionId":"original-question-01"', standalone)

    def test_source_provenance_rejects_bad_digest_version_and_signoff(self):
        for field, value in (("contentSha256", "not-a-sha256"), ("version", "1"), ("version", 0), ("clinicalSignoffLanguages", ["en", "en"]), ("clinicalSignoffLanguages", ["fr"]), ("questionId", "")):
            with self.subTest(field=field, value=value):
                case = imported_case()
                case["source"][field] = value
                manage.write_json(self.root / "data" / "emergency.json", [case])
                with self.assertRaisesRegex(manage.ValidationError, "source\\." + field):
                    manage.load_and_validate(self.root, check_assets=False)

    def test_draft_source_status_and_evidence_are_preserved_without_signoff(self):
        case = imported_case()
        case["source"].update(status="draft", evidenceFlag=True, reviewStatus="draft_not_reviewed", originalSources=[{"title": "Original supplied reference", "year": 2024, "url": "https://example.org/source"}])
        self.add_imported_case(case)
        catalog = manage.build(self.root)
        built = next(item for item in catalog["cases"] if item["id"] == case["id"])
        self.assertEqual(built["source"], case["source"])
        self.assertEqual(built["source"]["clinicalSignoffLanguages"], [])
        for field, value in (("status", ""), ("evidenceFlag", "false")):
            with self.subTest(field=field):
                invalid = copy.deepcopy(case)
                invalid["source"][field] = value
                manage.write_json(self.root / "data" / "emergency.json", [invalid])
                with self.assertRaisesRegex(manage.ValidationError, "source\\." + field):
                    manage.load_and_validate(self.root, check_assets=False)

    def test_imported_multilingual_text_round_trips_as_utf8(self):
        case = imported_case()
        case["presenting"] = {"en": "Clinical question — 37 °C.\nSecond line.", "de": "Überprüfung: Größe, Hämaturie und Ärztin.\nZweite Zeile.", "es": "Información: riñón, evaluación y atención.\nSegunda línea."}
        self.add_imported_case(case)
        catalog = manage.build(self.root)
        built = next(item for item in catalog["cases"] if item["id"] == case["id"])
        self.assertEqual(built["presenting"], case["presenting"])
        standalone = (self.root / "standalone.html").read_text(encoding="utf-8")
        for value in ("Überprüfung", "Hämaturie", "riñón", "evaluación", "37 °C"):
            self.assertIn(value, standalone)

    def test_missing_unknown_age_and_vitals_must_be_explicit_null(self):
        for field in ("age", "vitals"):
            with self.subTest(field=field):
                case = imported_case()
                (case["patient"] if field == "age" else case).pop(field)
                manage.write_json(self.root / "data" / "emergency.json", [case])
                with self.assertRaisesRegex(manage.ValidationError, "explicit null"):
                    manage.load_and_validate(self.root, check_assets=False)

    def test_source_mcq_does_not_assign_unvalidated_safety_errors(self):
        for field, value in (("critical", True), ("score", 3)):
            with self.subTest(field=field):
                case = imported_case()
                case["steps"][0]["options"][1][field] = value
                manage.write_json(self.root / "data" / "emergency.json", [case])
                with self.assertRaisesRegex(manage.ValidationError, "imported knowledge"):
                    manage.load_and_validate(self.root, check_assets=False)

    def test_variable_step_and_option_bounds(self):
        for step_count, option_count in ((1, 2), (8, 6), (0, 3), (9, 3), (3, 1), (3, 7)):
            with self.subTest(steps=step_count, options=option_count):
                case = example_case("emergency", 1)
                step = case["steps"][0]
                step["options"] = [copy.deepcopy(step["options"][0])] + [{"id": f"wrong-{index}", "text": translated("Distractor"), "score": 0, "minutes": 2, "feedback": translated("Feedback"), "critical": False} for index in range(option_count - 1)]
                case["steps"] = [{**copy.deepcopy(step), "id": f"step-{index}"} for index in range(step_count)]
                manage.write_json(self.root / "data" / "emergency.json", [case])
                if 1 <= step_count <= 8 and 2 <= option_count <= 6:
                    manage.load_and_validate(self.root, check_assets=False)
                else:
                    with self.assertRaises(manage.ValidationError):
                        manage.load_and_validate(self.root, check_assets=False)

    def test_analysis_accepts_a_one_step_four_choice_source_export(self):
        case = self.add_imported_case()
        record = {"caseId": case["id"], "area": case["area"], "score": 10, "maxScore": 10, "elapsed": 2, "criticalErrors": 0, "completedAt": "2026-10-05T09:00:00Z", "answers": [{"stepId": case["steps"][0]["id"], "optionId": "a", "score": 10, "minutes": 2}]}
        source = self.root / "source-session.json"
        output = self.root / "source-progress.csv"
        manage.write_json(source, {"version": 2, "history": [record]})
        self.assertEqual(manage.analyse(source, output, self.root), len(case["steps"]))
        with output.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]["max_score"], "10")
        self.assertEqual(rows[0]["critical_errors"], "0")
        record["answers"] = []
        manage.write_json(source, {"version": 2, "history": [record]})
        with self.assertRaisesRegex(manage.ValidationError, "must have 1 answers"):
            manage.analyse(source, output, self.root)


if __name__ == "__main__":
    unittest.main()
