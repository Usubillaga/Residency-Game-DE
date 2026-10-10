/* Original procedural character art reused from the user-supplied
 * classic/urology-night-shift.html (OL/st/shade/hair/head/figure/portrait).
 * Expanded room scenes and localized props for Night Shift Academy.
 * Cartoon expressions represent game feedback, never predicted patient outcomes.
 */
(function(root) {
  'use strict';
const OL = '#2a2442';
const st = (w = 3) => `stroke="${OL}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"`;

function shade(hex, pct) {
  const n = parseInt(hex.slice(1), 16);
  const f = pct / 100;
  const adj = c => Math.round(Math.max(0, Math.min(255, f < 0 ? c * (1 + f) : c + (255 - c) * f)));
  return '#' + [n >> 16, (n >> 8) & 255, n & 255].map(adj).map(x => x.toString(16).padStart(2, '0')).join('');
}

function hairBack(o) {
  const hc = o.hairColor;
  switch (o.hair) {
    case 'bob': return `<path d="M-46 30 Q-54 -54 0 -53 Q54 -54 46 30 Q41 38 31 33 L30 6 L-30 6 L-31 33 Q-41 38 -46 30Z" fill="${hc}" ${st()}/>`;
    case 'pony': return `<g transform="rotate(-16 40 0)"><ellipse cx="47" cy="16" rx="11" ry="27" fill="${hc}" ${st()}/><rect x="39" y="-9" width="15" height="7" rx="3" fill="#e2566b" ${st(2)}/></g>`;
    case 'bun': return `<circle cx="0" cy="-50" r="16" fill="${hc}" ${st()}/>`;
    case 'curly': return `<ellipse cx="0" cy="-6" rx="49" ry="47" fill="${hc}" ${st()}/>`;
    default: return '';
  }
}

const HAIR_FRONT = {
  short: 'M-40 0 Q-43 -47 0 -48 Q43 -47 40 0 Q37 -22 24 -28 Q12 -19 -2 -27 Q-16 -18 -29 -25 Q-37 -15 -40 0Z',
  messy: 'M-40 2 Q-46 -36 -24 -47 L-20 -60 L-8 -49 L2 -63 L10 -49 L24 -58 L25 -45 Q46 -36 40 2 Q37 -20 24 -27 Q10 -17 -4 -26 Q-18 -16 -30 -24 Q-38 -12 -40 2Z',
  bun: 'M-39 -2 Q-42 -46 0 -46 Q42 -46 39 -2 Q35 -29 0 -31 Q-35 -29 -39 -2Z',
  pony: 'M-39 -2 Q-42 -46 0 -46 Q42 -46 39 -2 Q33 -26 4 -30 Q-12 -22 -22 -28 Q-34 -22 -39 -2Z',
  bob: 'M-40 -2 Q-43 -48 0 -48 Q43 -48 40 -2 Q31 -25 4 -27 Q-6 -17 -18 -25 Q-31 -21 -40 -2Z',
  sidepart: 'M-40 -2 Q-45 -45 -6 -49 Q41 -49 40 -4 Q36 -26 16 -31 Q-2 -31 -16 -24 Q-30 -19 -36 -10Z',
  crew: 'M-39 -8 Q-40 -45 0 -46 Q40 -45 39 -8 Q36 -30 0 -31 Q-36 -30 -39 -8Z',
  bald: 'M-40 4 Q-46 -16 -34 -26 Q-30 -12 -37 10Z M40 4 Q46 -16 34 -26 Q30 -12 37 10Z'
};

function hairFront(o) {
  const hc = o.hairColor;
  if (o.hair === 'curly') {
    let s = `<ellipse cx="0" cy="-31" rx="33" ry="14" fill="${hc}"/>`;
    for (let i = 0; i < 9; i++) {
      const a = Math.PI * (1.08 + i * 0.105);
      s += `<circle cx="${(40 * Math.cos(a)).toFixed(1)}" cy="${(-4 + 42 * Math.sin(a)).toFixed(1)}" r="12.5" fill="${hc}" ${st(2.5)}/>`;
    }
    return s;
  }
  let s = `<path d="${HAIR_FRONT[o.hair] || HAIR_FRONT.short}" fill="${hc}" ${st()}/>`;
  if (o.hair === 'sidepart') s += `<path d="M-6 -48 Q-12 -36 -16 -25" stroke="${shade(hc, -30)}" stroke-width="2.5" fill="none"/>`;
  if (o.hair === 'bald') s += `<ellipse cx="-12" cy="-30" rx="10" ry="5" fill="#fff" opacity=".45" transform="rotate(-20 -12 -30)"/>`;
  return s;
}

function eyesSVG(expr) {
  const e = x => `<ellipse cx="${x}" cy="1" rx="4.6" ry="6" fill="${OL}"/><circle cx="${x + 1.7}" cy="-1.4" r="1.7" fill="#fff"/>`;
  switch (expr) {
    case 'pain': return `<path d="M-21 -4 L-10 1 L-21 6 M21 -4 L10 1 L21 6" fill="none" ${st(3)}/>`;
    case 'relieved': case 'happy': return `<path d="M-20 3 Q-14.5 -5 -9 3 M9 3 Q14.5 -5 20 3" fill="none" ${st(3)}/>`;
    case 'sleepy': return `<path d="M-20 2 Q-14.5 6 -9 2 M9 2 Q14.5 6 20 2" fill="none" ${st(3)}/>`;
    case 'scared': return `<ellipse cx="-14" cy="0" rx="7.5" ry="8.5" fill="#fff" ${st(2.5)}/><ellipse cx="14" cy="0" rx="7.5" ry="8.5" fill="#fff" ${st(2.5)}/><circle cx="-14" cy="1" r="2.6" fill="${OL}"/><circle cx="14" cy="1" r="2.6" fill="${OL}"/>`;
    default: return e(-14) + e(14);
  }
}

function browsSVG(expr, o) {
  const c = o.browColor || (o.hair === 'bald' ? '#9a9098' : shade(o.hairColor || '#444444', -35));
  const w = o.bushy ? 5.5 : 3.4;
  const D = {
    neutral: ['M-21 -15 Q-14 -19 -8 -16', 'M21 -15 Q14 -19 8 -16'],
    worried: ['M-22 -13 Q-15 -16 -8 -21', 'M22 -13 Q15 -16 8 -21'],
    stern: ['M-22 -20 Q-15 -17 -8 -13', 'M22 -20 Q15 -17 8 -13'],
    flat: ['M-21 -15 L-8 -15', 'M21 -15 L8 -15']
  };
  const map = { pain: 'worried', scared: 'worried', ill: 'worried', worried: 'worried', stern: 'stern', sleepy: 'flat' };
  const [L, R] = D[map[expr] || 'neutral'];
  return `<path d="${L}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="round"/><path d="${R}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="round"/>`;
}

function mouthSVG(expr) {
  const M = {
    smile: `<path d="M-12 17 Q0 31 12 17 Q0 21 -12 17Z" fill="#8c3a46" ${st(2.5)}/>`,
    relieved: `<path d="M-9 19 Q0 27 9 19" fill="none" ${st(3)}/>`,
    pain: `<rect x="-12" y="15" width="24" height="11" rx="4" fill="#fff" ${st(2.5)}/><path d="M-12 20.5 H12" stroke="${OL}" stroke-width="1.6"/>`,
    worried: `<path d="M-10 23 Q-5 19 0 23 Q5 27 10 23" fill="none" ${st(3)}/>`,
    scared: `<ellipse cx="0" cy="22" rx="5" ry="6.5" fill="#8c3a46" ${st(2.5)}/>`,
    sleepy: `<ellipse cx="3" cy="22" rx="4.5" ry="3.5" fill="#8c3a46" ${st(2.2)}/>`,
    stern: `<path d="M-9 22 H9" ${st(3)}/>`,
    neutral: `<path d="M-9 19 Q0 25 9 19" fill="none" ${st(3)}/>`
  };
  M.happy = M.smile; M.ill = M.worried;
  return M[expr] || M.neutral;
}

function head(o, expr = 'neutral') {
  const skin = o.skin;
  const rx = o.heavy ? 41 : 38;
  let s = hairBack(o);
  s += `<ellipse cx="-${rx}" cy="4" rx="7.5" ry="10" fill="${skin}" ${st()}/><ellipse cx="${rx}" cy="4" rx="7.5" ry="10" fill="${skin}" ${st()}/>`;
  s += `<ellipse cx="0" cy="0" rx="${rx}" ry="41" fill="${skin}" ${st()}/>`;
  if (o.stubble) s += `<path d="M-34 12 Q-29 39 0 41 Q29 39 34 12 Q23 29 0 29 Q-23 29 -34 12Z" fill="${OL}" opacity=".14"/>`;
  if (o.beard) s += `<path d="M-37 2 Q-37 46 0 47 Q37 46 37 2 Q30 21 18 25 Q8 19 0 20 Q-8 19 -18 25 Q-30 21 -37 2Z" fill="${o.hairColor}" ${st(2.5)}/>`;
  if (o.wrinkles) s += `<path d="M-13 -27 Q0 -31 13 -27 M-9 -22 Q0 -25 9 -22" fill="none" stroke="${OL}" stroke-width="1.6" opacity=".4"/>`;
  s += hairFront(o);
  if (expr === 'ill') s += `<ellipse cx="-22" cy="12" rx="8" ry="5" fill="#ff4d4d" opacity=".42"/><ellipse cx="22" cy="12" rx="8" ry="5" fill="#ff4d4d" opacity=".42"/>`;
  else if (['smile', 'happy', 'relieved', 'scared'].includes(expr) || o.blush) s += `<ellipse cx="-22" cy="13" rx="7" ry="4.2" fill="#ff7f8a" opacity=".35"/><ellipse cx="22" cy="13" rx="7" ry="4.2" fill="#ff7f8a" opacity=".35"/>`;
  if (o.freckles) s += `<g fill="#b9734e" opacity=".55"><circle cx="-24" cy="9" r="1.3"/><circle cx="-19" cy="12" r="1.3"/><circle cx="-26" cy="14" r="1.3"/><circle cx="24" cy="9" r="1.3"/><circle cx="19" cy="12" r="1.3"/><circle cx="26" cy="14" r="1.3"/></g>`;
  s += eyesSVG(expr);
  if (expr === 'ill') s += `<path d="M-20 -6 h12 v5.5 h-12Z M8 -6 h12 v5.5 h-12Z" fill="${skin}"/><path d="M-20 -0.5 h12 M8 -0.5 h12" ${st(2.5)}/>`;
  s += browsSVG(expr, o);
  s += `<ellipse cx="0" cy="9" rx="4.2" ry="3.2" fill="${shade(skin, -16)}"/>`;
  s += mouthSVG(expr);
  if (o.mustache) s += `<path d="M-15 16 Q-8 9 0 14 Q8 9 15 16 Q8 20 0 17 Q-8 20 -15 16Z" fill="${o.hairColor}" ${st(2)}/>`;
  if (expr === 'pain' || expr === 'ill') s += `<path d="M31 -24 q7 10 0 14 q-7 -4 0 -14Z" fill="#9edcff" ${st(1.8)}/>`;
  if (expr === 'sleepy') s += `<text x="33" y="-30" class="zzz">z</text><text x="44" y="-44" class="zzz" style="font-size:12px">z</text>`;
  if (o.glasses) s += `<g fill="rgba(255,255,255,.18)" ${st(2.6)}><circle cx="-14" cy="1" r="10.5"/><circle cx="14" cy="1" r="10.5"/></g><path d="M-3.5 0 Q0 -3 3.5 0 M-24.5 -1 L-${rx - 1} -4 M24.5 -1 L${rx - 1} -4" fill="none" ${st(2.6)}/>`;
  return s;
}

function figure(o, expr = 'neutral') {
  const top = o.top || '#8ec5e8';
  const coat = o.outfit === 'coat' || o.outfit === 'coatsuit';
  const pants = o.pants || (o.outfit === 'coatsuit' ? '#535866' : o.outfit === 'cardigan' ? '#3d4a6e' : shade(top, -8));
  const shoe = o.shoe || (o.outfit === 'cardigan' || o.outfit === 'coatsuit' ? '#2f2c3a' : '#f4f6fb');
  let s = `<ellipse cx="0" cy="0" rx="40" ry="8" fill="#000" opacity=".2"/><g class="body">`;
  s += `<g class="legL"><rect x="-21" y="-64" width="17" height="60" rx="7" fill="${pants}" ${st()}/><ellipse cx="-14" cy="-5" rx="14" ry="7" fill="${shoe}" ${st()}/></g>`;
  s += `<g class="legR"><rect x="4" y="-64" width="17" height="60" rx="7" fill="${pants}" ${st()}/><ellipse cx="14" cy="-5" rx="14" ry="7" fill="${shoe}" ${st()}/></g>`;
  s += `<rect x="-9" y="-128" width="18" height="18" fill="${o.skin}" ${st()}/>`;
  const torso = o.outfit === 'coatsuit' ? '#8b919e' : top;
  s += `<path d="M-34 -116 Q-41 -112 -41 -100 L-37 -56 Q-37 -50 -31 -50 L31 -50 Q37 -50 37 -56 L41 -100 Q41 -112 34 -116 Q18 -120 0 -108 Q-18 -120 -34 -116Z" fill="${torso}" ${st()}/>`;
  if (o.outfit === 'coatsuit') s += `<path d="M-10 -116 L0 -98 L10 -116Z" fill="#fff" ${st(2)}/>`;
  if (o.outfit === 'cardigan') s += `<path d="M-34 -116 L-20 -50 M34 -116 L20 -50" stroke="${shade(top, -25)}" stroke-width="3"/>`;
  if (coat) {
    s += `<path d="M-37 -116 Q-47 -110 -46 -96 L-43 -32 Q-43 -26 -37 -26 L-7 -26 L-4 -100 L-12 -117Z" fill="#fbfcff" ${st()}/>`;
    s += `<path d="M37 -116 Q47 -110 46 -96 L43 -32 Q43 -26 37 -26 L7 -26 L4 -100 L12 -117Z" fill="#fbfcff" ${st()}/>`;
    s += `<path d="M-12 -117 L-4 -100 L-15 -95Z M12 -117 L4 -100 L15 -95Z" fill="#e4e9f4" ${st(2)}/>`;
    s += `<path d="M-38 -62 h17 v12 h-17Z" fill="none" ${st(2)}/>`;
  }
  const sleeve = coat ? '#fbfcff' : top;
  if (coat || o.outfit === 'cardigan') {
    s += `<rect x="-56" y="-112" width="17" height="58" rx="8" fill="${sleeve}" ${st()}/><rect x="39" y="-112" width="17" height="58" rx="8" fill="${sleeve}" ${st()}/>`;
  } else {
    s += `<rect x="-55" y="-112" width="16" height="24" rx="7" fill="${sleeve}" ${st()}/><rect x="39" y="-112" width="16" height="24" rx="7" fill="${sleeve}" ${st()}/>`;
    s += `<rect x="-53" y="-92" width="12" height="38" rx="6" fill="${o.skin}" ${st()}/><rect x="41" y="-92" width="12" height="38" rx="6" fill="${o.skin}" ${st()}/>`;
  }
  s += `<circle cx="-47.5" cy="-52" r="8.5" fill="${o.skin}" ${st()}/><circle cx="47.5" cy="-52" r="8.5" fill="${o.skin}" ${st()}/>`;
  if (o.stetho) s += `<path d="M-13 -117 Q-24 -86 -9 -74 Q3 -68 8 -86" fill="none" stroke="#3a4157" stroke-width="3.5" stroke-linecap="round"/><circle cx="8" cy="-88" r="5.5" fill="#cfd6e6" ${st(2.5)}/>`;
  if (o.badge) s += `<rect x="17" y="-101" width="16" height="11" rx="2" fill="#fff" ${st(2)}/><rect x="17" y="-101" width="16" height="3.5" fill="${o.badge}"/>`;
  if (o.pens) s += `<rect x="13" y="-97" width="17" height="13" rx="2" fill="${shade(top, -14)}" ${st(2)}/><path d="M17 -97 v-7 M21.5 -97 v-8" stroke="#e5484d" stroke-width="3" stroke-linecap="round"/><path d="M26 -97 v-6" stroke="#3cc7c1" stroke-width="3" stroke-linecap="round"/>`;
  if (o.bowtie) s += `<path d="M-12 -121 L-1 -115 L-12 -109Z M12 -121 L1 -115 L12 -109Z" fill="#c0392b" ${st(2)}/><circle cx="0" cy="-115" r="3" fill="#a52f23" ${st(1.8)}/>`;
  if (o.dosimeter) s += dosimeter(-26, -92, 0.8);
  s += `<g transform="translate(0 -163)">${head(o, expr)}</g></g>`;
  return s;
}

// A film-badge dosimeter with the radiation trefoil: the radiation oncologist's mark.
function dosimeter(x, y, scale) {
  const blade = a => `<path d="M0 0 L${(9 * Math.cos(a)).toFixed(2)} ${(9 * Math.sin(a)).toFixed(2)} A9 9 0 0 1 ${(9 * Math.cos(a + 1.047)).toFixed(2)} ${(9 * Math.sin(a + 1.047)).toFixed(2)}Z" fill="${OL}"/>`;
  return `<g transform="translate(${x} ${y}) scale(${scale})"><rect x="-12" y="-12" width="24" height="24" rx="4" fill="#f2c94c" ${st(2.2)}/><g transform="scale(.95)">${[-1.571, 0.524, 2.618].map(a => blade(a - 0.524)).join('')}<circle r="3" fill="#f2c94c" ${st(1.4)}/></g></g>`;
}

let clipSeq = 0;
function portrait(o, expr = 'neutral', size = 96, opt = {}) {
  const id = 'pc' + (++clipSeq);
  const coat = o.outfit === 'coat' || o.outfit === 'coatsuit';
  const top = o.outfit === 'coatsuit' ? '#8b919e' : (o.top || '#8ec5e8');
  let body;
  if (o.gown) {
    body = `<path d="M-60 70 Q-58 34 -30 28 L30 28 Q58 34 60 70Z" fill="${o.gown}" ${st()}/><g fill="${shade(o.gown, -22)}"><circle cx="-34" cy="46" r="2.4"/><circle cx="-18" cy="54" r="2.4"/><circle cx="20" cy="50" r="2.4"/><circle cx="36" cy="58" r="2.4"/><circle cx="2" cy="62" r="2.4"/></g><path d="M-14 28 Q0 38 14 28" fill="none" ${st(2.5)}/>`;
  } else {
    body = `<path d="M-60 70 Q-58 34 -30 28 L30 28 Q58 34 60 70Z" fill="${coat ? '#fbfcff' : top}" ${st()}/>`;
    if (coat) body += `<path d="M-14 28 L0 60 L14 28Z" fill="${top}" ${st(2.5)}/>`;
    if (o.outfit === 'coatsuit') body += `<path d="M-8 28 L0 44 L8 28Z" fill="#fff" ${st(2)}/>`;
    if (!coat) body += `<path d="M-14 28 L0 42 L14 28" fill="none" ${st(2.5)}/>`;
    if (o.bowtie) body += `<path d="M-12 26 L-1 32 L-12 38Z M12 26 L1 32 L12 38Z" fill="#c0392b" ${st(2)}/><circle cx="0" cy="32" r="3" fill="#a52f23"/>`;
    if (o.stetho) body += `<path d="M-22 30 Q-26 52 -10 58 Q2 60 6 48" fill="none" stroke="#3a4157" stroke-width="3.5" stroke-linecap="round"/><circle cx="6" cy="46" r="5" fill="#cfd6e6" ${st(2.2)}/>`;
    if (o.pens) body += `<rect x="18" y="40" width="16" height="13" rx="2" fill="${shade(top, -14)}" ${st(2)}/><path d="M22 40 v-6 M27 40 v-7" stroke="#e5484d" stroke-width="3" stroke-linecap="round"/>`;
    if (o.dosimeter) body += dosimeter(26, 46, 1);
  }
  const neck = `<rect x="-9" y="16" width="18" height="16" fill="${o.skin}" ${st()}/>`;
  const phone = opt.phone ? `<g transform="translate(30 2) rotate(18)"><rect x="-7" y="-24" width="14" height="40" rx="6" fill="#2d3344" ${st(2.2)}/><circle cx="0" cy="18" r="9" fill="${o.skin}" ${st(2.5)}/></g>` : '';
  return `<svg viewBox="-64 -66 128 128" width="${size}" height="${size}" aria-hidden="true" focusable="false"><defs><clipPath id="${id}"><circle cx="0" cy="-2" r="62"/></clipPath></defs><circle cx="0" cy="-2" r="62" fill="${o.bg || '#2a355f'}"/><g clip-path="url(#${id})">${neck}${body}<g transform="translate(0 -14) scale(.92)">${head(o, expr)}</g>${phone}</g><circle cx="0" cy="-2" r="62" fill="none" stroke="${OL}" stroke-width="3"/></svg>`;
}


  const escape = value => String(value == null ? '' : value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const AVATARS = [
    {skin:'#f3cfae',hair:'short',hairColor:'#6b4226',top:'#8ec5e8',outfit:'coat',stetho:true,badge:'#3cc7c1',bg:'#2d6f8f'},
    {skin:'#c98e66',hair:'pony',hairColor:'#2b1d16',top:'#9fdcc8',outfit:'coat',stetho:true,badge:'#3cc7c1',bg:'#2f7a64'},
    {skin:'#7a4a2e',hair:'curly',hairColor:'#1d1512',top:'#c4b5f0',outfit:'coat',stetho:true,badge:'#3cc7c1',bg:'#5b4a9a'}
  ];
  const STAFF = {
    nurse:{skin:'#f4d2b5',hair:'bun',hairColor:'#e0b453',top:'#2f4f9e',outfit:'scrubs',pens:true,badge:'#e5484d',bg:'#3d5fb8'},
    attending:{skin:'#efc9a6',hair:'messy',hairColor:'#5b4a3c',glasses:true,stubble:true,top:'#5f7f9e',outfit:'coat',bg:'#6b5b95'},
    chief:{skin:'#f0caa8',hair:'sidepart',hairColor:'#d9dde6',browColor:'#c9ccd6',bushy:true,glasses:true,bowtie:true,outfit:'coatsuit',bg:'#9b3d3d'},
    radiotherapist:{skin:'#a8714f',hair:'bob',hairColor:'#2b1d16',top:'#2f8f86',outfit:'coat',dosimeter:true,bg:'#2d7f7a'}
  };
  const WORDS = {
    en:{areas:['Emergency','Ward','Clinic','Endoscopy','Theatre'],nurse:'Nurse',attending:'Attending',chief:'The chief',player:'You',coffee:'Coffee break',night:'UROLOGY · NIGHT SHIFT',room:'Conference room',stage:'Cartoon hospital: choose a department, a patient or the coffee machine',hero:'Your night team in a cartoon hospital, with a sleepy attending, a helpful nurse and a stern chief',welcome:'First night. Fresh scrubs. Very old coffee.',nurseLine:'Two hands. Five doors. We have got this.',chiefLine:'My question has three subquestions.',sleep:'ON CALL',paper:'PAPERWORK',waiting:'Not here yet',finished:'Case reviewed',available:'Open the chart',empty:'Quiet room. The pager disagrees.',routine:'Routine',urgent:'Urgent',critical:'Critical',station:'NURSING STATION',machine:'COFFEE'},
    de:{areas:['Notaufnahme','Station','Ambulanz','Endoskopie','OP-Saal'],nurse:'Pflege',attending:'Oberarzt',chief:'Der Chef',player:'Du',coffee:'Kaffeepause',night:'UROLOGIE · NACHTDIENST',stage:'Cartoon-Krankenhaus: Bereich, Patient oder Kaffeemaschine auswählen',hero:'Dein Nachtteam im Cartoon-Krankenhaus mit schläfrigem Oberarzt, hilfsbereiter Pflege und strengem Chef',welcome:'Erste Nacht. Frische Kittel. Sehr alter Kaffee.',nurseLine:'Zwei Hände. Fünf Türen. Das schaffen wir.',chiefLine:'Meine Frage hat drei Unterfragen.',sleep:'BEREITSCHAFT',room:'Konferenzraum',paper:'PAPIERKRAM',waiting:'Noch nicht da',finished:'Fall besprochen',available:'Akte öffnen',empty:'Ruhiger Raum. Der Pager sieht das anders.',routine:'Regulär',urgent:'Dringlich',critical:'Kritisch',station:'PFLEGESTÜTZPUNKT',machine:'KAFFEE'},
    es:{areas:['Urgencias','Planta','Consulta','Endoscopia','Quirófano'],nurse:'Enfermería',attending:'Adjunto',chief:'El jefe',player:'Tú',coffee:'Pausa para café',night:'UROLOGÍA · GUARDIA',room:'Sala de sesiones',stage:'Hospital de dibujos: elige un área, un paciente o la cafetera',hero:'Tu equipo nocturno en un hospital de dibujos, con un adjunto somnoliento, enfermería colaboradora y un jefe serio',welcome:'Primera noche. Pijama nuevo. Café muy viejo.',nurseLine:'Dos manos. Cinco puertas. Podemos hacerlo.',chiefLine:'Mi pregunta tiene tres subpreguntas.',sleep:'DE GUARDIA',paper:'PAPELEO',waiting:'Aún no ha llegado',finished:'Caso revisado',available:'Abrir historia',empty:'Sala tranquila. El busca no está de acuerdo.',routine:'Habitual',urgent:'Urgente',critical:'Crítico',station:'CONTROL DE ENFERMERÍA',machine:'CAFÉ'}
  };
  const AREAS = ['emergency','ward','clinic','endoscopy','theatre'];
  const lang = language => WORDS[language] || WORDS.en;
  const avatarIndex = index => ((Math.trunc(Number(index) || 0) % AVATARS.length) + AVATARS.length) % AVATARS.length;
  const expression = expr => ({good:'relieved',partial:'worried',unsafe:'scared'}[expr] || (['neutral','pain','relieved','happy','smile','sleepy','scared','stern','worried','ill'].includes(expr) ? expr : 'neutral'));
  const safeSize = size => Math.max(24, Math.min(320, Number(size) || 96));
  function hash(value) { let n=2166136261; for (const ch of String(value)) n=Math.imul(n^ch.charCodeAt(0),16777619); return n>>>0; }
  const CHILD_BANDS=['newborn','infant','child'],OLD_BANDS=['elderly'];
  function patientLook(id,hints) {
    // Appearance is a stable fictional design derived from the case ID, never from name or ethnicity.
    // Sex and age stated in the case text only rule out contradictions: no stubble on women or
    // children, no baldness in children, grey hair from 75 years.
    const n=hash(id),h=hints||{},age=Number.isInteger(h.age)?h.age:null;
    const child=age!==null?age<13:CHILD_BANDS.includes(h.ageBand),old=age!==null?age>=75:OLD_BANDS.includes(h.ageBand);
    const skin=['#f3cfae','#d6a27a','#c98e66','#b57b55','#8c5738','#7a4a2e'][n%6];
    const hairs=['short','messy','pony','bob','curly','bun','sidepart','bald'];
    return {skin,hair:child&&hairs[(n>>>4)%8]==='bald'?'messy':hairs[(n>>>4)%8],
      hairColor:old?['#d9dde6','#c3c8d3'][(n>>>8)%2]:['#6b4226','#2b1d16','#d9dde6','#e0b453','#7a3b2a','#443b53'][(n>>>8)%6],
      glasses:!!(n&256),freckles:!!(n&512),stubble:!!(n&1024)&&h.sex!=='female'&&!child,heavy:!!(n&2048)&&!child,
      gown:['#bcd6ef','#c4b5f0','#9fdcc8','#f2c879'][(n>>>12)%4],
      top:'#bcd6ef',outfit:'scrubs',bg:['#4d7599','#6b5b95','#3f7d70','#8f6748'][(n>>>16)%4]};
  }
  function portraitRole(role,expr='neutral',size=96,index=0) {
    const aliases={jana:'nurse',brenner:'attending',chef:'chief'};
    const look=STAFF[aliases[role]||role]||AVATARS[avatarIndex(index)];
    return portrait(look,expression(expr),safeSize(size),{phone:role==='attending'||role==='radiotherapist'});
  }
  function patientPortrait(id,expr='neutral',size=96,hints) { return portrait(patientLook(id,hints),expression(expr),safeSize(size)); }
  function avatar(index,size=96) { return portrait(AVATARS[avatarIndex(index)],'smile',safeSize(size)); }
  function iconPaths(area) {
    if(area==='emergency') return '<path d="M20 5H34V20H49V34H34V49H20V34H5V20H20Z" fill="#e65f68" '+st(3)+'/>';
    if(area==='ward') return '<rect x="5" y="25" width="44" height="12" rx="3" fill="#9acfe8" '+st(3)+'/><path d="M7 18V46M47 24V46" '+st(3)+'/><rect x="9" y="20" width="13" height="8" rx="3" fill="#fff" '+st(2)+'/><path d="M24 24H46" '+st(3)+'/>';
    if(area==='clinic') return '<rect x="14" y="7" width="29" height="40" rx="4" fill="#fff4d6" '+st(3)+'/><rect x="21" y="3" width="15" height="8" rx="3" fill="#c4b5f0" '+st(3)+'/><path d="M21 22H36M21 30H36M21 38H31" '+st(3)+'/>';
    if(area==='endoscopy') return '<rect x="4" y="5" width="42" height="31" rx="5" fill="#29334e" '+st(3)+'/><circle cx="25" cy="20" r="10" fill="#bd79b8" '+st(2)+'/><path d="M22 16Q32 14 28 25M25 36V46M14 47H36" fill="none" '+st(3)+'/>';
    return '<path d="M7 8H45L40 21H12Z" fill="#fff4d6" '+st(3)+'/><path d="M26 0V8M13 29H43M9 38H47M12 38V49M44 38V49" '+st(3)+'/><path d="M19 26Q28 20 39 29L41 37H14Z" fill="#66ba91" '+st(3)+'/>';
  }
  function areaIcon(area) {return '<svg viewBox="0 0 54 54" width="42" height="42" aria-hidden="true" focusable="false">'+iconPaths(area)+'</svg>';}
  function text(x,y,words,size=20,fill=OL,anchor='start',extra='') {
    return '<text x="'+x+'" y="'+y+'" text-anchor="'+anchor+'" fill="'+fill+'" font-size="'+size+'" '+extra+'>'+escape(words)+'</text>';
  }
  function boardLabel(label) {
    // Long duty labels are squeezed to the whiteboard width instead of running past its edge.
    return text(367,126,label,13,OL,'middle',String(label).length>20?'textLength="184" lengthAdjust="spacingAndGlyphs"':'');
  }
  function wrappedWords(value,max) {
    const result=[]; let row='';
    for (const word of String(value).split(/\s+/)) {
      if(row && (row+' '+word).length>max){result.push(row);row=word;}else row+=(row?' ':'')+word;
    }
    if(row)result.push(row); return result;
  }
  function bubble(x,y,width,words,fontSize=20) {
    const lines=wrappedWords(words,Math.floor(width/(fontSize*.54))-3);
    const h=lines.length*(fontSize+6)+24;
    return '<g class="cartoon-bubble" transform="translate('+x+' '+y+')"><path d="M32 '+(h-4)+'L28 '+(h+24)+'L60 '+(h-4)+'" fill="#fff9e8" '+st(4)+'/><rect width="'+width+'" height="'+h+'" rx="18" fill="#fff9e8" '+st(4)+'/>'+lines.map((row,i)=>text(17,28+i*(fontSize+6),row,fontSize)).join('')+'</g>';
  }
  function nightWindow(x,y,width,height) {
    return '<g transform="translate('+x+' '+y+')"><rect width="'+width+'" height="'+height+'" rx="12" fill="#14204a" '+st(4)+'/>'+
      '<circle cx="'+(width-37)+'" cy="32" r="17" fill="#fff2b6"/><circle cx="'+(width-28)+'" cy="25" r="15" fill="#14204a"/>'+
      [0,1,2,3,4,5].map(i=>'<circle cx="'+(15+(i*39)%(width-20))+'" cy="'+(14+(i*23)%(height-20))+'" r="2" fill="#f5eddb"/>').join('')+
      '<path d="M'+(width/2)+' 0V'+height+'M0 '+(height/2)+'H'+width+'" stroke="#edf2f8" stroke-width="5"/><rect width="'+width+'" height="'+height+'" rx="12" fill="none" '+st(4)+'/></g>';
  }
  function dayWindow(x,y,width,height) {
    return '<g transform="translate('+x+' '+y+')"><rect width="'+width+'" height="'+height+'" rx="12" fill="#a8daf2" '+st(4)+'/>'+
      '<circle cx="'+(width-36)+'" cy="33" r="17" fill="#ffd25e" '+st(2)+'/>'+
      '<path d="M16 '+(height-30)+'q10-15 26-6q10-13 26-2q15-1 13 13H14q-7-1 2-5Z" fill="#fff" '+st(2)+'/>'+
      '<path d="M'+(width/2)+' 0V'+height+'M0 '+(height/2)+'H'+width+'" stroke="#edf2f8" stroke-width="5"/><rect width="'+width+'" height="'+height+'" rx="12" fill="none" '+st(4)+'/></g>';
  }
  function boardScreen() {
    // The tumour board's projector: a cartoon cross-section, never a real image.
    return '<g transform="translate(560 30)"><rect width="560" height="170" rx="12" fill="#283249" '+st(4)+'/><rect x="14" y="12" width="532" height="136" rx="8" fill="#3f4e72"/>'+
      '<ellipse cx="150" cy="80" rx="88" ry="56" fill="#9aa6bf" '+st(3)+'/><ellipse cx="112" cy="84" rx="22" ry="30" fill="#cfd6e4" '+st(2)+'/><ellipse cx="188" cy="84" rx="22" ry="30" fill="#cfd6e4" '+st(2)+'/>'+
      '<circle cx="196" cy="72" r="9" fill="#e9a04f" '+st(2)+'/><path d="M196 72L262 34" stroke="#ffcf5a" stroke-width="4"/>'+
      '<path d="M300 46H500M300 76H470M300 106H486" stroke="#9fb0cf" stroke-width="9" stroke-linecap="round"/><path d="M300 136H420" stroke="#ffcf5a" stroke-width="9" stroke-linecap="round"/>'+
      '<path d="M120 0V-30M440 0V-30" '+st(4)+'/></g>';
  }
  function boardFolder(p,x,width,area,selectedId,language) {
    const w=lang(language), look=patientLook(p.id,p), available=p.available!==false, selected=p.id===selectedId||p.selected;
    const expr=p.finished?'neutral':p.feedback?expression(p.feedback):p.acuity==='critical'?'ill':p.acuity==='urgent'?'worried':'neutral';
    const fill=p.acuity==='critical'?'#d35468':p.acuity==='urgent'?'#e9a04f':'#57b997';
    const name=String(p.name||p.id),label=name+(p.age===null||p.age===undefined?'':' · '+p.age)+' · '+w[p.finished?'finished':available?'available':'waiting'];
    return '<g class="scene-hit scene-patient '+(selected?'selected ':'')+(available?'':'future')+'" transform="translate('+x+' 0)" role="button" tabindex="'+(available?0:-1)+'" aria-disabled="'+(!available)+'" aria-label="'+escape(label)+'" aria-pressed="'+!!selected+'" data-scene-patient="'+escape(p.id)+'"><title>'+escape(label)+'</title>'+
      '<rect x="4" y="195" width="'+(width-8)+'" height="226" rx="15" fill="#fff9e8" fill-opacity="'+(selected?'.60':'.22')+'" stroke="'+(selected?'#b58228':'#66748f')+'" stroke-width="'+(selected?'4':'2')+'"/>'+
      '<rect x="16" y="199" width="'+(width-32)+'" height="25" rx="8" fill="'+fill+'" '+st(2)+'/>'+text(width/2,218,p.finished?'✓ '+w.finished:w[p.acuity]||w.routine,14,'#231e36','middle','font-weight="800"')+
      '<rect x="18" y="244" width="'+Math.min(58,(width-36)/2)+'" height="16" rx="5" fill="'+look.gown+'" '+st(3)+'/><rect x="16" y="254" width="'+(width-32)+'" height="96" rx="8" fill="'+look.gown+'" '+st(3)+'/>'+
      '<rect x="26" y="264" width="'+(width-52)+'" height="78" rx="6" fill="#fff9e8" '+st(2)+'/><path d="M'+(width-66)+' 282H'+(width-36)+'M'+(width-66)+' 296H'+(width-42)+'M'+(width-66)+' 310H'+(width-48)+'" stroke="#b2a181" stroke-width="3"/>'+
      '<g transform="translate('+Math.round(width/2-18)+' 306) scale(.5)">'+head(look,expr)+'</g>'+
      text(width/2,403,name.length>21?name.slice(0,20)+'…':name,16,OL,'middle','font-weight="800"')+
      '<rect class="scene-focus" x="2" y="193" width="'+(width-4)+'" height="230" rx="17" fill="none" stroke="#ffcf5a" stroke-width="5" stroke-dasharray="9 6"/></g>';
  }
  function clockFace(x,y,value,radius=27) {
    const parts=String(value).split(':').map(Number);
    const hour=Number.isFinite(parts[0])?parts[0]:22, minute=Number.isFinite(parts[1])?parts[1]:0;
    let marks='';
    for(let i=0;i<12;i++) marks+='<path d="M0 '+(-radius+5)+'V'+(-radius+9)+'" transform="rotate('+(i*30)+')" '+st(2)+'/>';
    return '<g transform="translate('+x+' '+y+')"><circle r="'+radius+'" fill="#fff9e8" '+st(4)+'>'+ '</circle>'+marks+
      '<path d="M0 0V'+(-radius*.48)+'" transform="rotate('+((hour%12)*30+minute*.5)+')" '+st(4)+'/>'+
      '<path d="M0 0V'+(-radius*.70)+'" transform="rotate('+(minute*6)+')" '+st(3)+'/><circle r="3" fill="'+OL+'"/></g>';
  }
  function coffeeMachine(x,y,language,interactive=true,scale=1) {
    const w=lang(language);
    return '<g transform="translate('+x+' '+y+') scale('+scale+')"'+(interactive?' class="scene-hit coffee-machine" role="button" tabindex="0" data-scene-coffee="true" aria-label="'+escape(w.coffee)+'"':' class="coffee-machine"')+'>'+
      '<title>'+escape(w.coffee)+'</title><rect x="-6" y="-8" width="88" height="164" rx="12" fill="transparent"/>'+
      '<rect x="4" y="100" width="64" height="52" rx="5" fill="#b5c0d5" '+st(4)+'/>'+
      '<rect width="72" height="104" rx="10" fill="#493c58" '+st(4)+'/><rect x="10" y="12" width="52" height="17" rx="4" fill="#ffcf5a" '+st(2)+'/>'+
      text(36,25,w.machine,10,OL,'middle')+'<circle cx="55" cy="42" r="5" fill="#73e1ce" '+st(2)+'/>'+
      '<rect x="12" y="48" width="42" height="45" rx="4" fill="#201e36" '+st(2)+'/><path d="M33 47V58" stroke="#cbd2e1" stroke-width="5"/>'+
      '<rect x="22" y="71" width="26" height="21" rx="4" fill="#fff4d6" '+st(2.5)+'/><path d="M48 75q12 0 12 7q0 7-12 7" fill="none" '+st(2.5)+'/>'+
      '<g class="steam"><path d="M28 68q-6-9 0-17q6-7 0-16M40 68q6-9 0-17q-6-7 0-16" fill="none" stroke="#fff4d6" stroke-width="2.5" stroke-linecap="round"/></g>'+
      '<rect class="scene-focus" x="-6" y="-8" width="88" height="164" rx="12" fill="none" stroke="#ffcf5a" stroke-width="5" stroke-dasharray="9 6"/></g>';
  }
  function cup(x,y,scale=1) {
    return '<g transform="translate('+x+' '+y+') scale('+scale+')"><rect x="-12" y="-26" width="27" height="26" rx="5" fill="#fff4d6" '+st(3)+'/><path d="M15-22q15 0 15 11q0 11-15 11" fill="none" '+st(3)+'/><path d="M-4-32q-4-8 0-15M6-32q4-8 0-15" class="steam" fill="none" stroke="#fff4d6" stroke-width="3"/></g>';
  }
  function pager(x,y) {return '<g transform="translate('+x+' '+y+')" class="cartoon-pager"><rect x="-16" y="-12" width="36" height="24" rx="5" fill="#343047" '+st(3)+'/><rect x="-10" y="-7" width="24" height="9" rx="2" fill="#b9e2a1"/>'+text(2,0,'BEEP',6,OL,'middle')+'<path d="M-25-8l-9-7M29-8l9-7M-25 5h-12M29 5h12" stroke="#e8b64d" stroke-width="3" stroke-linecap="round"/></g>';}

  function hero(language='en') {
    const w=lang(language);
    return '<svg class="cartoon-hero" viewBox="0 0 1000 610" role="img" aria-label="'+escape(w.hero)+'" xmlns="http://www.w3.org/2000/svg">'+
      '<title>'+escape(w.hero)+'</title><rect x="3" y="3" width="994" height="604" rx="28" fill="#cde6de" '+st(6)+'/>'+
      '<path d="M3 463H997V580Q997 607 970 607H30Q3 607 3 580Z" fill="#8797b9" '+st(4)+'/>'+
      '<path d="M3 467H997M3 513H997M3 560H997M175 463L125 607M480 463L460 607M780 463L825 607" stroke="#aab7d0" stroke-width="3"/>'+
      nightWindow(25,30,140,157)+nightWindow(826,32,144,154)+
      '<rect x="186" y="25" width="613" height="49" rx="12" fill="#263456" '+st(4)+'/>'+text(490,57,w.night,25,'#fff4d6','middle','font-weight="800"')+
      '<path d="M302 176V454H474V176Z" fill="#9dccce" '+st(4)+'/><path d="M302 176H474" stroke="#6d93a7" stroke-width="7"/>'+
      '<path d="M321 184Q302 283 320 439M455 184Q474 283 455 439" fill="none" stroke="#557f95" stroke-width="5"/>'+
      '<rect x="326" y="193" width="123" height="29" rx="7" fill="#fff4d6" '+st(3)+'/>'+text(388,215,w.areas[0],17,OL,'middle')+
      '<rect x="559" y="171" width="177" height="286" rx="13" fill="#dfc4a1" '+st(4)+'/><rect x="580" y="201" width="135" height="38" rx="6" fill="#fff9e8" '+st(3)+'/>'+text(647,226,w.areas[1],18,OL,'middle')+
      '<circle cx="709" cy="336" r="6" fill="#ffcf5a" '+st(2)+'/>'+clockFace(776,114,'22:00',34)+
      '<rect x="82" y="355" width="94" height="112" rx="18" fill="#907caa" '+st(4)+'/><path d="M72 465V489M183 465V489" '+st(4)+'/>'+
      '<g transform="translate(135 484) scale(1.13)" class="cartoon-rest">'+figure(STAFF.attending,'sleepy')+'</g>'+
      coffeeMachine(25,241,language,false,1.08)+
      '<g transform="translate(362 502) scale(1.48)" class="cartoon-breathe">'+figure(AVATARS[0],'scared')+'</g>'+pager(431,399)+
      '<g transform="translate(569 502) scale(1.47)" class="cartoon-breathe">'+figure(STAFF.nurse,'smile')+'</g>'+cup(639,425,1.1)+
      '<g transform="translate(796 502) scale(1.45)">'+figure(STAFF.chief,'stern')+'</g>'+
      '<g transform="translate(865 330) rotate(8)"><rect width="72" height="103" rx="8" fill="#fff4d6" '+st(4)+'/><rect x="19" y="-6" width="34" height="15" rx="5" fill="#b49c77" '+st(3)+'/>'+text(36,29,w.paper,9,OL,'middle')+'<path d="M13 42H58M13 56H58M13 70H58M13 84H45" stroke="#8a7794" stroke-width="3"/></g>'+
      bubble(185,89,314,w.welcome,21)+bubble(461,160,294,w.nurseLine,20)+bubble(641,30,325,w.chiefLine,19)+
      text(135,544,w.attending,22,OL,'middle','font-weight="800"')+text(362,544,w.player,24,OL,'middle','font-weight="800"')+
      text(569,544,w.nurse,22,OL,'middle','font-weight="800"')+text(796,544,w.chief,22,OL,'middle','font-weight="800"')+
      '<rect x="53" y="565" width="895" height="29" rx="10" fill="#263456" '+st(2)+'/>'+text(502,586,w.night+' · 22:00',17,'#fff4d6','middle')+'</svg>';
  }
  function roomDoor(area,x,active,language) {
    const w=lang(language), label=w.areas[AREAS.indexOf(area)];
    const fill={emergency:'#e7b7b8',ward:'#b8c8e8',clinic:'#edd3a0',endoscopy:'#cfb4df',theatre:'#a9d3bf'}[area];
    return '<g class="scene-hit scene-door '+(active?'selected':'')+'" role="button" tabindex="0" data-scene-area="'+area+'" aria-label="'+escape(label)+'" aria-pressed="'+active+'" transform="translate('+x+' 33)">'+
      '<title>'+escape(label)+'</title><rect x="0" y="0" width="179" height="148" rx="13" fill="'+fill+'" '+st(4)+'/>'+
      '<rect x="14" y="14" width="151" height="36" rx="7" fill="#fff9e8" '+st(3)+'/>'+text(89,39,label,17,OL,'middle','font-weight="800"')+
      '<g transform="translate(63 62) scale(.95)">'+iconPaths(area)+'</g>'+
      '<circle cx="152" cy="117" r="6" fill="#ffcf5a" '+st(2.5)+'/>'+
      (active?'<path d="M58 142L89 126L120 142Z" fill="#ffcf5a" '+st(2.5)+'/>':'')+
      '<rect class="scene-focus" x="-5" y="-5" width="189" height="158" rx="17" fill="none" stroke="#ffcf5a" stroke-width="5" stroke-dasharray="10 7"/></g>';
  }
  function patientArea(patient) {
    if(AREAS.includes(patient.area))return patient.area;
    const fromCatalog=root.NSA_CATALOG && root.NSA_CATALOG.cases.find(c=>c.id===patient.id);
    if(fromCatalog)return fromCatalog.area;
    const prefix=String(patient.id).split('-')[0];
    return prefix==='ed'?'emergency':prefix;
  }
  function roomDecor(area,slots) {
    let s='';
    if(area==='emergency'||area==='ward'){
      s+='<path d="M495 187H1574" stroke="#71839e" stroke-width="6"/>';
      for(let i=0;i<=slots;i++){const x=494+i*178;s+='<path d="M'+x+' 190q-14 85 0 169v36h26v-36q12-84 0-169Z" fill="'+(area==='emergency'?'#86bfdc':'#b7a7d4')+'" '+st(3)+'/>';}
    }
    if(area==='clinic') s+='<g transform="translate(1534 270)"><path d="M-25 61H25L18 105H-18Z" fill="#dc9179" '+st(3)+'/><path d="M0 64V8" stroke="#4c865e" stroke-width="5"/><ellipse cx="-12" cy="24" rx="17" ry="8" fill="#78b88a" transform="rotate(35 -12 24)" '+st(2)+'/><ellipse cx="11" cy="12" rx="17" ry="8" fill="#78b88a" transform="rotate(-35 11 12)" '+st(2)+'/></g>';
    if(area==='endoscopy') s+='<g transform="translate(1450 204)"><rect width="116" height="75" rx="10" fill="#283249" '+st(4)+'/><rect x="9" y="9" width="98" height="55" rx="7" fill="#6e526f"/><circle cx="57" cy="35" r="23" fill="#bd79b8" '+st(2)+'/><path d="M43 27q27-15 24 13q-9 18-24-2" fill="#efb7c3" '+st(2)+'/><path d="M56 75V153M27 156H86" '+st(5)+'/></g>';
    if(area==='theatre') s+='<path d="M497 192H1580" stroke="#566c72" stroke-width="8"/><g transform="translate(960 202)"><path d="M0-14V4" '+st(5)+'/><ellipse rx="89" ry="20" fill="#fff4d6" '+st(4)+'/><g fill="#d8dbe0" '+st(2)+'><circle cx="-50" r="9"/><circle cx="-17" r="9"/><circle cx="17" r="9"/><circle cx="50" r="9"/></g><path d="M-58 16L-98 94H98L58 16Z" fill="#fff2b6" opacity=".22"/></g>';
    return s;
  }
  function bedside(p,x,width,area,selectedId,language) {
    const w=lang(language), look=patientLook(p.id,p), available=p.available!==false, selected=p.id===selectedId||p.selected;
    // These expressions communicate educational feedback, not recovery or severity predictions.
    const expr=p.finished?'neutral':p.feedback?expression(p.feedback):p.acuity==='critical'?'ill':p.acuity==='urgent'?'worried':'neutral';
    const fill=p.acuity==='critical'?'#d35468':p.acuity==='urgent'?'#e9a04f':'#57b997';
    const name=String(p.name||p.id),label=name+(p.age===null||p.age===undefined?'':' · '+p.age)+' · '+w[p.finished?'finished':available?'available':'waiting'];
    let s='<g class="scene-hit scene-patient '+(selected?'selected ':'')+(available?'':'future')+'" transform="translate('+x+' 0)" role="button" tabindex="'+(available?0:-1)+'" aria-disabled="'+(!available)+'" aria-label="'+escape(label)+'" aria-pressed="'+!!selected+'" data-scene-patient="'+escape(p.id)+'"><title>'+escape(label)+'</title>'+
      '<rect x="4" y="195" width="'+(width-8)+'" height="226" rx="15" fill="#fff9e8" fill-opacity="'+(selected?'.60':'.22')+'" stroke="'+(selected?'#b58228':'#66748f')+'" stroke-width="'+(selected?'4':'2')+'"/>'+
      '<rect x="16" y="199" width="'+(width-32)+'" height="25" rx="8" fill="'+fill+'" '+st(2)+'/>'+text(width/2,218,p.finished?'✓ '+w.finished:w[p.acuity]||w.routine,14,'#231e36','middle','font-weight="800"');
    if(area==='clinic'){
      s+='<rect x="16" y="317" width="64" height="56" rx="9" fill="#957eb5" '+st(3)+'/><path d="M18 373V391M74 373V391" '+st(3)+'/>'+
        '<g transform="translate(49 373) scale(.63)">'+figure({...look,top:look.gown},expr)+'</g>'+
        '<rect x="81" y="319" width="'+(width-100)+'" height="16" rx="5" fill="#d8c29d" '+st(3)+'/><path d="M88 335V381M'+(width-24)+' 335V381" '+st(4)+'/><path d="M95 316l29-5l7 7l-30 4Z" fill="#fff9e8" '+st(2)+'/>';
    }else{
      const blanket=area==='theatre'?'#69b99c':look.gown;
      s+='<path d="M26 341V377M'+(width-28)+' 341V377" stroke="#7c879e" stroke-width="6"/><circle cx="26" cy="383" r="7" fill="#3b4256" '+st(2)+'/><circle cx="'+(width-28)+'" cy="383" r="7" fill="#3b4256" '+st(2)+'/>'+
        '<rect x="15" y="321" width="'+(width-30)+'" height="18" rx="6" fill="#8e9ab2" '+st(3)+'/><rect x="15" y="297" width="'+(width-30)+'" height="27" rx="9" fill="#fff" '+st(3)+'/><ellipse cx="51" cy="299" rx="31" ry="10" fill="#eef3fb" '+st(2)+'/>'+
        '<path d="M63 287Q95 276 '+(width-24)+' 295V321H58Z" fill="'+blanket+'" '+st(3)+'/><path d="M70 294L'+(width-40)+' 314" stroke="'+shade(blanket,-18)+'" stroke-width="3"/>'+
        '<g transform="translate(52 274) scale(.72)">'+head(look,expr)+'</g>';
      if(area==='endoscopy')s+='<g transform="translate('+(width-57)+' 245)"><rect width="39" height="29" rx="5" fill="#283249" '+st(2)+'/><circle cx="19" cy="14" r="10" fill="#bd79b8"/><path d="M20 29V44" '+st(2)+'/></g>';
      else if(area!=='theatre')s+='<path d="M'+(width-24)+' 243V298" stroke="#8292a6" stroke-width="3"/><rect x="'+(width-33)+'" y="248" width="18" height="26" rx="5" fill="#cce9f6" '+st(2)+'/>';
    }
    s+=text(width/2,403,name.length>21?name.slice(0,20)+'…':name,16,OL,'middle','font-weight="800"')+
      '<rect class="scene-focus" x="2" y="193" width="'+(width-4)+'" height="230" rx="17" fill="none" stroke="#ffcf5a" stroke-width="5" stroke-dasharray="9 6"/></g>';
    return s;
  }
  function scene(area,patients,selectedId,time='22:00',index=0,language='en',options) {
    // Daytime duties get daylight and an awake attending; the tumour board meets in a conference room
    // where every case of the session lies on the table as a folder.
    const o=options||{},board=o.duty==='board',day=board||['clinic','elective','dayclinic','radiotherapy'].includes(o.duty);
    // In radiation oncology the radiation oncologist stands at the station instead of the attending.
    const consultant=o.duty==='radiotherapy'?STAFF.radiotherapist:STAFF.attending;
    if(!AREAS.includes(area))area='emergency';
    const w=lang(language);
    const list=(Array.isArray(patients)?patients:[]).filter(p=>board||patientArea(p)===area);
    let visible=list.slice(0,6);
    const selected=list.find(p=>p.id===selectedId);
    if(selected&&!visible.includes(selected))visible[visible.length-1]=selected;
    const color=board?'#e6dcc6':{emergency:'#cde6de',ward:'#dbd5e7',clinic:'#eadfbd',endoscopy:'#ddcce6',theatre:'#bcded0'}[area];
    let svg='<svg class="cartoon-room" viewBox="0 0 1600 440" role="group" aria-label="'+escape(w.stage)+'" xmlns="http://www.w3.org/2000/svg"><title>'+escape(w.stage)+'</title>'+
      '<rect width="1600" height="440" fill="'+color+'"/><rect y="385" width="1600" height="55" fill="#8c9ab7"/><path d="M0 389H1600M0 425H1600" stroke="#b3bfd4" stroke-width="3"/>'+
      '<rect width="1600" height="19" fill="#eef2f8"/><path d="M0 19H1600" stroke="#8e91a8" stroke-width="3"/>';
    for(let x=35;x<1580;x+=120)svg+='<path d="M'+x+' 390l-24 50" stroke="#a9b5ce" stroke-width="2"/>';
    svg+=(day?dayWindow(18,37,133,129):nightWindow(18,37,133,129))+clockFace(200,74,time,31)+text(200,128,time,23,OL,'middle','font-family="monospace" font-weight="800"')+
      '<rect x="259" y="33" width="216" height="53" rx="9" fill="#263456" '+st(3)+'/>'+text(367,66,board?w.room:w.areas[AREAS.indexOf(area)],22,'#fff4d6','middle','font-weight="800"')+
      '<rect x="266" y="103" width="201" height="75" rx="7" fill="#fff4d6" '+st(3)+'/>'+boardLabel(o.label||w.sleep)+
      '<path d="M282 140H452M282 153H439M282 166H412" stroke="#b2a181" stroke-width="3"/>'+
      (board?boardScreen()+'<rect x="488" y="343" width="1094" height="30" rx="12" fill="#b0845a" '+st(3)+'/><path d="M540 373V412M1530 373V412" '+st(6)+'/>':
        AREAS.map((id,i)=>roomDoor(id,505+i*214,id===area,language)).join('')+roomDecor(area,Math.max(visible.length,2)))+
      '<g transform="translate(177 410) scale(.90)" class="cartoon-breathe">'+figure(STAFF.nurse,visible.some(p=>p.feedback==='unsafe')?'stern':'smile')+'</g>'+
      '<g transform="translate(339 409) scale(.85)">'+figure(STAFF.chief,'stern')+'</g>'+
      '<g transform="translate(451 412) scale(.87)" class="cartoon-breathe">'+figure(AVATARS[avatarIndex(index)],visible.some(p=>p.feedback==='unsafe')?'scared':'neutral')+'</g>'+
      (day?'<g transform="translate(90 296) scale(.53)">'+figure(consultant,'smile')+'</g>':'<g transform="translate(90 296) scale(.53)" class="cartoon-rest">'+figure(STAFF.attending,'sleepy')+'</g>')+
      '<rect x="9" y="346" width="219" height="66" rx="7" fill="#d8c29d" '+st(3)+'/><rect x="5" y="334" width="227" height="17" rx="5" fill="#ecdcbd" '+st(3)+'/>'+text(118,379,w.station,14,OL,'middle','font-weight="800"')+
      '<rect x="88" y="296" width="61" height="36" rx="5" fill="#293249" '+st(3)+'/><rect x="95" y="302" width="47" height="24" rx="3" fill="#8cd6cc"/><path d="M119 332V337" '+st(3)+'/>'+
      coffeeMachine(239,302,language,true,.71)+pager(410,327)+
      text(337,434,w.chief,14,OL,'middle','font-weight="800"')+text(453,434,w.player,14,OL,'middle','font-weight="800"');
    if(visible.length){
      const width=Math.min(208,1055/Math.max(visible.length,4));
      svg+=visible.map((p,i)=>(board?boardFolder:bedside)(p,510+i*width,width,area,selectedId,language)).join('');
    }else svg+=bubble(669,263,570,w.empty,25);
    svg+='</svg>';
    return '<div class="cartoon-scene-wrap">'+svg+'</div>';
  }
  root.NSAArt={portrait:portraitRole,patientPortrait,avatar,hero,scene,areaIcon,avatarCount:AVATARS.length};
})(typeof window!=='undefined'?window:globalThis);
