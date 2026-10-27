/* Urodynamic tracings for the urodynamics lab: stacked ICS channels drawn from data/urodynamic-tracings.json.
 * The curves are synthetic teaching drawings. A cursor reads every channel at one moment; the findings of a
 * step are marked only after it has been answered. No network access, no external libraries.
 */
(function(root) {
  'use strict';
  const TEXT = {
    en: {
      title: 'Urodynamic tracing', uroflow: 'Uroflowmetry', note: 'Synthetic teaching curve following ICS conventions, not a patient recording.',
      hint: 'Tap or drag along the curves, or use ← → (Shift for bigger steps), to read every channel at that moment.',
      views: 'Section', markers: 'Markers', findings: 'Findings', time: 'Time', start: 'Move the cursor over the curves.',
      position: { sitting: 'sitting', supine: 'supine', standing: 'standing' }, rate: 'filling {r} ml/min',
      kind: { 'pressure-flow': 'Cystometry and pressure-flow study', 'video-pressure-flow': 'Video-urodynamics with pressure-flow study', cystometry: 'Filling cystometry', 'video-cystometry': 'Video-cystometry', uroflow: 'Uroflowmetry', 'uroflow-emg': 'Uroflowmetry with pelvic floor EMG' },
      vinf: 'infused', vvoid: 'voided', vinfShort: 'inf', vvoidShort: 'void',
      events: { cough: ['C', 'Cough'], valsalva: ['Vs', 'Straining (Valsalva)'], fs: ['FS', 'First sensation of filling'], fd: ['FD', 'First desire to void'], sd: ['SD', 'Strong desire to void'],
        urgency: ['U', 'Urgency'], leak: ['L', 'Leakage seen'], void: ['Void', 'Permission to void'], qmax: ['Qmax', 'Maximum flow marked by the software'], reduction: ['Red', 'Prolapse reduced with a speculum'],
        provocation: ['Prov', 'Provocation: running water and hand washing'], drain: ['Drain', 'Bladder drained through the catheter'], recatheterise: ['Cath', 'New vesical catheter, refill'],
        bloodPressure: ['BP', 'Blood pressure'], stop: ['Stop', 'Filling stopped'], flush: ['Flush', 'Vesical line flushed'] }
    },
    de: {
      title: 'Urodynamische Messkurve', uroflow: 'Uroflowmetrie', note: 'Synthetische Lernkurve nach ICS-Konventionen, keine Patientenmessung.',
      hint: 'Tippe oder ziehe entlang der Kurven oder nutze ← → (mit Umschalt größere Schritte), um alle Kanäle in diesem Moment abzulesen.',
      views: 'Ausschnitt', markers: 'Markierungen', findings: 'Befunde', time: 'Zeit', start: 'Bewege den Cursor über die Kurven.',
      position: { sitting: 'sitzend', supine: 'in Rückenlage', standing: 'stehend' }, rate: 'Füllung {r} ml/min',
      kind: { 'pressure-flow': 'Zystometrie und Druck-Fluss-Messung', 'video-pressure-flow': 'Videourodynamik mit Druck-Fluss-Messung', cystometry: 'Füllungszystometrie', 'video-cystometry': 'Videozystometrie', uroflow: 'Uroflowmetrie', 'uroflow-emg': 'Uroflowmetrie mit Beckenboden-EMG' },
      vinf: 'infundiert', vvoid: 'entleert', vinfShort: 'inf', vvoidShort: 'entl',
      events: { cough: ['H', 'Husten'], valsalva: ['VS', 'Pressen (Valsalva)'], fs: ['EF', 'Erstes Füllungsgefühl'], fd: ['EHD', 'Erster Harndrang'], sd: ['SHD', 'Starker Harndrang'],
        urgency: ['D', 'Imperativer Drang'], leak: ['L', 'Leckage beobachtet'], void: ['Mikt.', 'Miktionserlaubnis'], qmax: ['Qmax', 'Maximaler Fluss, von der Software markiert'], reduction: ['Rep.', 'Prolaps mit Spekulum reponiert'],
        provocation: ['Prov.', 'Provokation: Wasser laufen lassen, Hände waschen'], drain: ['Abl.', 'Blase über den Katheter abgelassen'], recatheterise: ['Kath.', 'Neuer Blasenkatheter, erneute Füllung'],
        bloodPressure: ['RR', 'Blutdruck'], stop: ['Stopp', 'Füllung gestoppt'], flush: ['Spül.', 'Blasendruckleitung gespült'] }
    },
    es: {
      title: 'Trazado urodinámico', uroflow: 'Flujometría', note: 'Curva didáctica sintética según las convenciones de la ICS; no es el registro de un paciente.',
      hint: 'Toca o arrastra a lo largo de las curvas, o usa ← → (Mayús para pasos mayores), para leer todos los canales en ese instante.',
      views: 'Tramo', markers: 'Marcas', findings: 'Hallazgos', time: 'Tiempo', start: 'Mueve el cursor sobre las curvas.',
      position: { sitting: 'en sedestación', supine: 'en decúbito supino', standing: 'en bipedestación' }, rate: 'llenado {r} ml/min',
      kind: { 'pressure-flow': 'Cistometría y estudio presión-flujo', 'video-pressure-flow': 'Videourodinámica con estudio presión-flujo', cystometry: 'Cistometría de llenado', 'video-cystometry': 'Videocistometría', uroflow: 'Flujometría', 'uroflow-emg': 'Flujometría con EMG del suelo pélvico' },
      vinf: 'infundido', vvoid: 'evacuado', vinfShort: 'inf', vvoidShort: 'evac',
      events: { cough: ['T', 'Tos'], valsalva: ['Vs', 'Prensa abdominal (Valsalva)'], fs: ['PS', 'Primera sensación de llenado'], fd: ['PD', 'Primer deseo miccional'], sd: ['DF', 'Deseo miccional fuerte'],
        urgency: ['U', 'Urgencia'], leak: ['E', 'Escape observado'], void: ['Mic.', 'Permiso para orinar'], qmax: ['Qmax', 'Flujo máximo marcado por el programa'], reduction: ['Red.', 'Prolapso reducido con espéculo'],
        provocation: ['Prov.', 'Provocación: agua corriendo, lavado de manos'], drain: ['Vac.', 'Vejiga vaciada por la sonda'], recatheterise: ['Sonda', 'Nueva sonda vesical, nuevo llenado'],
        bloodPressure: ['PA', 'Presión arterial'], stop: ['Fin', 'Llenado detenido'], flush: ['Purga', 'Línea vesical purgada'] }
    }
  };
  const CHANNEL = {
    pves: { label: 'Pves', unit: 'cmH2O', color: '#2563a8' },
    pabd: { label: 'Pabd', unit: 'cmH2O', color: '#2f7d55' },
    pdet: { label: 'Pdet', unit: 'cmH2O', color: '#b83250' },
    flow: { label: 'Q', unit: 'ml/s', color: '#b8601a' },
    vol: { label: 'V', unit: 'ml', color: '#6b6280' },
    vvoid: { label: 'V', unit: 'ml', color: '#b8601a' },
    emg: { label: 'EMG', unit: 'µV', color: '#6d4fb3' }
  };
  const TONE = { key: '#e8a13a', good: '#3f8e72', neutral: '#8a7f95' };
  const LAYOUT = {
    wide: { w: 960, left: 92, right: 16, top: 34, panel: 62, gap: 9, axis: 26, font: 12.5, small: 10.5, label: 15 },
    narrow: { w: 560, left: 84, right: 8, top: 38, panel: 74, gap: 9, axis: 30, font: 15, small: 13, label: 17 }
  };
  let sequence = 0;

  function lang(language) { return TEXT[language] ? language : 'en'; }
  function esc(value) { return String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]); }
  function decimal(value, digits, language) {
    const text = Number(value).toFixed(digits);
    return language === 'en' ? text : text.replace('.', ',');
  }
  function clock(seconds) {
    const s = Math.max(0, Math.round(seconds));
    return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
  }
  function pdetAt(tr, i) { return tr.pves[i] - tr.pabd[i]; }
  function value(tr, channel, i) {
    if (channel === 'pdet') return pdetAt(tr, i);
    if (channel === 'vol') return tr.vinf ? tr.vinf[i] : tr.vvoid[i];
    return tr[channel] ? tr[channel][i] : null;
  }
  function nearest(tr, time) {
    const t = tr.t;
    let lo = 0, hi = t.length - 1;
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (t[mid] <= time) lo = mid; else hi = mid;
    }
    return Math.abs(t[hi] - time) < Math.abs(t[lo] - time) ? hi : lo;
  }
  // A part of a study that would give an answer away (a repeat study, a second fill, what was done next) stays
  // hidden until that decision has been answered: the tracing then ends where the hidden part begins.
  function limitOf(tr, reveal) {
    const done = new Set(reveal || []);
    return (tr.conceal || []).reduce((limit, c) => done.has(c.until) ? limit : Math.min(limit, c.from), Infinity);
  }
  function viewsOf(tr, limit) {
    return (tr.views || []).filter(v => !v.t || v.t[0] < limit);
  }
  function viewOf(tr, id, limit) {
    const end = limit === undefined ? Infinity : limit, views = viewsOf(tr, end);
    const view = views.find(v => v.id === id) || views[0] || { id: 'all' };
    const range = view.t || [tr.t[0], tr.t[tr.t.length - 1]];
    return { id: view.id, label: view.label, t0: range[0], t1: Math.min(range[1], end) };
  }
  // The filling rate of the section: every rate that runs through at least a fifth of it (for example 30 → 15).
  function caption(tr, view, language) {
    const w = TEXT[lang(language)], span = view.t1 - view.t0;
    const rates = tr.rates || (tr.fillingRate ? [[tr.t[0], tr.fillingRate]] : []);
    const shown = rates.filter((r, k) => Math.min(view.t1, k + 1 < rates.length ? rates[k + 1][0] : Infinity) - Math.max(view.t0, r[0]) >= 0.2 * span).map(r => r[1]);
    return (w.kind[tr.kind] || w.title) + ' · ' + [tr.position ? w.position[tr.position] : '', shown.length ? w.rate.replace('{r}', shown.join(' → ')) : ''].filter(Boolean).join(' · ');
  }
  function niceMax(max, steps) {
    for (const step of steps) if (max <= step) return step;
    return steps[steps.length - 1];
  }
  // Ranges are chosen from the whole tracing so switching sections keeps the scales comparable.
  function ranges(tr) {
    if (tr._ranges) return tr._ranges;
    const n = tr.t.length, pres = [], det = [];
    let low = 0;
    for (let i = 0; i < n; i++) {
      if (tr.pves) { pres.push(Math.max(tr.pves[i], tr.pabd[i])); det.push(pdetAt(tr, i)); low = Math.min(low, tr.pves[i], tr.pabd[i]); }
    }
    const sorted = pres.slice().sort((a, b) => a - b), q = sorted[Math.floor(sorted.length * 0.985)] || 0;
    const detSorted = det.slice().sort((a, b) => a - b), dq = detSorted[Math.floor(detSorted.length * 0.995)] || 0, dmin = detSorted[0] || 0;
    const flowMax = tr.flow ? Math.max(...tr.flow) : 0;
    const volMax = Math.max(tr.vinf ? Math.max(...tr.vinf) : 0, tr.vvoid ? Math.max(...tr.vvoid) : 0);
    tr._ranges = {
      pves: [0, niceMax(q * 1.05, [50, 100, 125, 150, 200])],
      pabd: [0, niceMax(q * 1.05, [50, 100, 125, 150, 200])],
      pdet: [dmin < -6 ? -Math.max(40, Math.ceil((2 - dmin) / 10) * 10) : -10, niceMax(dq * 1.1 + 4, [30, 50, 75, 100, 125, 150])],
      flow: [0, niceMax(flowMax * 1.08, [5, 10, 15, 20, 25, 30, 40, 50])],
      vol: [0, niceMax(volMax * 1.06, [100, 200, 300, 400, 500, 600, 800, 1000, 1200])],
      vvoid: [0, niceMax(volMax * 1.06, [100, 200, 300, 400, 500, 600, 800, 1000])],
      emg: [0, 100]
    };
    // A line that drops below zero (an expelled catheter) keeps a little room under the zero line.
    tr._ranges.pves = tr._ranges.pabd = [low < -1 ? Math.floor((low - 3) / 10) * 10 : 0, Math.max(tr._ranges.pves[1], tr._ranges.pabd[1])];
    return tr._ranges;
  }
  function geometry(tr, layoutName) {
    const layout = LAYOUT[layoutName] || LAYOUT.wide, panels = [];
    let y = layout.top;
    for (const id of tr.channels) {
      panels.push({ id, top: y, bottom: y + layout.panel, range: ranges(tr)[id] || [0, 100] });
      y += layout.panel + layout.gap;
    }
    return { layout, panels, height: y - layout.gap + layout.axis, x0: layout.left, x1: layout.w - layout.right };
  }
  function ticks(min, max) {
    const span = max - min, step = span <= 10 ? 5 : span <= 30 ? 10 : span <= 80 ? 25 : span <= 160 ? 50 : span <= 400 ? 100 : span <= 800 ? 200 : 250;
    const out = [];
    for (let v = Math.ceil(min / step) * step; v <= max + 1e-9; v += step) out.push(v);
    return out;
  }
  function timeTicks(t0, t1) {
    const span = t1 - t0, step = span <= 30 ? 5 : span <= 90 ? 10 : span <= 200 ? 30 : span <= 600 ? 60 : span <= 1300 ? 120 : 300;
    const out = [];
    for (let v = Math.ceil(t0 / step) * step; v <= t1 + 1e-9; v += step) out.push(v);
    return out;
  }
  function revealed(tr, steps) {
    const done = new Set(steps || []);
    return (tr.annotations || []).filter(a => done.has(a.step));
  }

  function plot(tr, options) {
    const o = options || {}, language = lang(o.lang), w = TEXT[language], view = viewOf(tr, o.view, limitOf(tr, o.reveal));
    const g = geometry(tr, o.layout), L = g.layout, id = 'udy' + (++sequence);
    const sx = t => g.x0 + (t - view.t0) / (view.t1 - view.t0) * (g.x1 - g.x0);
    const sy = (panel, v) => panel.bottom - (Math.max(panel.range[0], Math.min(panel.range[1], v)) - panel.range[0]) / (panel.range[1] - panel.range[0]) * (panel.bottom - panel.top);
    const i0 = Math.max(0, nearest(tr, view.t0) - 1), i1 = Math.min(tr.t.length - 1, nearest(tr, view.t1) + 1);
    let s = '<svg class="udy-svg" viewBox="0 0 ' + L.w + ' ' + g.height.toFixed(1) + '" role="img" aria-label="' + esc(w.title + ' · ' + (view.label ? view.label[language] : '')) + '" xmlns="http://www.w3.org/2000/svg"' +
      ' data-x0="' + g.x0 + '" data-x1="' + g.x1 + '" data-t0="' + view.t0 + '" data-t1="' + view.t1 + '" data-width="' + L.w + '">';
    s += '<defs>' + g.panels.map((p, k) => '<clipPath id="' + id + '-c' + k + '"><rect x="' + g.x0 + '" y="' + (p.top - 1) + '" width="' + (g.x1 - g.x0) + '" height="' + (p.bottom - p.top + 2) + '"/></clipPath>').join('') + '</defs>';
    // Panels, grid lines, scales and channel names.
    g.panels.forEach(p => {
      const c = CHANNEL[p.id];
      s += '<rect x="' + g.x0 + '" y="' + p.top + '" width="' + (g.x1 - g.x0) + '" height="' + (p.bottom - p.top) + '" fill="#fffdf6" stroke="#cdbfa6" stroke-width="1"/>';
      for (const v of ticks(p.range[0], p.range[1])) {
        const y = sy(p, v).toFixed(1);
        s += '<path d="M' + g.x0 + ' ' + y + 'H' + g.x1 + '" stroke="' + (v === 0 ? '#b9ab92' : '#eadfc8') + '" stroke-width="' + (v === 0 ? 1.2 : 1) + '"/>';
        s += '<text x="' + (g.x0 - 5) + '" y="' + (Number(y) + L.small * 0.35).toFixed(1) + '" text-anchor="end" font-size="' + L.small + '" fill="#7a6d80">' + v + '</text>';
      }
      s += '<text x="6" y="' + (p.top + L.label + 1) + '" font-size="' + L.label + '" font-weight="800" fill="' + c.color + '">' + esc(c.label) + '</text>';
      s += '<text x="6" y="' + (p.top + L.label * 2.05) + '" font-size="' + L.small + '" fill="#7a6d80">' + esc(c.unit) + '</text>';
    });
    // Time axis: study time in minutes and seconds.
    const axisY = g.height - L.axis + 4;
    s += '<text x="6" y="' + (axisY + L.small + 2) + '" font-size="' + L.small + '" fill="#7a6d80">min:s</text>';
    for (const v of timeTicks(view.t0, view.t1)) {
      const x = sx(v).toFixed(1);
      s += '<path d="M' + x + ' ' + L.top + 'V' + (axisY - 2) + '" stroke="#efe6d2" stroke-width="1"/>';
      s += '<text x="' + x + '" y="' + (axisY + L.small + 2) + '" text-anchor="middle" font-size="' + L.small + '" fill="#7a6d80">' + clock(v) + '</text>';
    }
    // Revealed findings: shaded sections and numbered points, explained in the list under the drawing.
    const notes = o.reveal ? revealed(tr, o.reveal) : [];
    notes.forEach((a, k) => {
      const color = TONE[a.tone] || TONE.key, panel = g.panels.find(p => p.id === a.channel);
      const top = panel ? panel.top : L.top, bottom = panel ? panel.bottom : g.panels[g.panels.length - 1].bottom;
      if (a.kind === 'span') {
        const xa = sx(Math.max(view.t0, a.t0)), xb = sx(Math.min(view.t1, a.t1));
        if (xb > xa) s += '<rect class="udy-note" x="' + xa.toFixed(1) + '" y="' + top + '" width="' + Math.max(3, xb - xa).toFixed(1) + '" height="' + (bottom - top) + '" fill="' + color + '" fill-opacity=".2" stroke="' + color + '" stroke-width="1.5"/>' +
          '<circle cx="' + (xa + 11).toFixed(1) + '" cy="' + (top + 11) + '" r="9" fill="' + color + '"/><text x="' + (xa + 11).toFixed(1) + '" y="' + (top + 15) + '" text-anchor="middle" font-size="11" font-weight="800" fill="#fff">' + (k + 1) + '</text>';
      } else if (panel && a.t >= view.t0 && a.t <= view.t1) {
        const i = nearest(tr, a.t), x = sx(tr.t[i]), y = sy(panel, value(tr, a.channel, i));
        s += '<circle class="udy-note" cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="6.5" fill="none" stroke="' + color + '" stroke-width="3"/>' +
          '<circle cx="' + (x + 15).toFixed(1) + '" cy="' + Math.max(top + 10, y - 13).toFixed(1) + '" r="9" fill="' + color + '"/><text x="' + (x + 15).toFixed(1) + '" y="' + (Math.max(top + 10, y - 13) + 4).toFixed(1) + '" text-anchor="middle" font-size="11" font-weight="800" fill="#fff">' + (k + 1) + '</text>';
      }
    });
    // Curves.
    g.panels.forEach((p, k) => {
      const lines = p.id === 'vol' ? [['vinf', CHANNEL.vol.color, ''], ['vvoid', CHANNEL.vvoid.color, ' stroke-dasharray="5 3"']] : [[p.id, CHANNEL[p.id].color, '']];
      for (const [channel, color, dash] of lines) {
        if (channel !== 'pdet' && !tr[channel]) continue;
        let d = '';
        for (let i = i0; i <= i1; i++) {
          const v = channel === 'pdet' ? pdetAt(tr, i) : tr[channel][i];
          d += (d ? 'L' : 'M') + sx(tr.t[i]).toFixed(1) + ' ' + sy(p, v).toFixed(1);
        }
        s += '<path d="' + d + '" fill="none" stroke="' + color + '" stroke-width="' + (channel === 'emg' ? 1.3 : 1.9) + '" stroke-linejoin="round"' + dash + ' clip-path="url(#' + id + '-c' + k + ')"/>';
      }
      if (p.id === 'vol' && tr.vinf && tr.vvoid) {
        // The legend sits in the margin under the unit, where no curve can run through it.
        const y = p.top + L.label * 2.05 + L.small * 1.35;
        s += '<text x="6" y="' + y.toFixed(1) + '" font-size="' + L.small + '" fill="' + CHANNEL.vol.color + '"><title>' + esc(w.vinf) + '</title>— ' + esc(w.vinfShort) + '</text>' +
          '<text x="6" y="' + (y + L.small * 1.25).toFixed(1) + '" font-size="' + L.small + '" fill="' + CHANNEL.vvoid.color + '"><title>' + esc(w.vvoid) + '</title>- - ' + esc(w.vvoidShort) + '</text>';
      }
    });
    // Event markers with labels on two rows. Markers that matter for the questions are placed first; a cough
    // whose letter would collide keeps its line but not its letter.
    const shown = (tr.events || []).filter(e => e.t >= view.t0 && e.t <= view.t1 && w.events[e.type]);
    const labelOf = e => e.type === 'bloodPressure' && e.value ? w.events[e.type][0] + ' ' + e.value : w.events[e.type][0];
    const placed = [[], []], rows = shown.map(() => -1);
    const order = shown.map((_, i) => i).sort((i, j) => (shown[i].type === 'cough') - (shown[j].type === 'cough') || i - j);
    const halfOf = e => labelOf(e).length * L.small * 0.31 + 3;
    const labelX = e => Math.min(g.x1 - halfOf(e), Math.max(g.x0 + halfOf(e), sx(e.t)));
    for (const i of order) {
      const x = labelX(shown[i]), half = halfOf(shown[i]), a = x - half, b = x + half;
      let row = [0, 1].find(r => placed[r].every(([c, d]) => b < c || a > d));
      if (row === undefined && shown[i].type !== 'cough') row = placed[0].length <= placed[1].length ? 0 : 1;
      if (row === undefined) continue;
      rows[i] = row;
      placed[row].push([a, b]);
    }
    shown.forEach((e, i) => {
      const x = sx(e.t), y = 13 + Math.max(0, rows[i]) * 13 * (L.font / 12.5);
      if (e.type === 'qmax') {
        const panel = g.panels.find(p => p.id === 'flow');
        if (panel) {
          const k = nearest(tr, e.t), py = sy(panel, tr.flow[k]);
          s += '<path d="M' + x.toFixed(1) + ' ' + (py - 5).toFixed(1) + 'l-5 -9h10z" fill="#302944"/>';
        }
      } else {
        s += '<path d="M' + x.toFixed(1) + ' ' + (L.top - 3) + 'V' + (g.height - L.axis + 2) + '" stroke="#5c5168" stroke-width="1" stroke-dasharray="3 3" opacity=".55"/>';
      }
      if (rows[i] >= 0) s += '<text x="' + labelX(e).toFixed(1) + '" y="' + y.toFixed(1) + '" text-anchor="middle" font-size="' + L.small + '" font-weight="700" fill="#4a3f57">' + esc(labelOf(e)) + '</text>';
    });
    // The cursor: a line and one dot per channel, moved by bind().
    s += '<g class="udy-cursor" visibility="hidden"><path d="M0 ' + (L.top - 2) + 'V' + (g.height - L.axis + 2) + '" stroke="#302944" stroke-width="1.6"/>' +
      g.panels.map(p => '<circle data-ch="' + p.id + '" data-top="' + p.top + '" data-bottom="' + p.bottom + '" data-min="' + p.range[0] + '" data-max="' + p.range[1] + '" r="4" fill="' + CHANNEL[p.id].color + '" stroke="#fff" stroke-width="1.5"/>').join('') + '</g>';
    s += '<rect class="udy-hit" x="' + g.x0 + '" y="' + (L.top - 4) + '" width="' + (g.x1 - g.x0) + '" height="' + (g.height - L.axis - L.top + 6) + '" fill="transparent"/>';
    return s + '</svg>';
  }

  function readout(tr, i, language) {
    const lc = lang(language), w = TEXT[lc], parts = ['<b>' + esc(w.time) + ' ' + clock(tr.t[i]) + '</b>'];
    for (const ch of tr.channels) {
      if (ch === 'vol') {
        if (tr.vinf) parts.push('V<sub>' + esc(w.vinfShort) + '</sub> ' + Math.round(tr.vinf[i]) + ' ml');
        if (tr.vvoid) parts.push('V<sub>' + esc(w.vvoidShort) + '</sub> ' + Math.round(tr.vvoid[i]) + ' ml');
        continue;
      }
      if (ch === 'vvoid') { parts.push('V ' + Math.round(tr.vvoid[i]) + ' ml'); continue; }
      const c = CHANNEL[ch], v = value(tr, ch, i);
      if (v === null || v === undefined) continue;
      const text = ch === 'flow' ? decimal(v, 1, lc) : String(Math.round(v));
      parts.push('<span style="color:' + c.color + '">' + esc(c.label) + '</span> ' + text + ' ' + esc(c.unit));
    }
    const near = (tr.events || []).filter(e => Math.abs(e.t - tr.t[i]) <= 1.5 && w.events[e.type]);
    if (near.length) parts.push('<em>' + near.map(e => esc(w.events[e.type][1] + (e.value ? ' ' + e.value : ''))).join(' · ') + '</em>');
    return parts.join(' · ');
  }

  function figure(tr, options) {
    const o = options || {}, language = lang(o.lang), w = TEXT[language], limit = limitOf(tr, o.reveal), view = viewOf(tr, o.view, limit);
    const notes = o.reveal ? revealed(tr, o.reveal) : [], views = viewsOf(tr, limit);
    const used = [...new Set((tr.events || []).filter(e => e.t <= limit).map(e => e.type))].filter(type => w.events[type]);
    return '<figure class="udy" data-udy="' + esc(o.id) + '" data-view="' + esc(view.id) + '" data-reveal="' + esc((o.reveal || []).join(' ')) + '">' +
      '<figcaption><b>' + esc(caption(tr, view, language)) + '</b><small>' + esc(w.note) + '</small></figcaption>' +
      (views.length > 1 ? '<div class="udy-views" role="group" aria-label="' + esc(w.views) + '">' + views.map(v => '<button type="button" class="udy-view' + (v.id === view.id ? ' on' : '') + '" aria-pressed="' + (v.id === view.id) + '" data-udy-view="' + esc(v.id) + '">' + esc(v.label[language]) + '</button>').join('') + '</div>' : '') +
      '<div class="udy-plot" tabindex="0" role="slider" aria-label="' + esc(w.hint) + '" aria-valuemin="' + view.t0 + '" aria-valuemax="' + view.t1 + '" aria-valuenow="' + view.t0 + '" aria-valuetext="' + esc(w.start) + '">' + plot(tr, { ...o, view: view.id }) + '</div>' +
      '<p class="udy-readout" aria-live="polite">' + esc(w.start) + '</p><p class="udy-hint">' + esc(w.hint) + '</p>' +
      (notes.length ? '<ol class="udy-findings" aria-label="' + esc(w.findings) + '">' + notes.map(a => '<li class="tone-' + esc(a.tone || 'key') + '">' + esc(a.label[language]) + '</li>').join('') + '</ol>' : '') +
      (used.length ? '<details class="udy-legend"><summary>' + esc(w.markers) + '</summary><ul>' + used.map(type => '<li><b>' + esc(w.events[type][0]) + '</b> ' + esc(w.events[type][1]) + '</li>').join('') + '</ul></details>' : '') +
      '</figure>';
  }

  // Event handling: pointer and keyboard move the cursor; section buttons redraw the plot in place.
  function bind(doc, lookup, getLang, layoutFor) {
    const state = new WeakMap();
    function parts(fig) {
      const svg = fig.querySelector('.udy-svg');
      return svg && { svg, x0: +svg.dataset.x0, x1: +svg.dataset.x1, t0: +svg.dataset.t0, t1: +svg.dataset.t1, width: +svg.dataset.width };
    }
    function place(fig, time) {
      const tr = lookup(fig.dataset.udy), p = parts(fig);
      if (!tr || !p) return;
      const t = Math.max(p.t0, Math.min(p.t1, time)), i = nearest(tr, t), x = p.x0 + (tr.t[i] - p.t0) / (p.t1 - p.t0) * (p.x1 - p.x0);
      const cursor = p.svg.querySelector('.udy-cursor');
      cursor.setAttribute('visibility', 'visible');
      cursor.querySelector('path').setAttribute('transform', 'translate(' + x.toFixed(1) + ' 0)');
      cursor.querySelectorAll('circle').forEach(dot => {
        const v = value(tr, dot.dataset.ch, i), min = +dot.dataset.min, max = +dot.dataset.max;
        const y = +dot.dataset.bottom - (Math.max(min, Math.min(max, v)) - min) / (max - min) * (+dot.dataset.bottom - +dot.dataset.top);
        dot.setAttribute('cx', x.toFixed(1));
        dot.setAttribute('cy', y.toFixed(1));
      });
      state.set(fig, tr.t[i]);
      const html = readout(tr, i, getLang());
      fig.querySelector('.udy-readout').innerHTML = html;
      const box = fig.querySelector('.udy-plot');
      box.setAttribute('aria-valuenow', String(tr.t[i]));
      box.setAttribute('aria-valuetext', fig.querySelector('.udy-readout').textContent);
    }
    function timeAt(fig, clientX) {
      const p = parts(fig), rect = p.svg.getBoundingClientRect();
      const x = (clientX - rect.left) / rect.width * p.width;
      return p.t0 + (x - p.x0) / (p.x1 - p.x0) * (p.t1 - p.t0);
    }
    let dragging = null;
    doc.addEventListener('pointerdown', e => {
      const fig = e.target.closest && e.target.closest('.udy');
      if (!fig || !e.target.closest('.udy-svg')) return;
      dragging = fig;
      place(fig, timeAt(fig, e.clientX));
    });
    doc.addEventListener('pointermove', e => {
      const fig = dragging || (e.pointerType === 'mouse' && e.target.closest && e.target.closest('.udy'));
      if (!fig || !fig.querySelector('.udy-svg') || (!dragging && !e.target.closest('.udy-svg'))) return;
      place(fig, timeAt(fig, e.clientX));
    });
    doc.addEventListener('pointerup', () => { dragging = null; });
    doc.addEventListener('pointercancel', () => { dragging = null; });
    doc.addEventListener('keydown', e => {
      const box = e.target.closest && e.target.closest('.udy-plot');
      if (!box || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
      e.preventDefault();
      const fig = box.closest('.udy'), tr = lookup(fig.dataset.udy), p = parts(fig);
      if (!tr || !p) return;
      const now = state.has(fig) ? state.get(fig) : p.t0, i = nearest(tr, now), stepSize = e.shiftKey ? 10 : 1;
      if (e.key === 'Home') return place(fig, p.t0);
      if (e.key === 'End') return place(fig, p.t1);
      const next = e.key === 'ArrowRight' ? Math.min(tr.t.length - 1, i + stepSize) : Math.max(0, i - stepSize);
      place(fig, tr.t[next]);
    });
    doc.addEventListener('click', e => {
      const button = e.target.closest && e.target.closest('[data-udy-view]');
      if (!button) return;
      const fig = button.closest('.udy'), tr = lookup(fig.dataset.udy);
      if (!tr) return;
      fig.dataset.view = button.dataset.udyView;
      const reveal = fig.dataset.reveal ? fig.dataset.reveal.split(' ') : [];
      fig.querySelector('.udy-plot').innerHTML = plot(tr, { lang: getLang(), view: button.dataset.udyView, reveal, layout: layoutFor() });
      const view = viewOf(tr, button.dataset.udyView, limitOf(tr, reveal)), box = fig.querySelector('.udy-plot');
      fig.querySelector('figcaption b').textContent = caption(tr, view, getLang());
      box.setAttribute('aria-valuemin', String(view.t0));
      box.setAttribute('aria-valuemax', String(view.t1));
      fig.querySelectorAll('[data-udy-view]').forEach(b => { b.classList.toggle('on', b === button); b.setAttribute('aria-pressed', String(b === button)); });
      fig.querySelector('.udy-readout').textContent = TEXT[lang(getLang())].start;
      state.delete(fig);
    });
  }

  root.NSAUrodynamics = { figure, plot, readout, nearest, bind, viewOf, limitOf, caption, ranges, TEXT, CHANNEL };
})(typeof window !== 'undefined' ? window : globalThis);
