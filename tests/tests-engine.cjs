'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const E = require('../assets/engine.js');
const areaIds = ['emergency', 'ward', 'clinic', 'endoscopy', 'theatre'];
const catalog = {
  areas: areaIds.map(id => ({ id })),
  cases: areaIds.flatMap(id => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', id + '.json'), 'utf8').replace(/^\uFEFF/, '')))
};
const clone = value => JSON.parse(JSON.stringify(value));
const chosen = catalog.cases[0];
const maximum = c => c.steps.reduce((sum, step) => sum + Math.max(...step.options.map(option => option.score)), 0);
const legacyIds = [
  'ed-colic', 'ed-retention', 'ed-obstructed-infection', 'ed-torsion', 'ed-fournier', 'ed-clot-retention',
  'ward-bleeding', 'ward-aki', 'ward-urine-leak', 'ward-postop-sepsis', 'ward-ileus', 'ward-vte',
  'clinic-psa', 'clinic-luts', 'clinic-haematuria', 'clinic-recurrent-uti', 'clinic-stone-prevention', 'clinic-active-surveillance',
  'endoscopy-papillary', 'endoscopy-cis', 'endoscopy-stricture', 'endoscopy-stent', 'endoscopy-biopsy', 'endoscopy-infected-obstruction',
  'theatre-checklist', 'theatre-side-discrepancy', 'theatre-infected-stone', 'theatre-specimen-label', 'theatre-ureter-injury', 'theatre-postop-handover'
];
const importedCases = catalog.cases.filter(c => c.source);
const authoredCases = catalog.cases.filter(c => !c.source);
const expectedSourceCases = 267;
// Captured from the previous 30-case release, rather than derived from the
// expanded catalog. These completed first answers are stored-progress contracts.
const legacyFirstAnswers = [
  ['clinic-psa', 'assessment', 8], ['clinic-luts', 'assessment', 10],
  ['clinic-haematuria', 'assessment', 7], ['clinic-recurrent-uti', 'assessment', 8],
  ['clinic-stone-prevention', 'assessment', 10], ['clinic-active-surveillance', 'assessment', 10],
  ['ed-colic', 'assessment', 4], ['ed-retention', 'assessment', 4],
  ['ed-obstructed-infection', 'assessment', 2], ['ed-torsion', 'assessment', 2],
  ['ed-fournier', 'assessment', 2], ['ed-clot-retention', 'assessment', 4],
  ['endoscopy-papillary', 'interpretation', 5], ['endoscopy-cis', 'interpretation', 7],
  ['endoscopy-stricture', 'pause', 4], ['endoscopy-stent', 'assessment', 7],
  ['endoscopy-biopsy', 'interpretation', 7], ['endoscopy-infected-obstruction', 'recognition', 3],
  ['theatre-checklist', 'sign-in', 5], ['theatre-side-discrepancy', 'pause', 3],
  ['theatre-infected-stone', 'assessment', 7], ['theatre-specimen-label', 'hold', 3],
  ['theatre-ureter-injury', 'recognition', 4], ['theatre-postop-handover', 'handover', 6],
  ['ward-bleeding', 'assessment', 2], ['ward-aki', 'assessment', 4],
  ['ward-urine-leak', 'assessment', 4], ['ward-postop-sepsis', 'assessment', 2],
  ['ward-ileus', 'assessment', 4], ['ward-vte', 'assessment', 2]
];

test('a seeded schedule is repeatable, unique and balanced across all five areas', () => {
  const before = JSON.stringify(catalog);
  const ids = E.schedule(catalog, '2026-10-05-class-A');
  assert.deepEqual(ids, E.schedule(catalog, '2026-10-05-class-A'));
  assert.equal(ids.length, 10);
  assert.equal(new Set(ids).size, 10);
  for (const area of areaIds) {
    assert.equal(ids.filter(id => catalog.cases.find(c => c.id === id).area === area).length, 2);
  }
  assert.equal(JSON.stringify(catalog), before, 'Scheduling must not mutate source content.');
  const variants = ['alpha', 'beta', 'gamma', 'delta'].map(seed => E.schedule(catalog, seed).join('|'));
  assert.ok(new Set(variants).size > 1, 'Independent seeds should provide different practice schedules.');
});

test('option ordering is deterministic, valid, varied and leaves the catalog unchanged', () => {
  const ids = catalog.cases.map(c => c.id);
  const before = JSON.stringify(catalog);
  const first = E.create(catalog, ids, 'learn', 'options-seed');
  const second = E.create(catalog, ids, 'learn', 'options-seed');
  assert.deepEqual(first, second);
  let changed = false;
  for (const p of first.patients) {
    const c = catalog.cases.find(c => c.id === p.id);
    p.order.forEach((order, index) => {
      const original = c.steps[index].options.map(o => o.id);
      assert.deepEqual([...order].sort(), [...original].sort());
      assert.equal(new Set(order).size, order.length);
      if (order.join('') !== original.join('')) changed = true;
    });
  }
  assert.ok(changed, 'The display order should not always reveal the best choice by position.');
  assert.equal(JSON.stringify(catalog), before);
  assert.ok(E.validSession(first, catalog));
});

test('empty, duplicated and unknown case schedules cannot start', () => {
  assert.throws(() => E.create(catalog, [], 'learn', 'seed'), /Invalid case schedule/);
  assert.throws(() => E.create(catalog, [chosen.id, chosen.id], 'learn', 'seed'), /Invalid case schedule/);
  assert.throws(() => E.create(catalog, ['unknown-case'], 'learn', 'seed'), /Invalid case schedule/);
});

test('an answer counts once and requires acknowledging feedback before another step', () => {
  const s = E.create(catalog, [chosen.id], 'learn', 'seed');
  assert.throws(() => E.next(s, catalog, chosen.id), /Answer first/);
  assert.throws(() => E.answer(s, catalog, chosen.id, 'missing'), /Unknown choice/);
  const step = chosen.steps[0], option = step.options.find(o => o.id === step.best);
  assert.deepEqual(E.answer(s, catalog, chosen.id, option.id), option);
  assert.equal(s.patients[0].score, option.score);
  assert.equal(s.clock, option.minutes);
  assert.equal(s.patients[0].answers.length, 1);
  const after = clone(s);
  assert.throws(() => E.answer(s, catalog, chosen.id, option.id), /Case unavailable/);
  assert.deepEqual(s, after, 'A duplicate click must not add points, time or another answer.');
  assert.ok(E.validSession(s, catalog));
  assert.equal(E.next(s, catalog, chosen.id), false);
  assert.equal(s.patients[0].index, 1);
  assert.equal(s.patients[0].feedback, null);
  assert.ok(E.validSession(s, catalog));
});

test('shift arrivals block early answers and waiting advances to the next arrival', () => {
  const ids = catalog.cases.slice(0, 3).map(c => c.id);
  const s = E.create(catalog, ids, 'shift', 'arrivals');
  assert.deepEqual(s.patients.map(p => p.availableAt), [0, 10, 20]);
  const second = catalog.cases.find(c => c.id === ids[1]);
  const before = clone(s);
  assert.throws(() => E.answer(s, catalog, second.id, second.steps[0].best), /Case unavailable/);
  assert.deepEqual(s, before);
  E.wait(s);
  assert.equal(s.clock, 10);
  s.selected = second.id;
  E.answer(s, catalog, second.id, second.steps[0].best);
  assert.ok(E.validSession(s, catalog));
  E.wait(s);
  assert.equal(s.clock, 20);
  assert.ok(E.validSession(s, catalog));
});

test('mixed choices retain the actual score, elapsed minutes and critical-error count', () => {
  const c = catalog.cases.find(c => c.steps.some(step => step.options.some(o => o.critical)));
  const s = E.create(catalog, [c.id], 'learn', 'mixed');
  let points = 0, minutes = 0, errors = 0;
  c.steps.forEach((step, index) => {
    const option = index === 0
      ? step.options.find(o => o.critical) || step.options.find(o => o.score === 0)
      : step.options.find(o => o.score === 3);
    E.answer(s, catalog, c.id, option.id);
    points += option.score; minutes += option.minutes; errors += Number(option.critical);
    E.next(s, catalog, c.id);
  });
  const record = E.record(s, catalog, c.id);
  assert.equal(record.score, points);
  assert.equal(record.elapsed, minutes);
  assert.equal(record.criticalErrors, errors);
  assert.equal(record.maxScore, maximum(c));
  assert.ok(E.validSession(s, catalog));
});

test('case records require completion and copy their answers for safe export', () => {
  const s = E.create(catalog, [chosen.id], 'learn', 'record');
  assert.throws(() => E.record(s, catalog, chosen.id), /Incomplete case/);
  chosen.steps.forEach((step, index) => {
    E.answer(s, catalog, chosen.id, step.best);
    assert.equal(E.next(s, catalog, chosen.id), index === chosen.steps.length - 1);
  });
  assert.ok(s.finished);
  const record = E.record(s, catalog, chosen.id);
  assert.equal(record.caseId, chosen.id);
  assert.equal(record.area, chosen.area);
  assert.equal(record.score, maximum(chosen));
  assert.equal(record.maxScore, maximum(chosen));
  assert.equal(record.criticalErrors, 0);
  assert.equal(record.answers.length, chosen.steps.length);
  assert.ok(Number.isFinite(Date.parse(record.completedAt)));
  record.answers[0].score = -1;
  assert.equal(s.patients[0].answers[0].score, 10, 'Export copies must not change the stored session.');
  assert.throws(() => E.answer(s, catalog, chosen.id, 'a'), /Session finished/);
});

test('the complete case library can finish, with maxima and elapsed time calculated from its actual steps', () => {
  assert.equal(catalog.cases.length, authoredCases.length + expectedSourceCases);
  assert.ok(legacyIds.every(id => authoredCases.some(c => c.id === id)), 'The 30 original story cases are still authored cases');
  const s = E.create(catalog, catalog.cases.map(c => c.id), 'learn', 'whole-library');
  let expectedMinutes = 0;
  for (const c of catalog.cases) {
    s.selected = c.id;
    for (const step of c.steps) {
      const best = step.options.find(o => o.id === step.best);
      assert.equal(best.score, 10);
      assert.equal(best.critical, false);
      expectedMinutes += best.minutes;
      E.answer(s, catalog, c.id, best.id);
      assert.ok(E.validSession(s, catalog), 'Answered state must remain restorable: ' + c.id);
      E.next(s, catalog, c.id);
      assert.ok(E.validSession(s, catalog), 'Acknowledged state must remain restorable: ' + c.id);
    }
    const record = E.record(s, catalog, c.id);
    assert.equal(record.score, record.maxScore);
    assert.equal(record.criticalErrors, 0);
  }
  assert.ok(s.finished);
  assert.equal(s.patients.reduce((sum, p) => sum + p.score, 0), catalog.cases.reduce((sum, c) => sum + maximum(c), 0));
  assert.equal(s.clock, expectedMinutes);
  assert.equal(s.patients.filter(p => p.finished).length, catalog.cases.length);
});

test('all 267 imported source questions retain one decision and every original four-choice or five-choice option', () => {
  assert.equal(importedCases.length, expectedSourceCases);
  assert.equal(importedCases.filter(c => c.steps[0].options.length === 4).length, 223);
  assert.equal(importedCases.filter(c => c.steps[0].options.length === 5).length, 44);
  for (const c of importedCases) {
    assert.ok(c.source, 'An imported question must retain source provenance: ' + c.id);
    assert.equal(c.steps.length, 1, c.id + ' must not invent extra clinical decisions');
    const step = c.steps[0];
    assert.ok([4, 5].includes(step.options.length), c.id + ' must preserve the source choice count');
    assert.equal(new Set(step.options.map(option => option.id)).size, step.options.length);
    for (const option of step.options) assert.equal(option.score, option.id === step.best ? 10 : 0);
    const session = E.create(catalog, [c.id], 'learn', 'source-options-' + c.id);
    assert.deepEqual([...session.patients[0].order[0]].sort(), step.options.map(option => option.id).sort());
    assert.ok(E.validSession(session, catalog));
    const last = step.options.at(-1);
    E.answer(session, catalog, c.id, last.id);
    assert.equal(session.patients[0].answers[0].optionId, last.id);
    assert.equal(session.patients[0].score, last.score);
    assert.equal(session.clock, last.minutes);
    assert.ok(E.validSession(session, catalog));
    assert.equal(E.next(session, catalog, c.id), true);
    const record = E.record(session, catalog, c.id);
    assert.equal(record.answers.length, 1);
    assert.equal(record.answers[0].optionId, last.id);
    assert.equal(record.score, last.score);
    assert.equal(record.maxScore, maximum(c));
    assert.equal(record.criticalErrors, Number(last.critical));
    assert.ok(E.validSession(clone(session), catalog), 'Every source choice must survive JSON storage: ' + c.id);
    const truncated = clone(session);
    truncated.patients[0].order[0].pop();
    assert.equal(E.validSession(truncated, catalog), false, 'A lost final display choice must be rejected: ' + c.id);
  }
});

test('a real five-choice source question preserves answer e in its saved session and exported record', () => {
  const c = importedCases.find(c => c.steps[0].options.length === 5);
  assert.ok(c, 'The built question bank must include five-choice questions');
  const step = c.steps[0], fifth = step.options.find(option => option.id === 'e');
  assert.ok(fifth, 'The fifth source answer must keep its e mapping');
  const session = E.create(catalog, [c.id], 'learn', 'five-choice-save-export');
  assert.equal(session.patients[0].order[0].length, 5);
  assert.ok(session.patients[0].order[0].includes('e'));
  E.answer(session, catalog, c.id, 'e');
  const restored = clone(session);
  assert.ok(E.validSession(restored, catalog));
  assert.equal(restored.patients[0].feedback, 'e');
  E.next(restored, catalog, c.id);
  const record = clone(E.record(restored, catalog, c.id));
  assert.equal(record.answers[0].optionId, 'e');
  assert.equal(record.score, fifth.score);
  assert.equal(record.maxScore, maximum(c));
  assert.ok(E.validSession(restored, catalog));
});

test('variable cases support one through eight steps and two through six choices without assuming the first answer is best', () => {
  const step = (id, count) => ({
    id, best: String.fromCharCode(96 + count),
    options: Array.from({ length: count }, (_, i) => ({
      id: String.fromCharCode(97 + i), score: i === count - 1 ? 10 : i === 0 ? 3 : 0,
      minutes: i + 2, critical: false
    }))
  });
  const small = { id: 'fixture-one-step', area: 'clinic', steps: [step('decision', 2)] };
  const long = { id: 'fixture-eight-steps', area: 'theatre', steps: [2, 3, 4, 5, 6, 2, 4, 6].map((count, i) => step('decision-' + i, count)) };
  const variable = { areas: areaIds.map(id => ({ id })), cases: [small, long] };
  const session = E.create(variable, [small.id, long.id], 'learn', 'variable-boundaries');
  let minutes = 0;
  for (const c of variable.cases) {
    c.steps.forEach((s, i) => {
      const option = s.options.find(o => o.id === s.best);
      assert.equal(session.patients.find(p => p.id === c.id).order[i].length, s.options.length);
      E.answer(session, variable, c.id, option.id); minutes += option.minutes;
      assert.ok(E.validSession(session, variable));
      assert.equal(E.next(session, variable, c.id), i === c.steps.length - 1);
    });
    const record = E.record(session, variable, c.id);
    assert.equal(record.answers.length, c.steps.length);
    assert.equal(record.maxScore, c === small ? 10 : 80);
    assert.equal(record.score, record.maxScore);
    assert.ok(E.validSession(clone(session), variable));
  }
  assert.ok(session.finished);
  assert.equal(session.clock, minutes);
  assert.equal(session.patients.reduce((sum, p) => sum + p.score, 0), 90);
});

test('all 30 original case IDs and an existing serialized partial shift remain resumable after expansion', () => {
  for (const id of legacyIds) assert.ok(catalog.cases.some(c => c.id === id), 'Original case missing: ' + id);
  const saved = {
    version: 2, mode: 'learn', seed: 'saved-before-question-bank-upgrade', clock: 4, selected: 'ed-colic', finished: false,
    patients: [{
      id: 'ed-colic', index: 1, answers: [{ stepId: 'assessment', optionId: 'a', score: 10, minutes: 4 }],
      score: 10, elapsed: 4, criticalErrors: 0, availableAt: 0, feedback: null, finished: false,
      order: [['c', 'a', 'b'], ['b', 'c', 'a'], ['a', 'b', 'c']]
    }]
  };
  const restored = clone(saved);
  assert.ok(E.validSession(restored, catalog), 'A real pre-upgrade progress shape must still be accepted');
  const c = catalog.cases.find(c => c.id === restored.selected);
  for (const s of c.steps.slice(restored.patients[0].index)) {
    E.answer(restored, catalog, c.id, s.best);
    E.next(restored, catalog, c.id);
  }
  assert.ok(restored.finished);
  assert.ok(E.validSession(restored, catalog));
  assert.deepEqual(restored.patients[0].answers[0], saved.patients[0].answers[0]);
  assert.equal(E.record(restored, catalog, c.id).maxScore, maximum(c));
  const oldCatalog = { areas: catalog.areas, cases: legacyIds.map(id => catalog.cases.find(c => c.id === id)) };
  const legacySession = E.create(oldCatalog, legacyIds, 'learn', 'all-old-identifiers');
  assert.equal(legacyFirstAnswers.length, legacyIds.length);
  for (const [id, stepId, minutes] of legacyFirstAnswers) {
    const patient = legacySession.patients.find(p => p.id === id);
    patient.answers = [{ stepId, optionId: 'a', score: 10, minutes }];
    patient.index = 1; patient.score = 10; patient.elapsed = minutes;
    legacySession.clock += minutes;
  }
  assert.ok(E.validSession(clone(legacySession), catalog), 'Adding new IDs must not invalidate original progress');
});

test('restored sessions reject inconsistent answers, progress and shuffled option lists', async t => {
  const base = E.create(catalog, [chosen.id], 'learn', 'restore');
  E.answer(base, catalog, chosen.id, chosen.steps[0].best);
  assert.ok(E.validSession(base, catalog));
  const mutations = {
    'changed score': s => { s.patients[0].score += 1; },
    'changed elapsed': s => { s.patients[0].elapsed += 1; },
    'changed critical error count': s => { s.patients[0].criticalErrors += 1; },
    'skipped step': s => { s.patients[0].index += 1; },
    'forged answer score': s => { s.patients[0].answers[0].score = 99; },
    'forged answer time': s => { s.patients[0].answers[0].minutes += 1; },
    'wrong step id': s => { s.patients[0].answers[0].stepId = 'unknown'; },
    'unknown option id': s => { s.patients[0].answers[0].optionId = 'unknown'; },
    'feedback differs from answer': s => { s.patients[0].feedback = 'b'; },
    'duplicate display option': s => { s.patients[0].order[0][1] = s.patients[0].order[0][0]; },
    'unknown display option': s => { s.patients[0].order[0][0] = 'unknown'; },
    'false completion': s => { s.finished = true; },
    'unknown selected patient': s => { s.selected = 'unknown'; },
    'duplicate patient': s => { s.patients.push(clone(s.patients[0])); },
    'unknown patient': s => { s.patients[0].id = 'unknown'; },
    'invalid mode': s => { s.mode = 'unknown'; },
    'wrong version': s => { s.version = 1; }
  };
  for (const [name, mutate] of Object.entries(mutations)) {
    await t.test(name, () => {
      const s = clone(base); mutate(s);
      assert.equal(E.validSession(s, catalog), false, name);
    });
  }
});

test('restored sessions reject impossible simulation time and modified arrivals', async t => {
  const base = E.create(catalog, catalog.cases.slice(0, 3).map(c => c.id), 'shift', 'time-regression');
  E.answer(base, catalog, chosen.id, chosen.steps[0].best);
  const mutations = {
    'negative clock': s => { s.clock = -1; },
    'fractional clock': s => { s.clock += 0.5; },
    'non-finite clock': s => { s.clock = Infinity; },
    'clock less than completed answer time': s => { s.clock = 0; },
    'negative arrival': s => { s.patients[0].availableAt = -10; },
    'fractional arrival': s => { s.patients[1].availableAt = 10.5; },
    'modified arrival': s => { s.patients[1].availableAt = 0; },
    'non-string seed': s => { s.seed = {}; }
  };
  for (const [name, mutate] of Object.entries(mutations)) {
    await t.test(name, () => {
      const s = clone(base); mutate(s);
      assert.equal(E.validSession(s, catalog), false, name);
    });
  }
  const learn = E.create(catalog, [chosen.id], 'learn', 'learn-time');
  learn.patients[0].availableAt = 10;
  assert.equal(E.validSession(learn, catalog), false, 'Learning-mode cases are available immediately.');
});

test('malformed stored JSON-shaped inputs never throw while validating', () => {
  const bad = [null, undefined, {}, [], 'text', 42, { version: 2 }, { version: 2, patients: [null] }];
  for (const value of bad) assert.equal(E.validSession(value, catalog), false);
});

test('duty schedules draw only that duty, repeat for the same seed and mix topics', () => {
  for (const duty of E.DUTIES) {
    const pool = catalog.cases.filter(c => c.duty === duty);
    assert.ok(pool.length >= 10, duty + ' needs enough cases for a full ten-case session');
    const ids = E.scheduleDuty(catalog, 'duty-' + duty, duty);
    assert.deepEqual(ids, E.scheduleDuty(catalog, 'duty-' + duty, duty));
    assert.equal(ids.length, 10);
    assert.equal(new Set(ids).size, 10);
    assert.ok(ids.every(id => catalog.cases.find(c => c.id === id).duty === duty), duty + ' must not draw other duties');
    const topics = new Set(ids.map(id => { const c = catalog.cases.find(c => c.id === id); return c.source ? c.source.domain : 'story-' + c.area; }));
    assert.ok(topics.size >= Math.min(4, new Set(pool.map(c => c.source ? c.source.domain : 'story-' + c.area)).size), duty + ' sessions should rotate through topics');
    const session = E.create(catalog, ids, 'shift', 'duty-' + duty);
    assert.ok(E.validSession(Object.assign(session, { duty }), catalog));
  }
  assert.ok(new Set(['a', 'b', 'c'].map(seed => E.scheduleDuty(catalog, seed, 'night').join('|'))).size > 1);
  assert.throws(() => E.scheduleDuty(catalog, 'seed', 'weekend'), /Unknown duty/);
  assert.equal(catalog.cases.filter(c => !E.DUTIES.includes(c.duty)).length, 0, 'Every case needs a duty');
});

