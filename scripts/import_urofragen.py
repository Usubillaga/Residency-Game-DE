#!/usr/bin/env python3
"""Reproduce all 267 Urofragen cases without executing archive contents."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import unicodedata
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('de', 'en', 'es')
AREAS = ('emergency', 'ward', 'clinic', 'endoscopy', 'theatre')
GUIDES = {
    'andrologie': ('Sexual and Reproductive Health', 'sexual-and-reproductive-health'),
    'funktionell': ('Management of Non-neurogenic Male LUTS', 'management-of-non-neurogenic-male-luts'),
    'hodentumor': ('Testicular Cancer', 'testicular-cancer'),
    'infektiologie': ('Urological Infections', 'urological-infections'),
    'kinderurologie': ('Paediatric Urology', 'paediatric-urology'),
    'mibc': ('Muscle-invasive and Metastatic Bladder Cancer', 'muscle-invasive-and-metastatic-bladder-cancer'),
    'nierenzellkarzinom': ('Renal Cell Carcinoma', 'renal-cell-carcinoma'),
    'nmibc': ('Non-muscle-invasive Bladder Cancer', 'non-muscle-invasive-bladder-cancer'),
    'operativ': ('Guidelines: surgical topics', ''),
    'peniskarzinom': ('Penile Cancer', 'penile-cancer'),
    'prostatakarzinom': ('Prostate Cancer', 'prostate-cancer'),
    'rekonstruktion': ('Urethral Strictures', 'urethral-strictures'),
    'trauma': ('Urological Trauma', 'urological-trauma'),
    'urethrakarzinom': ('Primary Urethral Carcinoma', 'primary-urethral-carcinoma'),
    'urolithiasis': ('Urolithiasis', 'urolithiasis'),
    'utuc': ('Upper Urinary Tract Urothelial Cell Carcinoma', 'upper-urinary-tract-urothelial-cell-carcinoma'),
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def clinical_fingerprint(question, language):
    def normalize(text):
        return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())
    content = question['content'][language]
    choices = sorted((normalize(content['options'][option['key']]['text']), option['correct']) for option in question['options'])
    return digest([normalize(content['vignette']), normalize(content['lead_in']), choices])


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def source_age(content):
    recorded = set()
    for language, pattern in (
        ('de', r'(?<!\d)(\d{1,3})[\s-]*(?:jährige[rsnm]?|Jahre\s+alt)'),
        ('en', r'(?<!\d)(\d{1,3})[- ]year[- ]old'),
        ('es', r'(?<!\d)(\d{1,3})\s+años'),
    ):
        ages = {int(match[1]) for match in re.finditer(pattern, content[language]['vignette'], re.I)}
        if len(ages) > 1:
            return None
        recorded.update(ages)
    return next(iter(recorded)) if len(recorded) == 1 and 0 <= next(iter(recorded)) <= 120 else None


def approved_languages(question):
    approval = question.get('review', {}).get('approval') or {}
    if approval.get('question_version') != question.get('version'):
        return []
    # A German sign-off is not an approval of the English/Spanish translations.
    return sorted(set(approval.get('languages', [])) & set(LANGS))


def generate(archive_path, plan_path=ROOT / 'data/import-selection.json'):
    plan = read_json(plan_path)
    rows = plan['selection'] if isinstance(plan, dict) else plan
    require(len(rows) == 267, 'Selection must contain all 267 source questions')
    require(set(row['area'] for row in rows) == set(AREAS), 'All five departments must be represented')
    require(len({row['questionId'] for row in rows}) == 267, 'Source question IDs must be unique')
    generated = {area: [] for area in AREAS}
    snapshots, by_bank = [], {}
    with ZipFile(archive_path) as archive:
        require(len(set(archive.namelist())) == len(archive.namelist()), 'Archive contains duplicate member names')
        require(archive.getinfo('data/domains.json').file_size < 100000, 'Domain metadata too large')
        domains = json.loads(archive.read('data/domains.json').decode('utf-8-sig'))
        labels = {domain['slug']: domain['label'] for domain in domains['domains']}
        all_source_ids = set()
        fingerprints = {language: set() for language in LANGS}
        for domain in labels:
            member = 'data/fragen/' + domain + '.json'
            require(archive.getinfo(member).file_size < 4000000, 'Oversized question bank')
            bank = json.loads(archive.read(member).decode('utf-8-sig'))
            ids = [question['id'] for question in bank['fragen']]
            require(len(set(ids)) == len(ids) and not all_source_ids.intersection(ids), 'Duplicate source question IDs')
            all_source_ids.update(ids)
            for question in bank['fragen']:
                for language in LANGS:
                    fingerprint = clinical_fingerprint(question, language)
                    require(fingerprint not in fingerprints[language], f'Duplicate clinical question content in {language}: {question["id"]}')
                    fingerprints[language].add(fingerprint)
            by_bank[member] = {question['id']: question for question in bank['fragen']}
        require(all_source_ids == {row['questionId'] for row in rows}, 'Import must cover every source question exactly once')
        for index, row in enumerate(rows):
            member = row['sourcePath']
            parts = PurePosixPath(member).parts
            require(len(parts) == 3 and parts[:2] == ('data', 'fragen') and parts[-1].endswith('.json') and '..' not in parts, 'Selection may read only data/fragen/*.json')
            if member not in by_bank:
                require(archive.getinfo(member).file_size < 4000000, f'Oversized question bank: {member}')
                bank = json.loads(archive.read(member).decode('utf-8-sig'))
                require(len({question['id'] for question in bank['fragen']}) == len(bank['fragen']), f'Duplicate IDs in {member}')
                by_bank[member] = {question['id']: question for question in bank['fragen']}
            question = by_bank[member][row['questionId']]
            domain = question['taxonomy']['domain']
            require(question['status'] in ('published', 'draft'), f'Unsupported source status: {question["id"]}')
            require(question['type'] == 'single_best_answer', 'Only single-best-answer questions are supported')
            options = question['options']
            require(2 <= len(options) <= 6 and sum(option['correct'] is True for option in options) == 1, 'Exactly one correct option is required')
            keys = [option['key'] for option in options]
            require(len(set(keys)) == len(keys) and all(re.fullmatch('[A-F]', key) for key in keys), 'Unsupported option keys')
            content = question['content']
            for language in LANGS:
                block = content[language]
                texts = [block['vignette'], block['lead_in'], block['explanation']['core'], block['explanation']['teaching_point']]
                texts += [block['options'][key][field] for key in keys for field in ('text', 'rationale')]
                require(all(isinstance(text, str) and text.strip() and '\ufffd' not in text for text in texts), f'Incomplete or damaged {language} in {question["id"]}')
                require(set(block['options']) == set(keys), 'Translated options differ from original option keys')
            approval = approved_languages(question)
            source = {'questionId': question['id'], 'archivePath': member, 'domain': domain, 'version': question['version'], 'contentSha256': digest(content), 'status': question['status'], 'evidenceFlag': question.get('evidence', {}).get('flag') is True, 'reviewStatus': question.get('review', {}).get('clinical_review_status', 'draft_not_reviewed' if question['status'] == 'draft' else 'pending_independent_review'), 'clinicalSignoffLanguages': approval,
                      'originalSources': question.get('sources', []), 'evidenceNotes': [{'language': language, 'text': content[language]['flag_note']} for language in LANGS if content[language].get('flag_note')]}
            case = {
                'id': 'bank-' + question['id'], 'area': row['area'],
                'level': max(1, min(3, int(question.get('difficulty_estimated', 2)))),
                'acuity': 'routine' if row.get('acuity') == 'stable' else row.get('acuity', 'urgent' if row['area'] == 'emergency' else 'routine'),
                'patient': {'name': 'Uro-' + str(index + 1).zfill(3), 'age': source_age(content)},
                'topic': {language: labels[domain][language] for language in LANGS},
                'title': {language: content[language]['lead_in'] for language in LANGS},
                'presenting': {language: content[language]['vignette'] for language in LANGS},
                'vitals': None,
                'objectives': {language: [labels[domain][language] + ': ' + content[language]['lead_in']] for language in LANGS},
                'steps': [{'id': 'source-decision', 'kind': 'decision', 'prompt': {language: content[language]['lead_in'] for language in LANGS}, 'best': next(option['key'].lower() for option in options if option['correct']),
                           'options': [{'id': option['key'].lower(), 'text': {language: content[language]['options'][option['key']]['text'] for language in LANGS}, 'score': 10 if option['correct'] else 0, 'minutes': 5, 'critical': False,
                                        'feedback': {language: content[language]['options'][option['key']]['rationale'] for language in LANGS}} for option in options]}],
                'takeaway': {language: content[language]['explanation']['core'] + '\n\n' + content[language]['explanation']['teaching_point'] for language in LANGS},
                'references': ['bank-guide-' + domain], 'source': source,
            }
            generated[row['area']].append(case)
            snapshots.append({**source, 'options': options, 'content': content, 'sources': question.get('sources', [])})
    used_domains = {row['domain'] for row in snapshots}
    require(used_domains == set(GUIDES), 'Selection must cover all 16 source domains')
    references = [{'id': 'bank-guide-' + domain, 'title': 'EAU ' + GUIDES[domain][0], 'url': 'https://uroweb.org/guidelines' + ('/' + GUIDES[domain][1] if GUIDES[domain][1] else ''), 'checked': '2026-10-05', 'scope': 'Related primary guideline for this topic. Original question citations and language-specific review status are preserved in data/imported-source.json; no new clinical approval is implied.'} for domain in sorted(used_domains)]
    manifest = {'archiveName': Path(archive_path).name, 'archiveSha256': hashlib.sha256(Path(archive_path).read_bytes()).hexdigest(), 'importedCases': 267, 'legacyCases': 30, 'totalCases': 297, 'languages': list(LANGS), 'domains': sorted(used_domains), 'casesPerArea': dict(Counter(row['area'] for row in rows)), 'sourceStatuses': dict(Counter(row['status'] for row in snapshots)), 'flaggedSourceQuestions': sum(row['evidenceFlag'] for row in snapshots), 'selectionSha256': digest(rows), 'contentPolicy': 'All 267 original vignettes, questions, options, rationales and explanations are preserved once in DE/EN/ES. Drafts and evidence flags are retained. No archive scripts are executed. Missing or ambiguous ages and vital signs remain null. Uro identifiers represent teaching cases, including vignettes comparing multiple patients. Five minutes per answer are game time only.'}
    return generated, snapshots, references, manifest


def run(archive_path, check=False):
    generated, snapshots, references, manifest = generate(archive_path)
    updates = {}
    legacy_count = 0
    for area in AREAS:
        path = ROOT / 'data' / (area + '.json')
        existing = read_json(path)
        legacy = [case for case in existing if not case.get('source')]
        legacy_count += len(legacy)
        updates[path] = legacy + generated[area]
    require(legacy_count == 30, 'Expected the unchanged 30 original expanded cases')
    updates.update({ROOT / 'data/imported-source.json': snapshots, ROOT / 'data/refs-imported.json': references, ROOT / 'data/import-manifest.json': manifest})
    if check:
        for path, expected in updates.items():
            require(read_json(path) == expected, f'Imported data differs from source: {path.name}')
        print('Verified: 267 source cases + 30 legacy cases = 297, all three languages match the archive.')
    else:
        for path, value in updates.items():
            write_json(path, value)
        print('Imported: all 267 source cases once; 297 total; 16 domains; DE/EN/ES preserved.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path, help='The supplied Urofragen-GitHub-DE-EN-ES ZIP')
    parser.add_argument('--check', action='store_true', help='Verify the existing import without changing files')
    args = parser.parse_args()
    try:
        run(args.archive, args.check)
    except (ValueError, KeyError, OSError) as exc:
        print('Import error: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
