'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const E = require('../assets/engine.js');
const assets = path.join(__dirname, '..', 'assets');
const read = name => fs.readFileSync(path.join(assets, name), 'utf8').replace(/^\uFEFF/, '');
const clone = value => JSON.parse(JSON.stringify(value));
const areaIds = ['emergency', 'ward', 'clinic', 'endoscopy', 'theatre'];

function loadAssets() {
  const context = vm.createContext({ window: {} });
  for (const name of ['catalog.js', 'banter.js', 'art.js', 'i18n.js']) {
    vm.runInContext(read(name), context, { filename: name });
  }
  return context.window;
}
const data = loadAssets();
const catalog = data.NSA_CATALOG;

function shape(value, label) {
  if (Array.isArray(value)) return value.map((item, index) => shape(item, label + '[' + index + ']'));
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, shape(value[key], label + '.' + key)]));
  }
  assert.equal(typeof value, 'string', label + ' must be a localized string');
  assert.ok(value.trim(), label + ' must not be blank');
  return 'string';
}

function attributes(tag) {
  const result = {};
  for (const match of tag.matchAll(/([\w-]+)="([^"]*)"/g)) result[match[1]] = match[2];
  return result;
}
function groupsWith(markup, key) {
  return [...markup.matchAll(/<g\b[^>]*>/g)].map(match => attributes(match[0])).filter(group => key in group);
}
const normalizeClipIds = svg => svg.replace(/pc\d+/g, 'patient-clip');
const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));

// Run the actual app helpers with rendering and storage replaced by observable
// boundaries. This exercises gameplay without copying its implementation.
function appHarness(session = null, testCatalog = catalog) {
  const source = read('app.js');
  const start = source.indexOf('  function avatarChoices()');
  const end = source.indexOf("  document.addEventListener('click'", start);
  assert.ok(start >= 0 && end > start, 'The real game-helper section must be present');
  const stats = { persisted: 0, rendered: 0, dialogs: [], navigated: [], scrolled: 0 };
  const state = { lang: 'en', avatar: 0, sound: false, history: [], bookmarks: [], session };
  const dom = {
    querySelector() { return { close() {}, scrollIntoView() { stats.scrolled++; } }; }
  };
  const context = vm.createContext({
    window: data, C: testCatalog, E, A: data.NSAArt, state,
    document: dom, esc: escape,
    comedy: () => data.NSABanter[state.lang],
    getCase: id => testCatalog.cases.find(c => c.id === id),
    getArea: id => testCatalog.areas.find(a => a.id === id),
    t: key => data.NSABanter[state.lang][key] || data.NSA_TEXT[state.lang][key] || key,
    loc: value => value[state.lang],
    clock: minutes => String((22 + Math.floor(minutes / 60)) % 24).padStart(2, '0') + ':' + String(minutes % 60).padStart(2, '0'),
    persist() { stats.persisted++; },
    render() { stats.rendered++; },
    navigate(view) { stats.navigated.push(view); },
    openDialog(html) { stats.dialogs.push(html); return { classList: { add() {} } }; }
  });
  const constants = ['ATTENDING_CALLS', 'count', 'consultantOf'].map(name => source.match(new RegExp('const ' + name + '=[^\\n]*;'))[0]).join('\n');
  vm.runInContext(constants + "\nlet areaFilter = 'all', query = '', savedOnly = false;\n" + source.slice(start, end) + `
    globalThis.helpers = {
      gameStage, handleScene, coffeeBreak, askNurse, callAttending, attendingWarning, characterComment, startBoss, answerBoss, nextBoss,
      validBoss, bossCorrect, speakerFor, lineWithoutName,
      filterState: () => ({ areaFilter, query, savedOnly })
    };
  `, context, { filename: 'app-game-helpers.js' });
  return { state, stats, api: context.helpers };
}

function completedSession(seed = 'cartoon-regression') {
  const session = E.create(catalog, E.schedule(catalog, seed), 'learn', seed);
  for (const patient of session.patients) {
    const c = catalog.cases.find(c => c.id === patient.id);
    for (const step of c.steps) {
      E.answer(session, catalog, c.id, step.best);
      E.next(session, catalog, c.id);
    }
  }
  assert.ok(session.finished);
  return session;
}

test('all story keys and nested dialogue structures are present in English, German and Spanish', () => {
  assert.deepEqual(Object.keys(data.NSABanter).sort(), ['de', 'en', 'es']);
  const english = shape(data.NSABanter.en, 'en');
  for (const lang of ['de', 'es']) assert.deepEqual(shape(data.NSABanter[lang], lang), english);
  for (const [lang, text] of Object.entries(data.NSABanter)) {
    assert.deepEqual(Object.keys(text.areaIntro).sort(), [...areaIds].sort());
    assert.deepEqual([...new Set(text.opening.map(line => line.speaker))].sort(), ['attending', 'chief', 'nurse']);
    assert.equal(text.opening.length, 5);
    assert.equal(text.good.length, 12);
    assert.equal(text.partial.length, 5);
    assert.equal(text.unsafe.length, 5);
    assert.equal(text.coffee.length, 8);
    assert.equal(text.miss.length, 8);
    assert.equal(text.strike.length, 6);
    assert.equal(text.gameRank.length, 4);
    assert.equal(text.careerRanks.length, 9);
    assert.equal(text.careerJokes.length, 9);
    assert.equal(text.rankUp.length, 4);
    assert.deepEqual(Object.keys(text.badges), ['firstCase', 'firstShift', 'streak5', 'streak10', 'perfectShift', 'bossPerfect',
      'coffee5', 'allAreas', 'comeback', 'joker10', 'specialist', 'cases50', 'nightOwl', 'anatomist']);
    assert.equal(text.splash.length, 5, lang + ' splash lines');
    assert.deepEqual(Object.keys(text.atlasResult).sort(), ['good', 'perfect', 'poor']);
    for (const line of text.streak) assert.match(line, /\{n\}/, lang + ' streak lines must name the streak length');
    assert.match(text.jokerNote, /5/, lang + ' must describe the actual five-minute joker cost');
    assert.match(text.coffeeNote, /5/, lang + ' must describe the actual five-minute game break');
    assert.doesNotMatch(text.challengeRetry, /try again|erneut versuchen|vuelva a intentarlo/i,
      lang + ' feedback must not promise a retry when the game advances');
    assert.doesNotMatch(text.hero.replace(/<br\s*\/?\s*>/gi, ''), /[<>]/,
      lang + ' hero may contain line breaks, but no other HTML');
  }
});

test('every interface label exists in English, German and Spanish', () => {
  const english = Object.keys(data.NSA_TEXT.en).sort();
  for (const lang of ['de', 'es']) assert.deepEqual(Object.keys(data.NSA_TEXT[lang]).sort(), english, lang + ' interface labels');
  for (const lang of ['en', 'de', 'es']) {
    for (const key of ['allOptions', 'whyCorrect', 'revenge', 'stickers', 'careerTitle', 'blitz', 'keysHint']) {
      assert.ok(String(data.NSA_TEXT[lang][key] || '').trim(), lang + '.' + key);
    }
  }
});

test('the original cast survives in every language and speaker matching finds their comments', () => {
  const expected = {
    en: { nurse: 'Grace', attending: 'Dr. Brennan', chief: 'Prof. Whitfield' },
    de: { nurse: 'Jana', attending: 'Dr. Brenner', chief: 'Prof. Leuchtenberg' },
    es: { nurse: 'Lucía', attending: 'Dr. Herrera', chief: 'Prof. Valdés' }
  };
  const h = appHarness();
  for (const lang of Object.keys(expected)) {
    h.state.lang = lang;
    for (const [role, name] of Object.entries(expected[lang])) {
      assert.equal(data.NSABanter[lang].staff[role].name, name);
      assert.equal(h.api.speakerFor(name + ': Test'), role);
      assert.equal(h.api.lineWithoutName(name + ': Test', role), 'Test');
    }
  }
});

test('the hero is a named localized SVG image and every case receives a stable original portrait', () => {
  const art = data.NSAArt;
  const heroes = ['en', 'de', 'es'].map(lang => art.hero(lang));
  assert.equal(new Set(heroes).size, 3, 'Each hero must contain its own localized text');
  for (const hero of heroes) {
    const svg = attributes(hero.match(/<svg\b[^>]*>/)[0]);
    assert.equal(svg.role, 'img');
    assert.ok(svg['aria-label']);
    assert.match(hero, /<title>[^<]+<\/title>/);
    assert.doesNotMatch(hero, /undefined|NaN/);
  }
  assert.equal(catalog.cases.filter(c => c.source).length, 267, 'Every imported question is in the catalog');
  assert.ok(catalog.cases.length >= 297, 'The 30 story cases and any newer authored cases are in the catalog');
  const ids = [];
  const designs = [];
  for (const c of catalog.cases) {
    const svg = art.patientPortrait(c.id, 'neutral', 76);
    assert.match(svg, /<svg\b/);
    assert.match(svg, /aria-hidden="true"/);
    assert.match(svg, /width="76" height="76"/);
    assert.doesNotMatch(svg, /undefined|NaN/);
    ids.push(svg.match(/<clipPath id="([^"]+)"/)[1]);
    designs.push(normalizeClipIds(svg));
    assert.equal(normalizeClipIds(art.patientPortrait(c.id, 'neutral', 76)), normalizeClipIds(svg),
      'A case ID must keep its appearance across renders: ' + c.id);
    assert.notEqual(normalizeClipIds(art.patientPortrait(c.id, 'unsafe', 76)), normalizeClipIds(svg),
      'Feedback must change the expression without requiring an image download: ' + c.id);
  }
  assert.equal(new Set(ids).size, catalog.cases.length, 'Repeated portraits need unique SVG clip IDs');
  assert.ok(new Set(designs).size >= 20, 'The patient cast should not collapse into one repeated portrait');
});

