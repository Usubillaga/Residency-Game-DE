"""Offline source-import regression tests using the committed source snapshots."""

import copy
import importlib.util
import json
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("import_urofragen", ROOT / "scripts" / "import_urofragen.py")
importer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(importer)


class ImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshots = importer.read_json(ROOT / "data" / "imported-source.json")
        cls.plan = importer.read_json(ROOT / "data" / "import-selection.json")
        cls.expected_cases = {}
        cls.domain_labels = {}
        for area in importer.AREAS:
            for case in importer.read_json(ROOT / "data" / f"{area}.json"):
                if case.get("source"):
                    cls.expected_cases[case["source"]["questionId"]] = case
                    cls.domain_labels[case["source"]["domain"]] = case["topic"]
        cls.base_banks = {}
        for source in cls.snapshots:
            question = {
                "id": source["questionId"],
                "taxonomy": {"domain": source["domain"]},
                "version": source["version"],
                "status": source["status"],
                "type": "single_best_answer",
                "options": copy.deepcopy(source["options"]),
                "content": copy.deepcopy(source["content"]),
                "sources": copy.deepcopy(source["sources"]),
                "difficulty_estimated": cls.expected_cases[source["questionId"]]["level"],
                "evidence": {"flag": source["evidenceFlag"]},
                "review": {
                    "clinical_review_status": source["reviewStatus"],
                    "approval": {"question_version": source["version"], "languages": source["clinicalSignoffLanguages"]},
                },
            }
            cls.base_banks.setdefault(source["archivePath"], {"fragen": []})["fragen"].append(question)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.archive_path = self.directory / "source-fixture.zip"
        self.plan_path = self.directory / "explicit-plan.json"
        self.banks = copy.deepcopy(self.base_banks)
        self.rows = copy.deepcopy(self.plan)

    def write_fixture(self, *, extra_members=None):
        domains = {"domains": [{"slug": domain, "label": self.domain_labels[domain]} for domain in sorted(self.domain_labels)]}
        with zipfile.ZipFile(self.archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("data/domains.json", json.dumps(domains, ensure_ascii=False))
            for member, bank in sorted(self.banks.items()):
                archive.writestr(member, json.dumps(bank, ensure_ascii=False))
            for member, content in (extra_members or {}).items():
                archive.writestr(member, content)
        self.plan_path.write_text(json.dumps(self.rows, ensure_ascii=False), encoding="utf-8")

    def generate(self):
        # The explicit plan path and generate-only API keep the delivered files untouched.
        return importer.generate(self.archive_path, plan_path=self.plan_path)

    def questions(self):
        return [question for bank in self.banks.values() for question in bank["fragen"]]

    def test_every_source_question_is_imported_once_with_exact_multilingual_choices(self):
        self.write_fixture()
        generated, snapshots, references, manifest = self.generate()
        cases = [case for area in importer.AREAS for case in generated[area]]
        source_ids = [case["source"]["questionId"] for case in cases]
        expected_ids = {source["questionId"] for source in self.snapshots}
        self.assertEqual(len(cases), 267)
        self.assertEqual(len(source_ids), len(set(source_ids)))
        self.assertEqual(set(source_ids), expected_ids)
        self.assertEqual({source["questionId"] for source in snapshots}, expected_ids)
        self.assertEqual({len(source["options"]) for source in snapshots}, {4, 5})
        by_id = {source["questionId"]: source for source in self.snapshots}
        for case in cases:
            original = by_id[case["source"]["questionId"]]
            self.assertEqual(case, self.expected_cases[original["questionId"]])
            self.assertIsNone(case["vitals"])
            self.assertEqual(len(case["steps"]), 1)
            step = case["steps"][0]
            correct = next(option["key"].lower() for option in original["options"] if option["correct"])
            self.assertEqual(step["best"], correct)
            self.assertEqual(set(case["presenting"]), set(importer.LANGS))
            for language in importer.LANGS:
                self.assertEqual(case["presenting"][language], original["content"][language]["vignette"])
                self.assertEqual(step["prompt"][language], original["content"][language]["lead_in"])
                for option in step["options"]:
                    source_option = original["content"][language]["options"][option["id"].upper()]
                    self.assertEqual(option["text"][language], source_option["text"])
                    self.assertEqual(option["feedback"][language], source_option["rationale"])
                    self.assertEqual(option["score"], 10 if option["id"] == correct else 0)
                    self.assertFalse(option["critical"])
        self.assertEqual(manifest["importedCases"], len(expected_ids))
        self.assertEqual(manifest["sourceStatuses"], dict(Counter(source["status"] for source in self.snapshots)))
        self.assertEqual(manifest["flaggedSourceQuestions"], sum(source["evidenceFlag"] for source in self.snapshots))
        self.assertEqual({reference["id"] for reference in references}, {"bank-guide-" + domain for domain in self.domain_labels})

    def test_patient_names_come_from_the_curated_list_with_a_numbered_fallback(self):
        self.write_fixture()
        names = importer.patient_names(ROOT / "data" / "patient-names.json")
        self.assertEqual(len(names), 267)
        generated = importer.generate(self.archive_path, plan_path=self.plan_path, names_path=self.directory / "absent.json")[0]
        cases = [case for area in importer.AREAS for case in generated[area]]
        self.assertTrue(all(case["patient"]["name"].startswith("Uro-") for case in cases))
        self.assertTrue(all(case["patient"]["sex"] is None and case["patient"]["ageBand"] == "unknown" for case in cases))
        first, second = sorted(names)[:2]
        duplicate = self.directory / "duplicate-names.json"
        duplicate.write_text(json.dumps({"patients": {first: names[first], second: dict(names[second], name=names[first]["name"])}}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unique"):
            importer.patient_names(duplicate)
        invalid = self.directory / "invalid-sex.json"
        invalid.write_text(json.dumps({"patients": {first: dict(names[first], sex="unknown")}}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "sex"):
            importer.patient_names(invalid)

    def test_normalized_duplicate_clinical_content_is_rejected(self):
        questions = self.questions()
        original, duplicate = questions[:2]
        duplicate["options"] = copy.deepcopy(original["options"])
        duplicate["content"] = copy.deepcopy(original["content"])
        for language in importer.LANGS:
            block = duplicate["content"][language]
            for key in ("vignette", "lead_in"):
                block[key] = "\n  " + block[key].upper() + "\t  "
            for option in block["options"].values():
                option["text"] = "\t" + option["text"].upper() + " \n"
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, "Duplicate clinical question content"):
            self.generate()

    def test_missing_coverage_and_duplicate_plan_ids_are_rejected(self):
        for kind in ("missing", "duplicate"):
            with self.subTest(kind=kind):
                self.rows = copy.deepcopy(self.plan)
                if kind == "missing":
                    self.rows.pop()
                    expected = "all 267 source questions"
                else:
                    self.rows[1]["questionId"] = self.rows[0]["questionId"]
                    expected = "Source question IDs must be unique"
                self.write_fixture()
                with self.assertRaisesRegex(ValueError, expected):
                    self.generate()

    def test_duplicate_source_ids_and_unselected_extra_source_are_rejected(self):
        for kind in ("within-bank", "across-banks", "unselected-extra"):
            with self.subTest(kind=kind):
                self.banks = copy.deepcopy(self.base_banks)
                members = list(self.banks)
                first = self.banks[members[0]]["fragen"][0]
                if kind == "within-bank":
                    self.banks[members[0]]["fragen"].append(copy.deepcopy(first))
                    expected = "Duplicate source question IDs"
                elif kind == "across-banks":
                    self.banks[members[1]]["fragen"][0]["id"] = first["id"]
                    expected = "Duplicate source question IDs"
                else:
                    extra = copy.deepcopy(first)
                    extra["id"] = "unselected-extra-question"
                    for language in importer.LANGS:
                        extra["content"][language]["vignette"] += " Unique extra source vignette."
                    self.banks[members[0]]["fragen"].append(extra)
                    expected = "cover every source question exactly once"
                self.write_fixture()
                with self.assertRaisesRegex(ValueError, expected):
                    self.generate()

    def test_draft_and_evidence_flags_do_not_infer_translation_approval(self):
        question = self.questions()[0]
        question["status"] = "draft"
        question["evidence"] = {"flag": True}
        question["review"] = {"approval": {"question_version": question["version"], "languages": ["de"]}}
        self.write_fixture()
        _, snapshots, _, _ = self.generate()
        source = next(source for source in snapshots if source["questionId"] == question["id"])
        self.assertEqual(source["status"], "draft")
        self.assertTrue(source["evidenceFlag"])
        self.assertEqual(source["reviewStatus"], "draft_not_reviewed")
        self.assertEqual(source["clinicalSignoffLanguages"], ["de"])
        self.assertNotIn("en", source["clinicalSignoffLanguages"])
        question["review"]["approval"]["question_version"] += 1
        self.assertEqual(importer.approved_languages(question), [])

    def test_archive_scripts_are_never_executed_or_extracted(self):
        sentinel = self.directory / "archive-script-executed.txt"
        script = "from pathlib import Path\nPath(" + repr(str(sentinel)) + ").write_text('executed')\nraise RuntimeError('Untrusted archive script executed')\n"
        self.write_fixture(extra_members={"scripts/untrusted.py": script, "untrusted.py": script})
        _, snapshots, _, _ = self.generate()
        self.assertEqual(len(snapshots), len(self.snapshots))
        self.assertFalse(sentinel.exists())
        self.assertFalse((self.directory / "untrusted.py").exists())
        self.assertFalse((self.directory / "scripts").exists())

    def test_malformed_and_escaping_plan_paths_are_rejected(self):
        self.write_fixture()
        self.plan_path.write_text('{"selection": [broken json}', encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            self.generate()
        for member in ("../data/fragen/andrologie.json", "data/fragen/../domains.json", "/data/fragen/andrologie.json", "scripts/untrusted.py", "data/fragen/andrologie.py"):
            with self.subTest(member=member):
                self.rows = copy.deepcopy(self.plan)
                self.rows[0]["sourcePath"] = member
                self.write_fixture()
                with self.assertRaisesRegex(ValueError, "may read only data/fragen"):
                    self.generate()

    def test_missing_translation_or_original_option_mapping_is_rejected(self):
        for kind in ("missing-language", "missing-rationale", "wrong-option-map"):
            with self.subTest(kind=kind):
                self.banks = copy.deepcopy(self.base_banks)
                question = self.questions()[0]
                if kind == "missing-language":
                    question["content"].pop("es")
                elif kind == "missing-rationale":
                    question["content"]["en"]["options"]["A"]["rationale"] = ""
                else:
                    question["content"]["es"]["options"]["Z"] = copy.deepcopy(question["content"]["es"]["options"]["A"])
                self.write_fixture()
                with self.assertRaises((ValueError, KeyError)):
                    self.generate()

    def test_two_and_six_choice_sources_preserve_correct_answer_mapping(self):
        for count in (2, 6):
            with self.subTest(choice_count=count):
                self.banks = copy.deepcopy(self.base_banks)
                question = self.questions()[0]
                correct = next(option for option in question["options"] if option["correct"])
                if count == 2:
                    wrong = next(option for option in question["options"] if not option["correct"])
                    question["options"] = [wrong, correct]
                    keys = {option["key"] for option in question["options"]}
                    for language in importer.LANGS:
                        question["content"][language]["options"] = {key: value for key, value in question["content"][language]["options"].items() if key in keys}
                else:
                    for key in ("E", "F"):
                        question["options"].append({"key": key, "correct": False})
                        for language in importer.LANGS:
                            question["content"][language]["options"][key] = {"text": f"Synthetic fixture distractor {key}", "rationale": f"Synthetic fixture rationale {key}"}
                self.write_fixture()
                generated, snapshots, _, _ = self.generate()
                case = next(case for cases in generated.values() for case in cases if case["source"]["questionId"] == question["id"])
                source = next(source for source in snapshots if source["questionId"] == question["id"])
                step = case["steps"][0]
                self.assertEqual(len(step["options"]), count)
                self.assertEqual(step["best"], correct["key"].lower())
                self.assertEqual({option["id"] for option in step["options"]}, {option["key"].lower() for option in question["options"]})
                self.assertEqual(source["options"], question["options"])
                self.assertEqual(source["status"], question["status"])
                self.assertEqual(sum(option["score"] == 10 for option in step["options"]), 1)

    def test_source_age_keeps_absent_and_ambiguous_ages_unknown(self):
        missing = {language: {"vignette": "A case with no patient age provided."} for language in importer.LANGS}
        self.assertIsNone(importer.source_age(missing))
        ambiguous = {"de": {"vignette": "Ein 40-jähriger und ein 60-jähriger Patient."}, "en": {"vignette": "A 40-year-old and a 60-year-old patient."}, "es": {"vignette": "Un paciente de 40 años y otro de 60 años."}}
        self.assertIsNone(importer.source_age(ambiguous))
        agreed = {"de": {"vignette": "Eine 48-jährige Patientin."}, "en": {"vignette": "A 48-year-old patient."}, "es": {"vignette": "Una paciente de 48 años."}}
        self.assertEqual(importer.source_age(agreed), 48)
        conflicting = copy.deepcopy(agreed)
        conflicting["en"]["vignette"] = "A 58-year-old patient."
        self.assertIsNone(importer.source_age(conflicting))


if __name__ == "__main__":
    unittest.main()
