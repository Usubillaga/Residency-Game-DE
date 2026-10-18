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
CONTRACT = manage.read_json(ROOT / 'data/question-contract.json')
# The archive is empty since the supplementary questions returned to the bank; tests archive this one in a copy of the data.
ARCHIVED = 'fun-inc-duloxetine-counselling'


def archive_one(directory):
    """Copy the data and move one supplementary question, with its hint and drawing link, into the archive."""
    root = Path(directory)
    shutil.copytree(ROOT / 'data', root / 'data')
    path = root / 'data/clinic.json'
    rows = manage.read_json(path)
    case = next(c for c in rows if c['id'] == ARCHIVED)
    manage.write_json(path, [c for c in rows if c['id'] != ARCHIVED])
    archive = {'date': '2026-10-17', 'reason': {'en': 'Test archive'}, 'cases': [case], 'updates': [], 'hints': {}, 'schemas': {}}
    for name, key in (('attending-hints.json', 'hints'), ('case-schemas.json', 'schemas')):
        data = manage.read_json(root / 'data' / name)
        if ARCHIVED in data:
            archive[key][ARCHIVED] = data.pop(ARCHIVED)
        manage.write_json(root / 'data' / name, data)
    (root / 'data/archive').mkdir(exist_ok=True)
    manage.write_json(root / 'data/archive/supplemental-questions.json', archive)
    contract = manage.read_json(root / 'data/question-contract.json')
    contract['questions'] -= len(case['steps'])
    manage.write_json(root / 'data/question-contract.json', contract)
    return root


class QuestionBankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases, cls.references = manage.load_and_validate(ROOT)
        cls.all_cases, _ = manage.load_and_validate(ROOT, include_archive=True)

    def test_playable_decisions_match_the_contract_and_50_new_anatomy_questions(self):
        self.assertEqual(sum(len(c['steps']) for c in self.cases), CONTRACT['questions'])
        anatomy = [c for c in self.cases if c.get('subject') == 'anatomy']
        self.assertEqual(len(anatomy), 50)
        self.assertEqual(Counter(c['anatomyGroup'] for c in anatomy),
                         dict(kidney=10, ureter=8, bladder=6, prostate=7, penis=7, testis=7, nerves=5))
        self.assertTrue(all('objectives' not in c and len(c['steps']) == 1 for c in anatomy))
        self.assertEqual(sum('source' in c for c in self.cases), 267)
        self.assertEqual(sum(not c.get('source') and len(c['steps']) > 1 for c in self.cases), 50)

    def test_male_citrate_threshold_matches_eau_not_a_generic_2_5_cutoff(self):
        case = next(c for c in self.cases if c['id'] == 'bank-uro-lit-00003')
        answer = next(o for o in case['steps'][0]['options'] if o['id'] == 'd')
        for language, threshold in [('de', '1,7 mmol/d'), ('en', '1.7 mmol/day'), ('es', '1,7 mmol/día')]:
            with self.subTest(language=language):
                self.assertIn(threshold, answer['feedback'][language])
                self.assertNotRegex(answer['feedback'][language], r'2[,.]5')
        self.assertEqual(case['steps'][0]['best'], 'd')
        sources = {r['id']: r for r in self.references}
        self.assertIn('eau-urolithiasis-metabolic-2026', sources)
        source = sources['eau-urolithiasis-metabolic-2026']
        self.assertEqual(source['url'], 'https://uroweb.org/guidelines/urolithiasis/chapter/metabolic-evaluation-and-recurrence-prevention')

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
        target = CONTRACT['questions']
        with self.assertRaisesRegex(manage.ValidationError, f'expected {target} playable questions, found {target + 1}'):
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
            manage.write_json(root / 'data/question-contract.json', {'questions': target, 'minimumAnatomy': 51})
            with self.assertRaisesRegex(manage.ValidationError, 'at least 51 anatomy questions, found 50'):
                manage.validate_question_contract(root, self.cases)

    def test_no_question_is_archived_and_an_archived_question_is_validated_but_not_playable(self):
        self.assertFalse((ROOT / 'data/archive/supplemental-questions.json').exists())
        self.assertFalse([c for c in self.all_cases if c.get('archived')])
        with tempfile.TemporaryDirectory() as directory:
            root = archive_one(directory)
            cases, _ = manage.load_and_validate(root, check_assets=False)
            all_cases, _ = manage.load_and_validate(root, check_assets=False, include_archive=True)
            historical = [c for c in all_cases if c.get('archived')]
            self.assertEqual([c['id'] for c in historical], [ARCHIVED])
            self.assertNotIn(ARCHIVED, {c['id'] for c in cases})
            self.assertTrue(all(not c.get('archived') for c in cases))

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
        groups = Counter('imported' if 'source' in c else 'anatomy' if c.get('subject') == 'anatomy' else
                         'classification' if c.get('classification') else 'story' if len(c['steps']) > 1 else 'single'
                         for c in self.cases)
        # 30 + 20 stories; 136 single questions: 106 supplementary (protocols, side effects, continence, radiotherapy,
        # guideline topics) and 30 new ones on emergencies, oncology and drugs.
        self.assertEqual(groups, dict(imported=267, anatomy=50, classification=30, story=50, single=136))
        self.assertEqual(Counter(c['id'].split('-')[1] for c in self.cases if c['id'].startswith(('q-emg-', 'q-onc-', 'q-drug-'))),
                         dict(emg=10, onc=10, drug=10))
        self.assertEqual(sum('source' in c for c in self.cases), 267)
        self.assertEqual(sum(c.get('subject') == 'anatomy' for c in self.cases), 50)
        duties = Counter(manage.case_duty(c) for c in self.cases) if hasattr(manage, 'case_duty') else Counter(c.get('duty') for c in self.cases)
        for duty in ('night', 'board', 'clinic', 'elective', 'dayclinic', 'radiotherapy'):
            self.assertGreaterEqual(duties[duty], 10, duty)

    def test_old_archived_logbook_entry_still_exports_to_analysis(self):
        case = next(c for c in self.all_cases if c['id'] == ARCHIVED)
        step = case['steps'][0]
        option = next(o for o in step['options'] if o['id'] == step['best'])
        record = dict(caseId=case['id'], area=case['area'], score=option['score'], maxScore=10,
                      elapsed=option['minutes'], criticalErrors=0, completedAt='2026-10-10T12:00:00Z',
                      answers=[dict(stepId=step['id'], optionId=option['id'], score=option['score'], minutes=option['minutes'])])
        with tempfile.TemporaryDirectory() as directory:
            root, path = archive_one(directory), Path(directory)
            source = path / 'save.json'
            manage.write_json(source, {'version': 2, 'history': [record]})
            self.assertEqual(manage.analyse(source, path / 'progress.csv', root), 1)
            self.assertIn(case['id'], (path / 'progress.csv').read_text(encoding='utf-8-sig'))
            record['score'] = 999
            manage.write_json(source, {'version': 2, 'history': [record]})
            with self.assertRaises(manage.ValidationError):
                manage.analyse(source, path / 'tampered.csv', root)

    def test_built_catalog_has_no_objectives_including_history(self):
        text = (ROOT / 'assets/catalog.js').read_text()
        catalog = json.loads(text.split('window.NSA_CATALOG = ', 1)[1].removesuffix(';\n'))
        self.assertEqual(catalog['questionCount'], CONTRACT['questions'])
        self.assertEqual(catalog['historyCases'], [])
        self.assertTrue(all('objectives' not in c for c in catalog['cases'] + catalog['historyCases']))
        self.assertNotIn('"objectives"', text)


if __name__ == '__main__':
    unittest.main()