test('all room scenes expose five localized, keyboard-accessible department doors', () => {
  const names = {
    en: ['Emergency', 'Ward', 'Clinic', 'Endoscopy', 'Theatre'],
    de: ['Notaufnahme', 'Station', 'Ambulanz', 'Endoskopie', 'OP-Saal'],
    es: ['Urgencias', 'Planta', 'Consulta', 'Endoscopia', 'Quirófano']
  };
  for (const lang of Object.keys(names)) {
    for (const area of areaIds) {
      const scene = data.NSAArt.scene(area, [], null, '23:15', 0, lang);
      const doors = groupsWith(scene, 'data-scene-area');
      assert.equal(doors.length, 5);
      assert.deepEqual(doors.map(door => door['data-scene-area']), areaIds);
      assert.equal(doors.filter(door => door['aria-pressed'] === 'true').length, 1);
      doors.forEach((door, index) => {
        assert.equal(door.role, 'button');
        assert.equal(door.tabindex, '0');
        assert.equal(door['aria-label'], names[lang][index]);
        assert.equal(door['aria-pressed'], String(areaIds[index] === area));
      });
      const coffee = groupsWith(scene, 'data-scene-coffee');
      assert.equal(coffee.length, 1);
      assert.equal(coffee[0].role, 'button');
      assert.equal(coffee[0].tabindex, '0');
      assert.ok(coffee[0]['aria-label']);
    }
  }
});

