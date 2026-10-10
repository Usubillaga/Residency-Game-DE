/* Pure deterministic simulation: educational time and points, never clinical predictions. */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.NSAEngine = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';
  function random(seed) {
    let h = 2166136261;
    for (const ch of String(seed)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
    return () => { h ^= h << 13; h ^= h >>> 17; h ^= h << 5; return (h >>> 0) / 4294967296; };
  }
  function shuffle(items, rng) {
    const out = items.slice();
    for (let i = out.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [out[i], out[j]] = [out[j], out[i]]; }
    return out;
  }
  function schedule(catalog, seed, perArea = 2) {
    const rng = random(seed);
    const ids = catalog.areas.flatMap(a => shuffle(catalog.cases.filter(c => c.area === a.id), rng).slice(0, perArea).map(c => c.id));
    return shuffle(ids, rng);
  }
  const DUTIES = ['night', 'board', 'clinic', 'elective', 'dayclinic', 'radiotherapy'];
  // One duty's cases only, interleaving topics so a shift does not repeat a single subject.
  function scheduleDuty(catalog, seed, duty, size = 10) {
    if (!DUTIES.includes(duty)) throw new Error('Unknown duty');
    const rng = random(seed + ':' + duty), groups = new Map();
    for (const c of shuffle(catalog.cases.filter(c => c.duty === duty), rng)) {
      const key = c.source ? c.source.domain : 'story-' + c.area;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(c.id);
    }
    const queues = shuffle([...groups.values()], rng), ids = [];
    while (ids.length < size && queues.some(q => q.length)) {
      for (const q of queues) if (q.length && ids.length < size) ids.push(q.shift());
    }
    return ids;
  }
  function create(catalog, ids, mode, seed) {
    const unique = [...new Set(ids)];
    if (!unique.length || unique.length !== ids.length || unique.some(id => !catalog.cases.some(c => c.id === id))) throw new Error('Invalid case schedule');
    const rng = random(seed);
    const patients = unique.map((id, i) => {
      const c = catalog.cases.find(x => x.id === id);
      return { id, index:0, answers:[], score:0, elapsed:0, criticalErrors:0, availableAt:mode === 'shift' ? i * 10 : 0, feedback:null, finished:false,
        order:c.steps.map(s => shuffle(s.options.map(o => o.id), rng)) };
    });
    return {version:2, mode, seed:String(seed), clock:0, patients, selected:unique[0], finished:false};
  }
  function answer(session, catalog, caseId, optionId) {
    if (session.finished) throw new Error('Session finished');
    const p = session.patients.find(p => p.id === caseId);
    const c = catalog.cases.find(c => c.id === caseId);
    if (!p || p.finished || p.feedback || session.clock < p.availableAt) throw new Error('Case unavailable');
    const step = c.steps[p.index], option = step.options.find(o => o.id === optionId);
    if (!option) throw new Error('Unknown choice');
    p.answers.push({stepId:step.id,optionId:option.id,score:option.score,minutes:option.minutes});
    p.score += option.score; p.elapsed += option.minutes;
    p.criticalErrors += option.critical ? 1 : 0;
    session.clock += option.minutes; p.feedback = option.id;
    return option;
  }
  function next(session, catalog, caseId) {
    const p = session.patients.find(p => p.id === caseId);
    const c = catalog.cases.find(c => c.id === caseId);
    if (!p || !p.feedback || p.finished) throw new Error('Answer first');
    p.feedback = null;
    if (++p.index >= c.steps.length) p.finished = true;
    session.finished = session.patients.every(x => x.finished);
    return p.finished;
  }
  function wait(session) {
    const future = session.patients.filter(p => !p.finished && p.availableAt > session.clock).map(p => p.availableAt);
    session.clock = future.length ? Math.min(...future) : session.clock + 5;
  }
  function record(session, catalog, caseId) {
    const p = session.patients.find(p => p.id === caseId), c = catalog.cases.find(c => c.id === caseId);
    if (!p || !p.finished) throw new Error('Incomplete case');
    return {caseId,area:c.area,score:p.score,maxScore:c.steps.reduce((n,s) => n + Math.max(...s.options.map(o => o.score)),0),elapsed:p.elapsed,
      criticalErrors:p.criticalErrors,completedAt:new Date().toISOString(),answers:p.answers.map(a=>({...a}))};
  }
  function validSession(s, catalog) {
    try {
      if (!s || s.version !== 2 || !['learn','shift'].includes(s.mode) || typeof s.seed !== 'string' || !Number.isInteger(s.clock) || s.clock < 0 || typeof s.finished !== 'boolean' ||
        !Array.isArray(s.patients) || !s.patients.length || s.patients.length > catalog.cases.length || new Set(s.patients.map(p=>p.id)).size !== s.patients.length) return false;
      if (!s.patients.some(p=>p.id === s.selected)) return false;
      return s.patients.every((p, patientIndex) => {
        const c = catalog.cases.find(c=>c.id === p.id);
        if (!c || !Number.isInteger(p.index) || p.index < 0 || p.index > c.steps.length || typeof p.finished !== 'boolean' ||
          p.finished !== (p.index === c.steps.length) || p.availableAt !== (s.mode === 'shift' ? patientIndex * 10 : 0) || !Array.isArray(p.answers) || !Array.isArray(p.order) || p.order.length !== c.steps.length) return false;
        if (p.answers.length !== p.index + (p.feedback ? 1 : 0)) return false;
        let score=0, elapsed=0, errors=0;
        for (let i=0; i<p.answers.length; i++) {
          const a=p.answers[i], step=c.steps[i], o=step.options.find(o=>o.id===a.optionId);
          if (!o || a.stepId!==step.id || a.score!==o.score || a.minutes!==o.minutes) return false;
          score+=o.score; elapsed+=o.minutes; errors+=o.critical?1:0;
        }
        if (p.score!==score || p.elapsed!==elapsed || p.criticalErrors!==errors || (p.feedback && p.feedback!==p.answers[p.answers.length-1].optionId)) return false;
        return p.order.every((order,i)=>Array.isArray(order) && order.length===c.steps[i].options.length && new Set(order).size===order.length && order.every(id=>c.steps[i].options.some(o=>o.id===id)));
      }) && s.finished === s.patients.every(p=>p.finished) && s.clock >= s.patients.reduce((n,p)=>n+p.elapsed,0);
    } catch (_) { return false; }
  }
  return { random,shuffle,schedule,DUTIES,scheduleDuty,create,answer,next,wait,record,validSession };
});
