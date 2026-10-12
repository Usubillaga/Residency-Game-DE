"""Bank size, spoiler removal and compatibility of historical progress."""
import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('manage_bank', ROOT / 'scripts/manage.py')
manage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage)


class QuestionBankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases, cls.references = manage.load_and_validate(ROOT)
        cls.all_cases, _ = manage.load_and_validate(ROOT, include_archive=True)

    def test_exactly_500_playable_decisions_and_50_new_anatomy_questions(self):
        self.assertEqual(sum(len(c['steps']) for c in self.cases), 500)
        anatomy = [c for c in self.cases if c.get('subject') == 'anatomy']
        self.assertEqual(len(anatomy), 50)
        self.assertEqual(Counter(c['anatomyGroup'] for c in anatomy),
                         dict(kidney=10, ureter=8, bladder=6, prostate=7, penis=7, testis=7, nerves=5))
        self.assertTrue(all('objectives' not in c and len(c['steps']) == 1 for c in anatomy))
        self.assertEqual(sum('source' in c for c in self.cases), 267)
        self.assertEqual(sum(not c.get('source') and len(c['steps']) > 1 for c in self.cases), 50)

    def test_anatomy_requires_translated_clinical_correlation(self):
        anatomy = [c for c in self.cases if c.get('subject') == 'anatomy']
        self.assertEqual(Counter(c['clinicalContext']['kind'] for c in anatomy),
                         dict(operation=31, case=19))
        self.assertTrue(all(set(c['clinicalContext']['label']) == {'de', 'en', 'es'} for c in anatomy))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'data', root / 'data')
            area = anatomy[0]['area']
            path = root / 'data' / f'{area}.json'
            rows = manage.read_json(path)
            case = next(c for c in rows if c['id'] == anatomy[0]['id'])
            original = copy.deepcopy(case['clinicalContext'])
            for context, error in ((None, 'clinicalContext: anatomy requires'),
                                   ({'kind': 'recall', 'label': original['label']}, 'expected operation or case'),
                                   ({'kind': original['kind'], 'label': {'de': 'Nierenbiopsie'}}, 'clinicalContext.label')):
                with self.subTest(context=context):
                    case['clinicalContext'] = context
                    manage.write_json(path, rows)
                    with self.assertRaisesRegex(manage.ValidationError, error):
                        manage.load_and_validate(root, check_assets=False)

    def test_question_contract_rejects_count_drift_and_duplicate_content(self):
        changed = copy.deepcopy(self.cases)
        changed[0]['steps'].append(copy.deepcopy(changed[0]['steps'][0]))
        with self.assertRaisesRegex(manage.ValidationError, 'expected 500 playable questions, found 501'):
            manage.validate_question_contract(ROOT, changed)
        changed = copy.deepcopy(self.cases)
        singles = [c for c in changed if len(c['steps']) == 1]
        singles[1]['presenting'] = copy.deepcopy(singles[0]['presenting'])
        singles[1]['steps'] = copy.deepcopy(singles[0]['steps'])
        singles[1]['steps'][0]['options'].reverse()
        with self.assertRaisesRegex(manage.ValidationError, 'duplicate question'):
            manage.validate_question_contract(ROOT, changed)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manage.write_json(root / 'data/question-contract.json', {'questions': 500, 'minimumAnatomy': 51})
            with self.assertRaisesRegex(manage.ValidationError, 'at least 51 anatomy questions, found 50'):
                manage.validate_question_contract(root, self.cases)

    def test_archived_cases_are_validated_but_not_playable(self):
        active_ids = {c['id'] for c in self.cases}
        historical = [c for c in self.all_cases if c.get('archived')]
        self.assertEqual(len(historical), 101)
        self.assertFalse(active_ids & {c['id'] for c in historical})
        self.assertEqual(sum(len(c['steps']) for c in historical), 101)
        self.assertTrue(all(c['steps'][0]['best'] in [o['id'] for o in c['steps'][0]['options']] for c in historical))
        self.assertTrue(all(not c.get('archived') for c in self.cases))

    def test_30_source_linked_staging_trauma_cases_and_14_edition_labelled_guides(self):
        schemas, _, _ = manage.load_visuals(ROOT, self.cases)
        guides = manage.load_classifications(ROOT, self.cases, self.references, schemas)
        self.assertEqual(Counter(g['kind'] for g in guides), dict(tumour=9, trauma=5))
        new = [c for c in self.cases if c.get('classification')]
        self.assertEqual(len(new), 30)
        self.assertEqual(Counter(c['subject'] for c in new), dict(staging=21, trauma=9))
        self.assertEqual(sum(len(g['cases']) for g in guides), 30)
        self.assertTrue(all(len(c['steps']) == 1 and len(c['steps'][0]['options']) == 4 for c in new))
        self.assertTrue(all(c['clinicalContext']['kind'] in ('operation', 'case') and
                            not c.get('objectives') and c['clinicalSignoffLanguages'] == [] for c in new))
        self.assertTrue(all(g['edition'] and g['references'] and g['clinicalSignoffLanguages'] == [] for g in guides))

    def test_classification_validation_rejects_missing_sources_schemas_and_case_links(self):
        schemas, _, _ = manage.load_visuals(ROOT, self.cases)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = manage.read_json(ROOT / 'data/classifications.json')
            for field, bad in (('references', ['unknown']), ('schema', 'unknown'), ('cases', ['unknown'])):
                with self.subTest(field=field):
                    broken = copy.deepcopy(data)
                    broken['guides'][0][field] = bad
                    manage.write_json(root / 'data/classifications.json', broken)
                    with self.assertRaises(manage.ValidationError):
                        manage.load_classifications(root, self.cases, self.references, schemas)

    def test_original_imported_story_and_anatomy_counts_remain_unchanged_and_all_duties_playable(self):
        self.assertEqual(len(self.cases), 402)
        self.assertEqual(sum('source' in c for c in self.cases), 267)
        self.assertEqual(sum(c.get('subject') == 'anatomy' for c in self.cases), 50)
        duties = Counter(manage.case_duty(c) for c in self.cases) if hasattr(manage, 'case_duty') else Counter(c.get('duty') for c in self.cases)
        for duty in ('night', 'board', 'clinic', 'elective', 'dayclinic', 'radiotherapy'):
            self.assertGreaterEqual(duties[duty], 10, duty)

    def test_old_archived_logbook_entry_still_exports_to_analysis(self):
        case = next(c for c in self.all_cases if c.get('archived'))
        step = case['steps'][0]
        option = next(o for o in step['options'] if o['id'] == step['best'])
        record = dict(caseId=case['id'], area=case['area'], score=option['score'], maxScore=10,
                      elapsed=option['minutes'], criticalErrors=0, completedAt='2026-10-10T12:00:00Z',
                      answers=[dict(stepId=step['id'], optionId=option['id'], score=option['score'], minutes=option['minutes'])])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            source = path / 'save.json'
            manage.write_json(source, {'version': 2, 'history': [record]})
            self.assertEqual(manage.analyse(source, path / 'progress.csv', ROOT), 1)
            self.assertIn(case['id'], (path / 'progress.csv').read_text(encoding='utf-8-sig'))
            record['score'] = 999
            manage.write_json(source, {'version': 2, 'history': [record]})
            with self.assertRaises(manage.ValidationError):
                manage.analyse(source, path / 'tampered.csv', ROOT)

    def test_built_catalog_has_no_objectives_including_history(self):
        text = (ROOT / 'assets/catalog.js').read_text()
        catalog = json.loads(text.split('window.NSA_CATALOG = ', 1)[1].removesuffix(';\n'))
        self.assertEqual(catalog['questionCount'], 500)
        self.assertEqual(len(catalog['historyCases']), 101)
        self.assertTrue(all('objectives' not in c for c in catalog['cases'] + catalog['historyCases']))
        self.assertNotIn('"objectives"', text)


if __name__ == '__main__':
    unittest.main()