test('patient names, IDs, age labels and clock text are escaped before entering scene markup', () => {
  const patient = {
    id: 'ed-" onfocus="injected"><svg>&\'',
    name: 'Eve <script>alert("x")</script> & \'quoted\'',
    age: '"><script>age</script>', area: 'emergency', acuity: 'routine', available: true
  };
  const time = '<script>clock</script>';
  const scene = data.NSAArt.scene('emergency', [patient], patient.id, time, 0, 'en');
  assert.ok(scene.includes('data-scene-patient="' + escape(patient.id) + '"'));
  assert.ok(scene.includes(escape(patient.name)));
  assert.ok(scene.includes(escape(patient.age)));
  assert.ok(scene.includes(escape(time)));
  assert.doesNotMatch(scene, /<script>|<svg>&'|onfocus="injected"/);
  assert.equal(groupsWith(scene, 'data-scene-patient').length, 1);
});

test('scenes filter patients by area and keep future patients out of keyboard interaction', () => {
  const patients = [
    { id: 'ed-one', name: 'Available', area: 'emergency', age: 40, acuity: 'routine', available: true },
    { id: 'ed-two', name: 'Future', area: 'emergency', age: 42, acuity: 'urgent', available: false },
    { id: 'clinic-three', name: 'Other area', area: 'clinic', age: 50, acuity: 'routine', available: true }
  ];
  const scene = data.NSAArt.scene('emergency', patients, 'ed-one');
  const shown = groupsWith(scene, 'data-scene-patient');
  assert.deepEqual(shown.map(p => p['data-scene-patient']), ['ed-one', 'ed-two']);
  assert.equal(shown[0].tabindex, '0');
  assert.equal(shown[0]['aria-disabled'], 'false');
  assert.equal(shown[1].tabindex, '-1');
  assert.equal(shown[1]['aria-disabled'], 'true');
  assert.match(shown[1].class, /\bfuture\b/);
  assert.ok(!scene.includes('Other area'));
  const allPatients = catalog.cases.map(c => ({ id: c.id, name: c.patient.name, age: c.patient.age, area: c.area, acuity: c.acuity, available: true }));
  for (const area of areaIds) {
    const expected = catalog.cases.filter(c => c.area === area).map(c => c.id);
    const selected = expected.at(-1);
    const generated = groupsWith(data.NSAArt.scene(area, allPatients, selected), 'data-scene-patient');
    const shownIds = generated.map(p => p['data-scene-patient']);
    assert.equal(generated.length, Math.min(6, expected.length));
    assert.equal(new Set(shownIds).size, shownIds.length);
    assert.ok(shownIds.every(id => expected.includes(id)), 'A room cannot display another area\'s case');
    assert.ok(shownIds.includes(selected), 'Selecting a case beyond the first six must keep it visible');
    assert.equal(generated.filter(p => p['aria-pressed'] === 'true').length, 1);
  }
});

test('scene actions cannot select a future arrival and department doors select only arrived patients', () => {
  const ids = [catalog.cases.find(c => c.area === 'emergency').id,
    catalog.cases.find(c => c.area === 'clinic').id,
    catalog.cases.find(c => c.area === 'ward').id];
  const s = E.create(catalog, ids, 'shift', 'scene-actions');
  const h = appHarness(s);
  h.api.handleScene({ dataset: { scenePatient: ids[1] } });
  assert.equal(s.selected, ids[0]);
  assert.equal(h.stats.persisted, 0);
  h.api.handleScene({ dataset: { sceneArea: 'clinic' } });
  assert.equal(s.selected, ids[0]);
  assert.equal(h.stats.dialogs.length, 1, 'A room with no arrived case should explain why it is empty');
  s.clock = 10;
  h.api.handleScene({ dataset: { sceneArea: 'clinic' } });
  assert.equal(s.selected, ids[1]);
  assert.equal(h.stats.persisted, 1);
  const idle = appHarness();
  idle.api.handleScene({ dataset: { sceneArea: 'theatre' } });
  assert.equal(idle.api.filterState().areaFilter, 'theatre');
  assert.deepEqual(idle.stats.navigated, ['library']);
});

test('morning report is locked until the clinical session is finished', () => {
  const session = E.create(catalog, [catalog.cases[0].id], 'learn', 'unfinished');
  const h = appHarness(session);
  h.api.startBoss();
  assert.equal(session.boss, undefined);
  assert.equal(h.stats.persisted, 0);
  assert.ok(h.stats.dialogs[0].includes(escape(data.NSABanter.en.bossLocked)));
});

test('morning report selects five distinct reproducible questions, one from each completed area', () => {
  for (const seed of ['morning-A', 'morning-B', 'morning-C']) {
    const h = appHarness(completedSession(seed));
    const untouched = clone(h.state.session.patients);
    h.api.startBoss();
    const boss = h.state.session.boss;
    assert.equal(boss.items.length, 5);
    assert.ok(h.api.validBoss(boss));
    assert.equal(new Set(boss.items.map(item => item.caseId + ':' + item.stepIndex)).size, 5);
    assert.deepEqual(clone(boss.items.map(item => catalog.cases.find(c => c.id === item.caseId).area)).sort(), [...areaIds].sort());
    for (const item of boss.items) {
      const step = catalog.cases.find(c => c.id === item.caseId).steps[item.stepIndex];
      assert.deepEqual(clone(item.order).sort(), clone(step.options.map(option => option.id)).sort());
    }
    const second = appHarness(completedSession(seed));
    second.api.startBoss();
    assert.deepEqual(clone(second.state.session.boss.items), clone(boss.items));
    assert.deepEqual(clone(h.state.session.patients), untouched);
    const before = clone(boss);
    h.api.startBoss();
    assert.deepEqual(clone(h.state.session.boss), before, 'Reopening the quiz must not replace its questions or progress');
  }
});

test('morning reports preserve real four-choice and five-choice source questions alongside original clinical steps', () => {
  for (const optionCount of [4, 5]) {
  const imported = catalog.cases.find(c => c.source && c.steps.length === 1 && c.steps[0].options.length === optionCount);
  assert.ok(imported, 'The built catalog must contain a ' + optionCount + '-choice source question');
  const legacy = catalog.cases.find(c => !c.source && c.area === imported.area && c.steps.length === 3);
  assert.ok(legacy, 'The original case in this area must remain available');
  const session = E.create(catalog, [legacy.id, imported.id], 'learn', 'mixed-chief-options-' + optionCount);
  for (const c of [legacy, imported]) {
    for (const step of c.steps) { E.answer(session, catalog, c.id, step.best); E.next(session, catalog, c.id); }
  }
  const h = appHarness(session), clinical = clone(session.patients), initialClock = session.clock;
  h.api.startBoss();
  const boss = session.boss;
  assert.ok(h.api.validBoss(boss));
  assert.equal(boss.items.length, legacy.steps.length + imported.steps.length);
  assert.ok(boss.items.some(item => item.order.length === 3));
  assert.ok(boss.items.some(item => item.order.length === optionCount));
  let checkedSource = false;
  for (const item of boss.items) {
    const c = catalog.cases.find(c => c.id === item.caseId), step = c.steps[item.stepIndex];
    const choice = item.caseId === imported.id ? step.options.at(-1) : step.options.find(option => option.id === step.best);
    h.api.answerBoss(choice.id);
    if (item.caseId === imported.id) {
      checkedSource = true;
      assert.equal(boss.answers[boss.index], step.options.at(-1).id, 'The last source choice remains selectable in the chief quiz');
      if (optionCount === 5) assert.equal(boss.answers[boss.index], 'e');
      assert.equal((h.stats.dialogs.at(-1).match(/data-boss-option="/g) || []).length, optionCount);
      assert.ok(h.stats.dialogs.at(-1).includes(escape(choice.feedback.en)));
      const missingLast = clone(boss);
      missingLast.items[boss.index].order.pop();
      assert.equal(h.api.validBoss(missingLast), false, 'A restored chief question cannot silently lose its last choice');
    }
    h.api.nextBoss();
    assert.ok(h.api.validBoss(boss));
  }
  assert.ok(checkedSource && boss.done);
  assert.equal(session.clock, initialClock);
  assert.deepEqual(clone(session.patients), clinical);
  }
});

test('chief questions validate and render the supported two-choice and six-choice boundaries', () => {
  const makeCase = (id, area, count) => {
    const c = clone(catalog.cases[0]);
    c.id = id; c.area = area;
    const step = clone(c.steps[0]);
    step.id = 'fixture-decision';
    step.options = Array.from({ length: count }, (_, i) => {
      const option = clone(c.steps[0].options[i % c.steps[0].options.length]);
      option.id = String.fromCharCode(97 + i); option.score = i === count - 1 ? 10 : 0; option.critical = false;
      return option;
    });
    step.best = step.options.at(-1).id; c.steps = [step];
    return c;
  };
  const testCatalog = { ...catalog, cases: [makeCase('fixture-boss-two', 'clinic', 2), makeCase('fixture-boss-six', 'theatre', 6)] };
  const session = E.create(testCatalog, testCatalog.cases.map(c => c.id), 'learn', 'boss-boundaries');
  for (const c of testCatalog.cases) { E.answer(session, testCatalog, c.id, c.steps[0].best); E.next(session, testCatalog, c.id); }
  const h = appHarness(session, testCatalog);
  h.api.startBoss();
  const boss = session.boss;
  assert.deepEqual(clone(boss.items.map(item => item.order.length)).sort((a, b) => a - b), [2, 6]);
  for (const item of boss.items) {
    const c = testCatalog.cases.find(c => c.id === item.caseId), step = c.steps[0];
    assert.ok(h.api.validBoss(boss));
    assert.equal((h.stats.dialogs.at(-1).match(/data-boss-option="/g) || []).length, step.options.length);
    h.api.answerBoss(step.best); h.api.nextBoss();
  }
  assert.ok(boss.done);
  assert.equal(h.api.bossCorrect(boss), 2);
});

test('morning-report answers count once, need feedback acknowledgement, and never alter clinical points or time', () => {
  const h = appHarness(completedSession('morning-answer-regression'));
  const clinical = clone(h.state.session.patients);
  const initialClock = h.state.session.clock;
  h.api.startBoss();
  const boss = h.state.session.boss;
  let correct = 0;
  h.api.nextBoss();
  assert.equal(boss.index, 0, 'An unanswered round cannot be skipped');
  h.api.answerBoss('unknown');
  assert.equal(boss.answers.length, 0);
  for (let i = 0; i < boss.items.length; i++) {
    const item = boss.items[i], step = catalog.cases.find(c => c.id === item.caseId).steps[item.stepIndex];
    const answer = i === 1 ? step.options.find(option => option.id !== step.best).id : step.best;
    h.api.answerBoss(answer);
    correct += Number(answer === step.best);
    const answered = clone(boss), saved = h.stats.persisted;
    h.api.answerBoss(step.best);
    assert.deepEqual(clone(boss), answered, 'A repeated answer click cannot retry, replace or add an answer');
    assert.equal(h.stats.persisted, saved);
    assert.match(h.stats.dialogs.at(-1), /data-action="boss-next"/);
    assert.match(h.stats.dialogs.at(-1), /data-boss-option="[^"]+" disabled/);
    h.api.nextBoss();
    assert.ok(h.api.validBoss(boss));
    if (i < boss.items.length - 1) {
      const index = boss.index;
      h.api.nextBoss();
      assert.equal(boss.index, index, 'Double-clicking next cannot skip the following unanswered round');
    }
  }
  assert.ok(boss.done);
  assert.equal(h.api.bossCorrect(boss), correct);
  assert.equal(correct, 4);
  const done = clone(boss);
  h.api.answerBoss('a'); h.api.nextBoss();
  assert.deepEqual(clone(boss), done);
  assert.equal(h.state.session.clock, initialClock);
  assert.deepEqual(clone(h.state.session.patients), clinical);
  assert.deepEqual(h.state.history, [], 'Quiz answers must not create clinical logbook records');
});

test('a coffee break adds exactly five game minutes without changing clinical scores, answers or error counts', () => {
  const session = E.create(catalog, E.schedule(catalog, 'coffee-regression'), 'shift', 'coffee-regression');
  const first = catalog.cases.find(c => c.id === session.selected);
  E.answer(session, catalog, first.id, first.steps[0].best);
  const h = appHarness(session);
  const patients = clone(session.patients), initialClock = session.clock;
  h.api.coffeeBreak();
  assert.equal(session.clock, initialClock + 5);
  assert.equal(session.coffees, 1);
  assert.deepEqual(clone(session.patients), patients);
  assert.ok(E.validSession(session, catalog));
  h.api.coffeeBreak();
  assert.equal(session.clock, initialClock + 10);
  assert.equal(session.coffees, 2);
  assert.deepEqual(clone(session.patients), patients);
  assert.equal(h.stats.persisted, 2);
  assert.equal(h.stats.rendered, 2);
  assert.equal(h.stats.dialogs.length, 2);
  assert.deepEqual(h.state.history, []);
});

test('coffee outside an unfinished shift cannot add time or claim it added five minutes', () => {
  for (const session of [null, completedSession('coffee-finished')]) {
    const h = appHarness(session), before = clone(h.state);
    h.api.coffeeBreak();
    assert.deepEqual(clone(h.state), before);
    assert.equal(h.stats.persisted, 0);
    assert.equal(h.stats.rendered, 0);
    assert.equal(h.stats.dialogs.length, 1);
    assert.ok(!h.stats.dialogs[0].includes(escape(data.NSABanter.en.coffeeNote)),
      'A joke-only break must not display the active-shift time-cost message');
  }
});

test('restored morning-report progress rejects premature completion, answer gaps and duplicated questions', async t => {
  const h = appHarness(completedSession('boss-restore'));
  h.api.startBoss();
  const base = clone(h.state.session.boss);
  const best = item => catalog.cases.find(c => c.id === item.caseId).steps[item.stepIndex].best;
  const mutations = {
    'done after only the first answer': boss => { boss.answers = [best(boss.items[0])]; boss.done = true; },
    'a gap in already completed answers': boss => { boss.index = 2; boss.answers = [best(boss.items[0]), null]; },
    'duplicated question': boss => { boss.items[1] = clone(boss.items[0]); },
    'string rather than numeric step index': boss => { boss.items[0].stepIndex = String(boss.items[0].stepIndex); },
    'invalid option in an earlier answer': boss => { boss.index = 1; boss.answers = ['unknown']; }
  };
  for (const [name, mutate] of Object.entries(mutations)) {
    await t.test(name, () => {
      const boss = clone(base); mutate(boss);
      assert.equal(h.api.validBoss(boss), false, name);
    });
  }
});

test("the nurse's joker crosses out one wrong answer, costs five game minutes and never touches points", () => {
  for (const c of [catalog.cases.find(c => c.source && c.steps[0].options.length === 5), catalog.cases.find(c => !c.source)]) {
    const session = E.create(catalog, [c.id], 'learn', 'joker-' + c.id);
    session.struck = {};
    const h = appHarness(session);
    const patients = clone(session.patients), clock = session.clock;
    h.api.askNurse();
    const key = c.id + ':0', struck = session.struck[key], step = c.steps[0];
    assert.ok(step.options.some(o => o.id === struck), 'The joker must strike a real option');
    assert.notEqual(struck, step.best, 'The joker can never strike the correct answer');
    assert.equal(step.options.find(o => o.id === struck).score, Math.min(...step.options.filter(o => o.id !== step.best).map(o => o.score)));
    assert.equal(session.clock, clock + 5);
    assert.equal(session.jokers, 1);
    assert.deepEqual(clone(session.patients), patients, 'Clinical answers and points stay unchanged');
    assert.ok(E.validSession(session, catalog));
    h.api.askNurse();
    assert.equal(session.struck[key], struck, 'A second request cannot strike another answer');
    assert.equal(session.clock, clock + 5);
    assert.ok(h.stats.dialogs[1].includes(escape(data.NSABanter.en.strikeUsed.replace(/^Grace: /, ''))));
    E.answer(session, catalog, c.id, step.best);
    const answered = session.clock;
    h.api.askNurse();
    assert.equal(session.clock, answered, 'After answering, the nurse only gives advice');
    const repeat = E.create(catalog, [c.id], 'learn', 'joker-' + c.id);
    repeat.struck = {};
    appHarness(repeat).api.askNurse();
    assert.equal(repeat.struck[key], struck, 'The struck answer is reproducible for the same session seed');
  }
});

test('calling the attending costs five minutes, gives the decision rule but never the answer, and works three times a shift', () => {
  const ids = catalog.cases.filter(c => !c.source && c.steps.length > 1).slice(0, 4).map(c => c.id);
  const testCatalog = clone(catalog);
  const first = testCatalog.cases.find(c => c.id === ids[0]);
  first.steps[0].hint = { en: 'Think about what decides the next step.', de: 'Denk daran, was den nächsten Schritt entscheidet.', es: 'Piensa en lo que decide el siguiente paso.' };
  const session = E.create(testCatalog, ids, 'shift', 'attending-calls');
  Object.assign(session, { duty: 'night', selected: ids[0] });
  const h = appHarness(session, testCatalog);
  const patients = clone(session.patients), clock = session.clock;
  h.api.callAttending();
  assert.equal(session.clock, clock + 5, 'A call costs five game minutes');
  assert.deepEqual(clone([session.calls, session.called]), [1, { [ids[0] + ':0']: true }]);
  assert.deepEqual(clone(session.patients), patients, 'A call never touches answers or points');
  assert.ok(E.validSession(session, testCatalog));
  const said = h.stats.dialogs.at(-1);
  assert.ok(said.includes(escape(first.steps[0].hint.en)), 'The attending gives the hint of this decision');
  assert.ok(!said.includes(escape(first.steps[0].options.find(o => o.id === first.steps[0].best).text.en)), 'but never the answer');
  assert.ok(said.includes(escape(data.NSA_TEXT.en.attendingNote.replace('{n}', 2))), 'and says how many calls are left');
  h.api.callAttending();
  assert.equal(session.clock, clock + 5, 'Asking again about the same decision is free');
  assert.equal(session.calls, 1);
  for (const id of ids.slice(1, 3)) { session.selected = id; h.api.callAttending(); }
  assert.equal(session.calls, 3);
  const withoutHint = testCatalog.cases.find(c => c.id === ids[1]);
  assert.ok(h.stats.dialogs.at(-2).includes(escape(withoutHint.objectives.en[0])), 'Without a written hint the case objective is the nudge');
  const beforeBusy = session.clock;
  session.selected = ids[3];
  h.api.callAttending();
  assert.equal(session.clock, beforeBusy, 'A fourth call is not answered and costs nothing');
  assert.equal(session.calls, 3);
  assert.ok(data.NSABanter.en.attendingBusy.some(line => h.stats.dialogs.at(-1).includes(escape(line.replace(/^Grace: /, '')))), 'The nurse explains that the attending is busy');
  session.selected = ids[0];
  E.answer(session, testCatalog, ids[0], first.steps[0].best);
  const answered = session.clock;
  h.api.callAttending();
  assert.equal(session.clock, answered, 'After the answer the attending debriefs for free');
  assert.ok(h.stats.dialogs.at(-1).includes(escape(first.steps[0].hint.en)));
  for (const lang of ['en', 'de', 'es']) {
    const text = data.NSABanter[lang];
    for (const kind of ['attendingNight', 'attendingDay', 'attendingAfter', 'attendingIdle', 'attendingWarn']) {
      assert.ok(text[kind].length >= 2 && text[kind].every(line => line.startsWith(text.staff.attending.name + ':')), lang + ' ' + kind + ' lines are the attending\'s');
    }
    assert.ok(text.attendingBusy.every(line => line.startsWith(text.staff.nurse.name + ':')), lang + ' the nurse answers when no calls are left');
  }
});

test('after a dangerous answer the attending steps in with the decisive rule', () => {
  const c = clone(catalog.cases.find(c => !c.source && c.steps.some(s => s.options.some(o => o.critical))));
  const h = appHarness(null);
  const step = c.steps[0];
  const fallback = h.api.attendingWarning(c, step, c.id + ':0');
  assert.match(fallback, /attending-warning/);
  assert.ok(fallback.includes(escape(c.takeaway.en)), 'Without a written hint the warning gives the take-home message');
  assert.ok(fallback.includes(escape(data.NSA_TEXT.en.attendingImportant)));
  step.hint = { en: 'Unstable <first>: secure the circulation.', de: 'x', es: 'x' };
  const warned = h.api.attendingWarning(c, step, c.id + ':0');
  assert.ok(warned.includes('Unstable &lt;first&gt;: secure the circulation.'), 'The hint is escaped and shown');
  assert.ok(data.NSABanter.en.attendingWarn.some(line => warned.includes(escape(line.replace(/^Dr\. Brennan: /, '')))));
});

test('radiotherapy questions are answered by the radiation oncologist, on the phone and after a dangerous answer', () => {
  const testCatalog = clone(catalog);
  const c = testCatalog.cases.find(c => !c.source && c.steps.some(s => s.options.some(o => o.critical)));
  c.consultant = 'radiotherapist';
  c.steps[0].hint = { en: 'Total dose, dose per fraction and target belong together.', de: 'x', es: 'x' };
  const session = E.create(testCatalog, [c.id], 'shift', 'radio-call');
  Object.assign(session, { duty: 'radiotherapy', selected: c.id });
  const h = appHarness(session, testCatalog);
  h.api.callAttending();
  const said = h.stats.dialogs.at(-1), staff = data.NSABanter.en.staff;
  assert.ok(said.includes(escape(staff.radiotherapist.name)) && !said.includes(escape(staff.attending.name)), 'The radiation oncologist takes the call');
  assert.ok(said.includes(escape(c.steps[0].hint.en)));
  assert.ok(data.NSABanter.en.radioCall.some(line => said.includes(escape(line.replace(/^Dr\. Okoro: /, '')))));
  assert.equal(session.calls, 1, 'Her calls count against the same three calls of the shift');
  const warned = h.api.attendingWarning(c, c.steps[0], c.id + ':0');
  assert.ok(warned.includes(escape(staff.radiotherapist.name)) && data.NSABanter.en.radioWarn.some(line => warned.includes(escape(line.replace(/^Dr\. Okoro: /, '')))));
  delete c.consultant;
  assert.ok(h.api.attendingWarning(c, c.steps[0], c.id + ':0').includes(escape(staff.attending.name)), 'Other cases keep the attending');
  for (const lang of ['en', 'de', 'es']) {
    const text = data.NSABanter[lang];
    for (const kind of ['radioCall', 'radioAfter', 'radioWarn', 'radioIdle']) assert.ok(text[kind].length >= 2 && text[kind].every(line => line.startsWith(text.staff.radiotherapist.name + ':')), lang + ' ' + kind);
    assert.ok(text.radioBusy.every(line => line.startsWith(text.staff.nurse.name + ':')));
    assert.ok(text.askRadiotherapist && text.staff.radiotherapist.role);
  }
  assert.match(data.NSAArt.portrait('radiotherapist', 'smile', 96), /<svg/);
  assert.notEqual(data.NSAArt.portrait('radiotherapist', 'smile', 96), data.NSAArt.portrait('attending', 'smile', 96), 'She has her own portrait');
});

function protocolHarness(protocols, lang = 'en') {
  const source = read('app.js');
  const start = source.indexOf('  function protocols()'), end = source.indexOf('  function atlas()', start);
  assert.ok(start >= 0 && end > start, 'The protocol page must be present');
  const context = vm.createContext({ C: { ...catalog, protocols }, esc: escape, getCase: id => catalog.cases.find(c => c.id === id),
    t: key => data.NSA_TEXT[lang][key] || key, loc: value => value[lang], protocolEntity: null, protocolKind: 'systemic', state: { lang } });
  vm.runInContext(source.slice(start, end) + '\nglobalThis.page = { protocols, protocolCard, rtCard };', context, { filename: 'app-protocols.js' });
  return context;
}

test('the protocol page shows cycles, doses, routes and sources per tumour and links its questions', () => {
  const text = value => ({ en: value, de: value, es: value });
  const regimen = { id: 'fixture-regimen', name: text('Gem<Cis>'), setting: text('Metastatic'), cycleDays: 21, cycles: text('4–6'), support: text('Hydration'), cautions: text('GFR'), evidence: text('Standard'),
    drugs: [{ name: text('Gemcitabine'), dose: text('1000 mg/m²'), route: 'i.v.', schedule: text('Days 1 and 8') }, { name: text('Mitomycin C'), dose: text('40 mg'), route: 'intravesical', schedule: text('Weekly') }],
    sources: [{ label: 'Guideline', url: 'https://example.org/g' }], questions: [catalog.cases[0].id, 'missing-case'] };
  const continuous = { ...regimen, id: 'fixture-continuous', cycleDays: null, questions: [] };
  const h = protocolHarness([{ id: 'one', title: text('Bladder'), regimens: [regimen, continuous] }, { id: 'two', title: text('Kidney'), regimens: [continuous] }]);
  const page = h.page.protocols();
  assert.ok(page.includes('protocol-warning'), 'The page always carries the learning-overview warning');
  assert.equal((page.match(/data-protocol-entity=/g) || []).length, 2, 'One tab per tumour');
  assert.equal((page.match(/class="protocol-card"/g) || []).length, 2, 'Only the regimens of the selected tumour');
  assert.ok(page.includes('Gem&lt;Cis&gt;') && !page.includes('Gem<Cis>'), 'Protocol text is escaped');
  assert.ok(page.includes('1000 mg/m²') && page.includes(escape(data.NSA_TEXT.en.routeIntravesical)), 'Doses and routes are shown');
  assert.ok(page.includes(escape(data.NSA_TEXT.en.protocolCycleDays.replace('{n}', 21))) && page.includes(escape(data.NSA_TEXT.en.protocolContinuous)));
  assert.ok(page.includes('href="https://example.org/g"') && page.includes('rel="noopener noreferrer"'));
  assert.equal((page.match(/data-protocol-practice=/g) || []).length, 1, 'Only regimens with questions get a practice button');
  assert.ok(page.includes(escape(data.NSA_TEXT.en.protocolPractice.replace('{n}', 1))), 'Unknown question ids are not counted');
  h.protocolEntity = 'two';
  assert.equal((h.page.protocols().match(/class="protocol-card"/g) || []).length, 1, 'Switching the tab shows the other tumour');
  assert.ok(protocolHarness([]).page.protocols().includes('protocol-warning'), 'Without protocols the page still renders');
});

test('the radiotherapy schemes show total dose, dose per fraction and fractions with the decimal comma of the language', () => {
  const text = value => ({ en: value, de: value, es: value });
  const scheme = { id: 'rt-fixture', name: text('Ultrahypo'), setting: text('Localised'), technique: text('SBRT'), combined: text('None'), support: text('Spacer'), cautions: text('Rectum'), evidence: text('Trial'),
    phases: [{ target: text('Prostate'), totalGy: 36.25, fractionGy: 7.25, fractions: 5, schedule: text('Every other day') }, { target: text('Seeds <I-125>'), totalGy: 145, fractionGy: null, fractions: null, schedule: text('Once') }],
    sources: [{ label: 'Guideline', url: 'https://example.org/rt' }], questions: [] };
  const h = protocolHarness([{ id: 'one', title: text('Bladder'), regimens: [] }], 'de');
  h.C.radiotherapy = [{ id: 'rt-one', title: text('Prostata'), regimens: [scheme] }];
  h.protocolKind = 'radiotherapy';
  const page = h.page.protocols();
  assert.ok(page.includes('data-protocol-kind="radiotherapy"') && page.includes('aria-pressed="true"'), 'The switch shows the radiotherapy view as selected');
  assert.ok(page.includes(escape(data.NSA_TEXT.de.rtWarning)), 'The radiotherapy page has its own warning');
  assert.ok(page.includes('36,25 Gy') && page.includes('7,25 Gy') && page.includes('>5<'), 'German shows the decimal comma');
  assert.ok(page.includes('145 Gy') && page.includes(escape(data.NSA_TEXT.de.rtPermanent)), 'A permanent implant has a total dose only');
  assert.ok(page.includes('Seeds &lt;I-125&gt;'), 'Scheme text is escaped');
  const en = protocolHarness([], 'en'); en.C.radiotherapy = h.C.radiotherapy; en.protocolKind = 'radiotherapy';
  assert.ok(en.page.protocols().includes('36.25 Gy'), 'English keeps the decimal point');
});

test('streak comments name the streak and wrong source answers get exam-style teasing', () => {
  const h = appHarness();
  for (const lang of ['en', 'de', 'es']) {
    h.state.lang = lang;
    const streak = h.api.characterComment('good', 'case-x', 0, 5, true);
    assert.match(streak, /\b5\b/);
    assert.doesNotMatch(streak, /\{n\}/);
    assert.match(streak, /class="character-comment good streak"/);
    const miss = h.api.characterComment('partial', 'case-x', 0, 0, true);
    assert.ok(data.NSABanter[lang].miss.some(line => miss.includes(escape(line.slice(line.indexOf(':') + 1).trim()))),
      lang + ' wrong source answers use the miss lines');
    const story = h.api.characterComment('partial', 'case-x', 0, 0, false);
    assert.ok(data.NSABanter[lang].partial.some(line => story.includes(escape(line.slice(line.indexOf(':') + 1).trim()))),
      lang + ' partly appropriate story answers keep their own lines');
  }
});

test('every case has its own patient name, and imported names match the sex and age the case text states', () => {
  const names = catalog.cases.map(c => c.patient.name);
  assert.equal(new Set(names).size, names.length, 'Every case needs its own patient name');
  const mapping = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'patient-names.json'), 'utf8')).patients;
  const imported = catalog.cases.filter(c => c.source);
  assert.equal(Object.keys(mapping).length, imported.length, 'Every imported question needs exactly one name entry');
  const stubble = 'M-34 12 Q-29 39 0 41';
  for (const c of catalog.cases.filter(c => !c.source)) {
    assert.ok([null, 'female', 'male'].includes(c.patient.sex), 'Story patients state their sex or null: ' + c.id);
    if (c.patient.sex === 'female') {
      assert.ok(!data.NSAArt.patientPortrait(c.id, 'neutral', 76, c.patient).includes(stubble), 'No stubble for women: ' + c.id);
    }
  }
  for (const c of imported) {
    const entry = mapping[c.source.questionId];
    assert.ok(entry, 'Missing name for ' + c.source.questionId);
    assert.equal(c.patient.name, entry.name);
    assert.doesNotMatch(c.patient.name, /^Uro-\d+$/);
    assert.equal(c.patient.sex, entry.sex);
    assert.equal(c.patient.ageBand, entry.ageBand);
    assert.equal(/ & /.test(c.patient.name), entry.kind === 'multiple', 'Only vignettes with several patients list several surnames: ' + c.id);
    const female = /\b(woman|girl|pregnant)\b/i.test(c.presenting.en), male = /\b(man|boy)\b/i.test(c.presenting.en);
    if (entry.kind === 'single' && female !== male) {
      assert.equal(c.patient.sex, female ? 'female' : 'male', 'Name sex must follow the case text: ' + c.id);
    }
    const child = c.patient.age !== null ? c.patient.age < 13 : ['newborn', 'infant', 'child'].includes(c.patient.ageBand);
    if (c.patient.sex === 'female' || child) {
      assert.ok(!data.NSAArt.patientPortrait(c.id, 'neutral', 76, c.patient).includes(stubble), 'No stubble for women or children: ' + c.id);
    }
  }
});

test('every duty has a translated briefing, scene line and whiteboard label', () => {
  for (const lang of ['en', 'de', 'es']) {
    const text = data.NSABanter[lang];
    for (const duty of E.DUTIES) {
      assert.ok(text.dutyOpening[duty].length >= 2, lang + ' ' + duty + ' briefing');
      assert.ok(text.dutyOpening[duty].every(line => ['nurse', 'attending', 'chief', 'radiotherapist'].includes(line.speaker) && line.text.trim()));
      assert.ok(text.dutyIntro[duty].trim() && text.dutyBoard[duty].trim());
      for (const key of ['duty_', 'dutyText_', 'dutyTime_']) assert.ok(String(data.NSA_TEXT[lang][key + duty] || '').trim(), lang + '.' + key + duty);
    }
  }
});

test('day duties wake the attending, and the tumour board shows every case as a folder without doors', () => {
  const pick = area => catalog.cases.find(c => c.area === area);
  const patients = ['clinic', 'theatre', 'ward'].map(area => { const c = pick(area); return { id: c.id, name: c.patient.name, age: c.patient.age, area: c.area, acuity: c.acuity, available: true }; });
  const night = data.NSAArt.scene('clinic', patients, patients[0].id, '22:10', 0, 'de', { duty: 'night' });
  assert.match(night, /cartoon-rest/, 'The attending dozes at night');
  assert.equal(groupsWith(night, 'data-scene-patient').length, 1, 'Room scenes show only their own department');
  const clinic = data.NSAArt.scene('clinic', patients, patients[0].id, '08:10', 0, 'de', { duty: 'clinic', label: 'SPRECHSTUNDE' });
  assert.doesNotMatch(clinic, /cartoon-rest/, 'The attending is awake for daytime duties');
  assert.ok(clinic.includes('SPRECHSTUNDE'));
  const board = data.NSAArt.scene('clinic', patients, patients[1].id, '15:40', 0, 'de', { duty: 'board', label: 'TUMORBOARD' });
  assert.equal(groupsWith(board, 'data-scene-area').length, 0, 'The conference room has no department doors');
  const folders = groupsWith(board, 'data-scene-patient');
  assert.deepEqual(folders.map(f => f['data-scene-patient']), patients.map(p => p.id), 'Every session case lies on the table');
  assert.equal(folders.filter(f => f['aria-pressed'] === 'true').length, 1);
  assert.ok(folders.every(f => f.role === 'button' && f.tabindex === '0'));
});


// The schema viewer, atlas and quiz live outside the game-helper section, so they get their own small harness.
function schemaHarness(testCatalog = catalog) {
  const source = read('app.js');
  const start = source.indexOf('  // Teaching schemas are inline SVG');
  const end = source.indexOf('  function sourceLinks(c)', start);
  assert.ok(start >= 0 && end > start, 'The real schema section must be present');
  const stats = { dialogs: [], sounds: [], celebrations: [], splashes: 0, persisted: 0, rewards: 0 };
  const state = { lang: 'de', avatar: 0, stats: { atlasPerfect: 0 } };
  const context = vm.createContext({
    C: testCatalog, E, A: data.NSAArt, state, esc: escape,
    document: { querySelector: () => null },
    t: key => data.NSABanter[state.lang][key] || data.NSA_TEXT[state.lang][key] || key,
    loc: value => value[state.lang],
    comedy: () => data.NSABanter[state.lang],
    nowSeed: () => 'schema-test',
    speakerFor: () => 'attending',
    lineWithoutName: line => line,
    openDialog(html) { stats.dialogs.push(html); return { classList: { add() {} } }; },
    persist() { stats.persisted++; },
    celebrate(big) { stats.celebrations.push(big); },
    checkRewards() { stats.rewards++; },
    sound(kind) { stats.sounds.push(kind); },
    splash() { stats.splashes++; }
  });
  vm.runInContext(source.slice(start, end) + `
    globalThis.helpers = { schemaFigure, caseVisuals, atlas, startQuiz, answerQuiz,
      quiz: () => quiz, next() { quiz.index++; quiz.answered = null; showQuiz(); } };
  `, context, { filename: 'app-schema-helpers.js' });
  return { state, stats, api: context.helpers };
}
function fakeFigure() {
  const figure = { classes: new Set(), marks: {}, note: { innerHTML: '' } };
  figure.classList = { add: name => figure.classes.add(name) };
  figure.querySelector = selector => {
    if (selector === '.schema-note') return figure.note;
    const part = selector.match(/data-part="([^"]+)"/);
    return part ? { classList: { add: (...names) => { figure.marks[part[1]] = (figure.marks[part[1]] || []).concat(names); } } } : null;
  };
  return figure;
}
const partIdsInSvg = svg => [...svg.matchAll(/data-part="([^"]+)"/g)].map(match => match[1]);
// The whole SVG must consist of tags made only of whitelisted elements and double-quoted, whitelisted attributes
// whose values contain no angle brackets, so no attribute or tag can hide after a stray ">".
const SVG_ELEMENTS = new Set(['g', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon']);
const SVG_ATTRIBUTES = new Set(['d', 'x', 'y', 'width', 'height', 'rx', 'ry', 'cx', 'cy', 'r', 'x1', 'y1', 'x2', 'y2', 'points', 'fill', 'stroke',
  'stroke-width', 'stroke-dasharray', 'stroke-linecap', 'stroke-linejoin', 'opacity', 'fill-opacity', 'stroke-opacity', 'transform', 'data-part']);
function strictSvgProblems(svg) {
  const tag = /<(\/?)([a-z]+)((?:\s+[a-z][a-z0-9-]*="[^"<>]*")*)\s*(\/?)>/y;
  const problems = [];
  let at = 0;
  while (at < svg.length) {
    if (/\s/.test(svg[at])) { at++; continue; }
    tag.lastIndex = at;
    const match = tag.exec(svg);
    if (!match) { problems.push('unparsable markup at ' + at + ': ' + svg.slice(at, at + 40)); break; }
    if (!SVG_ELEMENTS.has(match[2])) problems.push('element <' + match[2] + '>');
    for (const attribute of match[3].matchAll(/([a-z][a-z0-9-]*)="([^"]*)"/g)) {
      if (!SVG_ATTRIBUTES.has(attribute[1])) problems.push('attribute ' + attribute[1]);
      if (/url\(|javascript:/i.test(attribute[2])) problems.push('unsafe value in ' + attribute[1]);
    }
    at = tag.lastIndex;
  }
  return problems;
}

test('teaching schemas are safe, every drawn structure is explained, and linked cases highlight real structures', () => {
  const schemas = catalog.schemas;
  assert.ok(schemas.length >= 12, 'The atlas ships the urology teaching schemas');
  assert.equal(new Set(schemas.map(s => s.id)).size, schemas.length, 'Schema ids are unique');
  for (const s of schemas) {
    assert.equal(s.viewBox, '0 0 600 420', s.id + ' uses the shared canvas');
    shape({ title: s.title, caption: s.caption, parts: s.parts.map(p => ({ label: p.label, note: p.note })) }, s.id);
    assert.deepEqual(strictSvgProblems(s.svg), [], s.id + ' contains only plain shapes');
    const ids = s.parts.map(p => p.id);
    assert.equal(new Set(ids).size, ids.length, s.id + ' part ids are unique');
    assert.deepEqual([...new Set(partIdsInSvg(s.svg))].sort(), [...ids].sort(), s.id + ' draws exactly the structures it explains');
    assert.ok(ids.length >= 5 && ids.length <= 16, s.id + ' has a playable number of structures');
  }
  const linked = catalog.cases.filter(c => c.schema);
  // Drug, dose and protocol questions (sys-*) deliberately have no anatomy schema.
  const anatomical = catalog.cases.filter(c => !c.id.startsWith('sys-'));
  assert.ok(linked.length >= anatomical.length * 0.4, 'At least 40 % of the cases outside drug questions come with a schema (' + linked.length + ' of ' + anatomical.length + ')');
  assert.ok(!linked.some(c => c.id.startsWith('sys-')), 'Drug questions link no anatomy schema');
  for (const c of linked) {
    const s = schemas.find(s => s.id === c.schema.id);
    assert.ok(s, c.id + ' links a schema that exists');
    assert.ok(c.schema.parts.length >= 1 && c.schema.parts.length <= 4, c.id + ' highlights one to four structures');
    for (const part of c.schema.parts) assert.ok(s.parts.some(p => p.id === part), c.id + ' highlights ' + part + ' which ' + s.id + ' draws');
  }
  for (const s of schemas) assert.ok(linked.some(c => c.schema.id === s.id), s.id + ' explains at least one case');
});

test('a case schema glows on its key structures, and the quiz view never names the answer', () => {
  const { api } = schemaHarness();
  const c = catalog.cases.find(c => c.schema && c.schema.parts.length >= 2);
  const s = catalog.schemas.find(s => s.id === c.schema.id);
  const html = api.caseVisuals(c);
  const glowing = [...html.matchAll(/data-part="([^"]+)"[^>]*class="hl"/g)].map(m => m[1]);
  assert.deepEqual(glowing.sort(), [...c.schema.parts].sort(), 'Exactly the case structures glow');
  const chips = [...html.matchAll(/data-legend-part="([^"]+)">(★ )?/g)];
  assert.equal(chips.length, s.parts.length, 'The legend lists every structure');
  assert.deepEqual(chips.slice(0, c.schema.parts.length).map(m => [m[1], m[2]]), clone(c.schema.parts.map(p => [p, '★ '])), 'Case structures lead the legend with a star');
  assert.ok(chips.slice(c.schema.parts.length).every(m => !m[2]));
  assert.equal(api.schemaFigure(s.id, ['not-a-part']).includes('class="hl"'), false, 'Unknown highlights are ignored');
  assert.equal(api.schemaFigure('no-such-schema'), '');
  const quiz = api.schemaFigure(s.id, [], 'quiz');
  assert.doesNotMatch(quiz, /schema-legend/, 'The quiz has no legend to peek at');
  const labels = [...quiz.matchAll(/data-part="[^"]+" tabindex="0" role="button" aria-label="([^"]*)"/g)].map(m => m[1]);
  assert.equal(labels.length, s.parts.length, 'Every structure is a keyboard button');
  assert.ok(labels.every(label => label === data.NSA_TEXT.de.atlasQuiz), 'Screen-reader labels do not reveal the structure names in the quiz');
  for (const part of s.parts) assert.ok(!quiz.includes('>' + escape(part.label.de) + '<'), 'The quiz markup does not print ' + part.label.de);
  assert.ok(api.atlas().split('class="atlas-card"').length - 1 === catalog.schemas.length, 'The atlas shows every schema');
  const single = catalog.schemas.find(s => catalog.cases.filter(c => c.schema && c.schema.id === s.id).length === 1);
  if (single) {
    const card = api.atlas().split('class="atlas-card"').find(html => html.includes('data-atlas-quiz="' + single.id + '"'));
    assert.match(card, /<small>1 Fall ·/, 'One linked case reads "1 Fall", not "1 Fälle"');
  }
  assert.deepEqual(strictSvgProblems('<g data-part="a"><circle cx="1" cy="1" r="1" fill="#f00>"/onclick="x()"/></g>').length > 0, true, 'The strict check catches attributes hidden after a ">" in a value');
  assert.ok(strictSvgProblems('<img/src="x"/onerror="x()"').length > 0, 'The strict check catches an unterminated foreign tag');
});

test('the find-the-structure quiz asks five different structures, scores each round once and rewards a perfect run', () => {
  const { api, stats, state } = schemaHarness();
  const s = catalog.schemas[0];
  api.startQuiz(s.id);
  const rounds = api.quiz().rounds;
  assert.equal(rounds.length, 5);
  assert.equal(new Set(rounds).size, 5, 'No structure is asked twice');
  assert.ok(rounds.every(id => s.parts.some(p => p.id === id)));
  const wrong = s.parts.find(p => p.id !== rounds[0]).id;
  let figure = fakeFigure();
  api.answerQuiz(figure, 'not-a-structure', null);
  assert.equal(api.quiz().answered, null, 'A tap on something that is not a structure does not use up the round');
  api.answerQuiz(figure, wrong, null);
  api.answerQuiz(figure, rounds[0], null);
  assert.equal(api.quiz().score, 0, 'A second tap in the same round changes nothing');
  assert.deepEqual(figure.marks[rounds[0]], ['right', 'on'], 'The wanted structure is revealed');
  assert.deepEqual(figure.marks[wrong], ['wrong']);
  assert.deepEqual(stats.sounds, ['splash']);
  assert.equal(stats.splashes, 1, 'A wrong tap splashes instead of confetti');
  api.next();
  for (let i = 1; i < 5; i++) { figure = fakeFigure(); api.answerQuiz(figure, rounds[i], null); api.next(); }
  assert.equal(api.quiz().score, 4);
  assert.equal(state.stats.atlasPerfect, 0, 'Four of five is not perfect');
  assert.match(stats.dialogs.at(-1), /4 von 5/, "The result names the score");
  api.startQuiz(s.id);
  for (let i = 0; i < 5; i++) { api.answerQuiz(fakeFigure(), api.quiz().rounds[i], null); api.next(); }
  assert.equal(state.stats.atlasPerfect, 1, 'A perfect quiz counts towards the anatomist sticker');
  assert.equal(stats.rewards, 1);
  assert.equal(stats.celebrations.at(-1), true, 'A perfect quiz ends with big confetti');
});

test('keyboard focus never hides what a structure shows', () => {
  const css = read('cartoon.css');
  const ring = css.indexOf('.schema [data-part]:focus-visible,.schema [data-part].hl:focus-visible{');
  assert.ok(ring > 0, 'Focused structures get a ring');
  for (const [verdict, colour] of [['right', '#3f8e72'], ['wrong', '#d35468']]) {
    const rule = css.indexOf('.schema [data-part].' + verdict + ':focus-visible{');
    assert.ok(rule > ring, 'A focused ' + verdict + ' quiz answer has its own rule after the general ring');
    assert.ok(css.slice(rule, css.indexOf('}', rule)).includes(colour), 'and keeps its verdict colour inside the ring');
  }
  assert.ok(css.includes('.schema.focus [data-part]:not(.on):not(.right):not(.wrong):not(:focus-visible){opacity:.32}'), 'A focused structure is not dimmed while another one is selected');
});

test('the game names no authors: no author citations, author or article mentions, or citation strings', () => {
  const shipped = JSON.stringify(catalog.cases);
  assert.doesNotMatch(shipped, /\bet al\b/, 'No "et al." anywhere in the cases');
  assert.doesNotMatch(shipped, /"citation":/, 'Source lists carry titles, not author citations');
  const mention = /\b(?:Erst|Letzt)?[Aa]utor(?:en|in|innen|es|as?)?(?:gruppe)?\b|\b[Aa]uthors?\b|\bArtikels?\b|\b[Aa]rticles?\b|\b[Aa]rtículos?\b|\b[A-ZÄÖÜ][a-zäöüß-]+ (?:&|and|und|y) [A-ZÄÖÜ][a-zäöüß-]+,? (?:19|20)\d{2}\b/;
  for (const c of catalog.cases) {
    const fields = [c.title, c.presenting, c.takeaway, c.topic, ...c.steps.flatMap(s => [s.prompt, ...s.options.flatMap(o => [o.text, o.feedback])])].filter(Boolean);
    for (const field of fields) for (const text of Object.values(field)) assert.doesNotMatch(String(text), mention, c.id + ' names an author or an article');
    for (const text of Object.values(c.objectives || {}).flat()) assert.doesNotMatch(String(text), mention, c.id + ' objectives name an author');
  }
});

// The real save-file helpers from app.js, with the constants they use taken from the same source.
function saveHarness(state) {
  const source = read('app.js');
  const constant = name => { const match = source.match(new RegExp('const ' + name + '=[^\\n]*;')); assert.ok(match, name + ' is declared in app.js'); return match[0]; };
  const section = (from, to) => { const start = source.indexOf(from), end = source.indexOf(to, start); assert.ok(start >= 0 && end > start, from + ' must be present'); return source.slice(start, end); };
  const context = vm.createContext({ C: catalog, E, state, getCase: id => catalog.cases.find(c => c.id === id) });
  vm.runInContext([constant('SAVE_FORMAT'), constant('BADGE_ICONS'), constant('STAT_KEYS'), constant('RANK_COUNT'), constant('ATTENDING_CALLS'), constant('DUTIES'), constant('count')].join('\n') + '\n' +
    section('  function validRecord(r)', '  // Career XP counts') + section('  function validBoss(boss)', '  function bossCorrect(boss)') +
    '\nglobalThis.helpers = { cleanSave, saveFile, readSaveFile, mergeSave, chooseShift, hasProgress };', context, { filename: 'app-save-helpers.js' });
  return context.helpers;
}
function playedState() {
  const done = completedSession('save-roundtrip');
  const history = done.patients.map(p => ({ ...E.record(done, catalog, p.id), shift: done.seed }));
  const open = E.create(catalog, E.schedule(catalog, 'save-open'), 'shift', 'save-open');
  const first = open.patients[0], c = catalog.cases.find(c => c.id === first.id);
  E.answer(open, catalog, c.id, c.steps[0].best); E.next(open, catalog, c.id);
  for (const p of open.patients) p.logged = p.finished;
  Object.assign(open, { duty: 'night', coffees: 2, streak: 1, bestStreak: 1, jokers: 0, streakAt: null, struck: {}, counted: false, bossCounted: false, calls: 0, called: {} });
  return { lang: 'de', name: 'Dr. Test', avatar: 2, sound: false, history, bookmarks: [history[0].caseId], session: open,
    stats: { shifts: 3, perfectShifts: 1, bossPerfect: 0, maxCoffees: 4, bestStreak: 6, jokers: 2, rank: 2, atlasPerfect: 1 }, badges: ['firstCase', 'streak5'], lastDuty: 'board',
    countedShifts: ['shift:' + done.seed] };
}
const emptyState = () => ({ lang: 'en', name: '', avatar: 0, sound: false, history: [], bookmarks: [], session: null,
  stats: { shifts: 0, perfectShifts: 0, bossPerfect: 0, maxCoffees: 0, bestStreak: 0, jokers: 0, rank: 0, atlasPerfect: 0 }, badges: [], lastDuty: 'night', countedShifts: [] });
const fileOf = state => JSON.parse(JSON.stringify(saveHarness(state).saveFile()));

test('a downloaded game file loads again on a fresh device with logbook, counters, stickers and the open shift', () => {
  const played = playedState(), file = fileOf(played);
  assert.equal(file.format, 'night-shift-academy-save');
  assert.equal(file.version, 3);
  const fresh = emptyState(), api = saveHarness(fresh);
  const found = api.readSaveFile(file);
  assert.ok(found && found.full && found.named);
  assert.equal(found.skipped, 0);
  const merged = clone(api.mergeSave(fresh, found));
  assert.deepEqual(merged.history, clone(played.history), 'Every logbook entry comes back unchanged');
  assert.deepEqual(merged.session, clone(played.session), 'The open shift continues where it stopped');
  assert.deepEqual({ ...merged.stats, rank: played.stats.rank }, played.stats);
  assert.equal(merged.stats.rank, 0, 'The rank is recalculated from the logbook after loading, never taken from the file');
  assert.deepEqual(merged.badges, played.badges);
  assert.deepEqual(merged.bookmarks, played.bookmarks);
  assert.deepEqual(merged.countedShifts, played.countedShifts);
  assert.deepEqual([merged.name, merged.avatar, merged.lastDuty], ['Dr. Test', 2, 'board']);
  const again = clone(api.mergeSave(merged, found));
  assert.equal(again.history.length, played.history.length, 'Loading the same file twice does not count anything twice');
  const replayed = clone(merged);
  replayed.history = replayed.history.concat(played.history.slice(0, 2).map(r => ({ ...r, completedAt: '2030-01-01T00:00:00.000Z' })));
  assert.equal(clone(api.mergeSave(emptyState(), api.readSaveFile(fileOf(replayed)))).history.length, played.history.length, 'The same patient of the same shift counts once');
});

test('loading keeps the progress already on the device and accepts old logbook-only exports', () => {
  const played = playedState(), device = playedState();
  device.history = device.history.slice(0, 2).map(r => ({ ...r, shift: 'other-shift', completedAt: '2026-01-01T08:00:00.000Z' }));
  device.session = null;
  device.stats.shifts = 9; device.badges = ['coffee5']; device.bookmarks = [played.history[1].caseId];
  device.name = 'Kept'; device.avatar = 1;
  const api = saveHarness(device);
  const logbook = { version: 2, exportedAt: '2026-05-01T10:00:00.000Z', history: clone(played.history).map(({ shift, ...r }) => r) };
  const found = api.readSaveFile(logbook);
  assert.ok(found && !found.full && !found.named, 'Version-2 logbooks still load');
  const merged = clone(api.mergeSave(device, found));
  assert.equal(merged.history.length, 2 + played.history.length, 'Both logbooks are combined');
  assert.ok(merged.history.every((r, i, all) => i === 0 || Date.parse(all[i - 1].completedAt) <= Date.parse(r.completedAt)), 'in time order');
  assert.equal(merged.session, null, 'A logbook without a shift leaves the device without one');
  assert.equal(merged.stats.shifts, 9, 'Counters keep the higher value');
  assert.deepEqual([merged.name, merged.avatar, merged.lastDuty], ['Kept', 1, device.lastDuty], 'A logbook-only file does not rename the player');
  const withShift = clone(api.mergeSave(device, api.readSaveFile(fileOf(played))));
  assert.deepEqual(withShift.session, clone(played.session), 'A shift in the file is taken when the device has none');
  assert.deepEqual(withShift.badges.sort(), ['coffee5', 'firstCase', 'streak5']);
  assert.deepEqual(withShift.bookmarks.sort(), [played.history[0].caseId, played.history[1].caseId].sort());
  const unnamed = { ...played, name: '', avatar: 2 };
  assert.equal(clone(api.mergeSave(emptyState(), api.readSaveFile(fileOf(unnamed)))).avatar, 2, 'A fresh device takes the avatar even without a name');
  assert.equal(clone(api.mergeSave(device, api.readSaveFile(fileOf(unnamed)))).avatar, 1, 'A named device keeps its avatar for an unnamed file');
  const stickersOnly = { ...emptyState(), badges: ['anatomist'], stats: { ...emptyState().stats, atlasPerfect: 2 }, bookmarks: [played.history[0].caseId] };
  assert.ok(saveHarness(stickersOnly).hasProgress(stickersOnly), 'Stickers and bookmarks alone are progress worth saving');
  assert.ok(api.readSaveFile(fileOf(stickersOnly)), 'and such a file loads');
});

test('the shift that continues is never a step back: same shift further along, open before finished', () => {
  const played = playedState(), api = saveHarness(emptyState());
  const older = clone(played.session), newer = clone(played.session);
  const second = newer.patients.find(p => !p.finished), c = catalog.cases.find(c => c.id === second.id);
  newer.selected = second.id;
  while (newer.clock < second.availableAt) E.wait(newer);
  E.answer(newer, catalog, c.id, c.steps[0].best);
  assert.equal(api.chooseShift(newer, older).outcome, 'ahead', 'An older copy of the same shift does not replace the device copy');
  assert.equal(api.chooseShift(newer, older).session, newer);
  assert.equal(api.chooseShift(older, newer).outcome, 'same', 'A newer copy of the same shift is taken');
  const finished = completedSession('save-finished');
  assert.equal(api.chooseShift(older, finished).outcome, 'kept', 'A finished shift in the file does not replace an open shift');
  assert.equal(api.chooseShift(finished, older).outcome, 'takes', 'An open shift in the file replaces a finished one on the device');
  const other = E.create(catalog, E.schedule(catalog, 'save-other'), 'shift', 'save-other');
  assert.equal(api.chooseShift(older, other).outcome, 'replaces', 'Two different open shifts: the file wins, and the dialog warns');
  assert.equal(api.chooseShift(older, null).outcome, 'none');
});

test('a game file is untrusted: wrong formats, changed scores, unknown cases and smuggled keys are refused', () => {
  const played = playedState(), api = saveHarness(emptyState());
  const file = () => fileOf(played);
  for (const bad of [null, [], 'text', 42, {}, { version: 2 }, { version: 3, history: [] }, { ...file(), format: 'other-game' }, { ...file(), version: 4 },
    { format: 'night-shift-academy-save', version: 2, history: file().history }, { ...file(), history: [], session: null, badges: [], bookmarks: [], stats: {} }]) {
    assert.equal(api.readSaveFile(bad), null, 'Refused: ' + JSON.stringify(bad).slice(0, 60));
  }
  const tampered = file();
  tampered.history[0].score += 10;
  tampered.history[1].caseId = 'no-such-case';
  tampered.history[2].completedAt = 12345;
  tampered.history[3].evil = '<img src=x onerror=alert(1)>';
  tampered.history[3].answers[0].evil = 'x';
  tampered.history[4].shift = 'x'.repeat(500);
  tampered.badges = ['toString', '__proto__', 'constructor', 'firstCase', 'firstCase'];
  tampered.bookmarks = ['no-such-case', { id: 1 }, played.history[0].caseId];
  tampered.session.patients[0].score += 10;
  tampered.name = 'N'.repeat(31) + '🦉🦉'; tampered.avatar = 99; tampered.lastDuty = 'party';
  tampered.stats = { shifts: -3, jokers: 'many', rank: 99, bestStreak: 4, atlasPerfect: 1e300 };
  tampered.countedShifts = ['shift:a', 7, 'x'.repeat(400)];
  const found = api.readSaveFile(tampered);
  assert.equal(found.skipped, 3, 'Changed score, unknown case and a non-text time are skipped');
  assert.equal(found.save.history.length, played.history.length - 3);
  assert.ok(found.save.history.every(r => !('evil' in r) && r.answers.every(a => !('evil' in a))), 'Only known record fields are kept');
  assert.ok(found.save.history.every(r => !r.shift || r.shift.length <= 120), 'An overlong shift tag is dropped');
  assert.deepEqual(clone(found.save.badges), ['firstCase'], 'Inherited object keys are not stickers');
  assert.deepEqual(clone(found.save.bookmarks), [played.history[0].caseId]);
  assert.equal(found.save.session, null, 'A shift whose points were changed is dropped');
  assert.equal(Array.from(found.save.name).length, 32, 'Names are cut by characters, never through an emoji');
  assert.ok(!found.save.name.includes('�'));
  assert.deepEqual([found.save.avatar, found.save.lastDuty], [0, 'night']);
  assert.deepEqual(clone(found.save.stats), { shifts: 0, perfectShifts: 0, bossPerfect: 0, maxCoffees: 0, bestStreak: 4, jokers: 0, rank: 8, atlasPerfect: 1000000 });
  assert.deepEqual(clone(found.save.countedShifts), ['shift:a']);
  const smuggled = file();
  Object.assign(smuggled.session, { junk: 'J'.repeat(1000), seed: smuggled.session.seed });
  smuggled.session.patients[0].extra = { deep: [[[]]] };
  smuggled.session.patients[0].answers[0].extra = 1;
  const p0 = smuggled.session.patients[0];
  smuggled.session.struck = { [p0.id + ':0']: catalog.cases.find(c => c.id === p0.id).steps[0].options[0].id, 'nobody:0': 'a', [p0.id + ':0x']: 'a', [p0.id + ':9']: 'a', [p0.id + ':1']: { evil: true } };
  smuggled.session.boss = { index: 0, answers: [], done: false, items: [{ caseId: 'no-such-case', stepIndex: 0, order: [] }] };
  const session = clone(api.readSaveFile(smuggled).save.session);
  assert.ok(session, 'The valid shift itself still loads');
  assert.ok(!('junk' in session) && !('boss' in session), 'Unknown keys and an invalid morning report are dropped');
  assert.ok(!('extra' in session.patients[0]) && !('extra' in session.patients[0].answers[0]));
  assert.deepEqual(Object.keys(session.struck), [p0.id + ':0'], 'Only joker marks for real steps and options survive');
});
