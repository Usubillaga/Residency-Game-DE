(function() {
  'use strict';
  const C = window.NSA_CATALOG, E = window.NSAEngine, strings = window.NSA_TEXT;
  const root = document.getElementById('app');
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  if (!C || !E) { root.innerHTML='<main class="container page-head"><h1>Night Shift Academy</h1><p>'+esc(strings.en.dataError)+'</p></main>'; return; }
  const STORAGE='night-shift-academy-v2';
  // A downloaded game file can be loaded again to carry on, on this or another device.
  const SAVE_FORMAT='night-shift-academy-save',SAVE_LIMIT=5000000;
  const A=window.NSAArt;
  const comedy=()=>window.NSABanter[state.lang];
  const getCase = id=>C.cases.find(c=>c.id===id);
  const getArea = id=>C.areas.find(a=>a.id===id);
  // Stickers are derived from the logbook and a few game counters; the icons are language-neutral.
  const BADGE_ICONS={firstCase:'📋',firstShift:'🌅',streak5:'📟',streak10:'🚀',perfectShift:'📘',bossPerfect:'🎓',coffee5:'☕',allAreas:'🗺️',comeback:'🔁',joker10:'🤝',specialist:'🔬',cases50:'🦉',nightOwl:'🌙',anatomist:'🦴'};
  const STAT_KEYS=['shifts','perfectShifts','bossPerfect','maxCoffees','bestStreak','jokers','rank','atlasPerfect'];
  const RANK_COUNT=9; // the career ladder: RANK_XP below and careerRanks in banter.js have nine steps
  // The attending in the background takes three calls per shift; each costs five game minutes, never points.
  const ATTENDING_CALLS=3,CALL_MINUTES=5;
  // Duties decide which cases a session draws: emergencies at night, oncology decisions in the tumour board,
  // outpatient work in clinic and planned surgery on the elective list. Start times are game minutes after midnight.
  const DUTIES=['night','board','clinic','elective','dayclinic','radiotherapy'],DUTY_START={night:1320,board:930,clinic:480,elective:450,dayclinic:510,radiotherapy:495,mixed:1320};
  const DUTY_ICON={night:'🌙',board:'🎗️',clinic:'🩺',elective:'✂️',dayclinic:'💉',radiotherapy:'☢️',mixed:'🔀'};
  // Radiotherapy questions are answered by the radiation oncologist; every other case by the attending.
  const consultantOf=c=>c&&c.consultant==='radiotherapist'?'radiotherapist':'attending';
  const count=v=>Number.isInteger(v)&&v>=0?v:0;
  let storageFailed=false, state={lang:'en',name:'',avatar:0,sound:false,history:[],bookmarks:[],session:null,stats:cleanStats(null),badges:[],lastDuty:'night',countedShifts:[]};
  try {
    const s=JSON.parse(localStorage.getItem(STORAGE)||'null');
    if (s && typeof s==='object' && !Array.isArray(s)) Object.assign(state,cleanSave(s));
  } catch (_) { /* In-memory play stays available when browser storage is blocked. */ }
  let view=['intro','library','atlas','protocols','progress','sources','play','report'].includes(location.hash.slice(1))?location.hash.slice(1):'intro';
  let areaFilter='all',topicFilter='all',dutyFilter='all',pendingDuty='night',libraryPage=0,query='',savedOnly=false,pendingIds=null,customSchedule=null,dialogSequence=0,pendingSave=null,protocolEntity=null,protocolKind='systemic';
  const t = key => {const value=typeof comedy()[key]==='string'?comedy()[key]:(strings[state.lang][key] || strings.en[key] || key);return value.replaceAll('{cases}',String(C.cases.length)).replaceAll('{areas}',String(C.areas.length));};
  const loc = value => value[state.lang];
  const pct = r=>Math.round(r.score/r.maxScore*100);
  const nowSeed=()=>new Date().toLocaleDateString('sv-SE')+'-'+Date.now();
  const caseMaximum=c=>c.steps.reduce((n,s)=>n+Math.max(...s.options.map(o=>o.score)),0);
  // A case without any patient (e.g. a departmental meeting) carries a translated label instead of a name.
  const patientName=c=>c.patient.label?loc(c.patient.label):c.patient.name;
  const casePortrait=(c,expr,size)=>c.patient.label?A.portrait('chief','stern',size,state.avatar):A.patientPortrait(c.id,expr,size,c.patient);
  const patientLabel=c=>patientName(c)+(c.patient.age===null?'':' · '+c.patient.age);
  const clock=(min,duty=state.session?.duty)=>{const at=(DUTY_START[duty]??DUTY_START.night)+min;return String(Math.floor(at/60)%24).padStart(2,'0')+':'+String(at%60).padStart(2,'0');};
  const dutyOf=c=>DUTIES.includes(c.duty)?c.duty:({emergency:'night',ward:'night',clinic:'clinic',endoscopy:'elective',theatre:'elective'}[c.area]||'clinic');
  const dutyName=d=>DUTY_ICON[d]+' '+t('duty_'+d);
  // Only duties with cases are offered; saved sessions and filters still accept every known duty.
  const PLAYABLE=DUTIES.filter(d=>C.cases.some(c=>dutyOf(c)===d));
  const commonDuty=ids=>{const found=new Set(ids.map(id=>dutyOf(getCase(id))));return found.size===1?[...found][0]:'mixed';};
  function validRecord(r) {
    try {
      const c=getCase(r.caseId);
      if (!c || r.area!==c.area || !Array.isArray(r.answers) || r.answers.length!==c.steps.length || typeof r.completedAt!=='string' || !Number.isFinite(Date.parse(r.completedAt))) return false;
      let score=0,minutes=0,errors=0;
      for (let i=0;i<c.steps.length;i++) {
        const a=r.answers[i],s=c.steps[i],o=s.options.find(o=>o.id===a.optionId);
        if (!o || a.stepId!==s.id || a.score!==o.score || a.minutes!==o.minutes) return false;
        score+=o.score;minutes+=o.minutes;errors+=o.critical?1:0;
      }
      return r.score===score && r.elapsed===minutes && r.criticalErrors===errors && r.maxScore===c.steps.reduce((n,s)=>n+Math.max(...s.options.map(o=>o.score)),0);
    } catch(_){return false;}
  }
  function cleanStats(raw) {
    // Counters are capped: a hand-edited file cannot store absurd values or a rank beyond the ladder.
    const stats={};for(const key of STAT_KEYS)stats[key]=Math.min(count(raw&&raw[key]),key==='rank'?RANK_COUNT-1:1000000);
    return stats;
  }
  function cleanSession(s) {
    // Rebuilt from known fields only, so a saved shift cannot carry extra data into storage. Game-only extras never change
    // clinical points, answers or the logbook. Call only after E.validSession has accepted the shift.
    const patients=s.patients.map(p=>({id:p.id,index:p.index,answers:p.answers.map(a=>({stepId:a.stepId,optionId:a.optionId,score:a.score,minutes:a.minutes})),
      score:p.score,elapsed:p.elapsed,criticalErrors:p.criticalErrors,availableAt:p.availableAt,feedback:p.feedback||null,finished:p.finished,order:p.order.map(order=>[...order]),logged:p.logged===true}));
    const struck={};
    if(s.struck&&typeof s.struck==='object'&&!Array.isArray(s.struck))for(const [key,value] of Object.entries(s.struck)){
      const match=/^(.+):(\d+)$/.exec(key),patient=match&&patients.find(p=>p.id===match[1]),step=patient&&getCase(patient.id).steps[Number(match[2])];
      if(step&&typeof value==='string'&&step.options.some(o=>o.id===value))struck[key]=value;
    }
    const called={};
    if(s.called&&typeof s.called==='object'&&!Array.isArray(s.called))for(const key of Object.keys(s.called)){
      const match=/^(.+):(\d+)$/.exec(key),patient=match&&patients.find(p=>p.id===match[1]);
      if(patient&&Number(match[2])<getCase(patient.id).steps.length&&s.called[key]===true)called[key]=true;
    }
    const capped=v=>Math.min(count(v),1000000),streak=capped(s.streak);
    const clean={version:2,mode:s.mode,seed:s.seed.slice(0,120),clock:s.clock,patients,selected:s.selected,finished:s.finished,duty:DUTIES.includes(s.duty)?s.duty:'mixed',
      coffees:capped(s.coffees),streak,bestStreak:Math.max(capped(s.bestStreak),streak),jokers:capped(s.jokers),
      streakAt:typeof s.streakAt==='string'&&s.streakAt.length<=200?s.streakAt:null,struck,counted:s.counted===true,bossCounted:s.bossCounted===true,
      calls:Math.min(capped(s.calls),ATTENDING_CALLS),called};
    if(validBoss(s.boss))clean.boss={index:s.boss.index,done:s.boss.done,answers:[...s.boss.answers],items:s.boss.items.map(item=>({caseId:item.caseId,stepIndex:item.stepIndex,order:[...item.order]}))};
    return clean;
  }
  // Saved games are untrusted input, whether they come from this browser or from a file: only what passes the checks is kept.
  // Function declarations, not constants: the saved game is restored at start-up, before later constants exist.
  function cleanRecord(r) {
    return {caseId:r.caseId,area:r.area,score:r.score,maxScore:r.maxScore,elapsed:r.elapsed,criticalErrors:r.criticalErrors,completedAt:r.completedAt,
      answers:r.answers.map(a=>({stepId:a.stepId,optionId:a.optionId,score:a.score,minutes:a.minutes})),...(typeof r.shift==='string'&&r.shift.length<=120?{shift:r.shift}:{})};
  }
  // Any progress worth saving: a logbook entry, a shift, a sticker, a bookmark or a counter.
  function hasProgress(s) { return s.history.length>0||!!s.session||s.badges.length>0||s.bookmarks.length>0||STAT_KEYS.some(key=>s.stats[key]>0); }
  function cleanSave(s) {
    return {
      lang:['en','de','es'].includes(s.lang)?s.lang:'en',
      name:typeof s.name==='string'?Array.from(s.name).slice(0,32).join(''):'',
      avatar:Number.isInteger(s.avatar)&&s.avatar>=0&&s.avatar<3?s.avatar:0,
      sound:s.sound===true,
      bookmarks:Array.isArray(s.bookmarks)?[...new Set(s.bookmarks.filter(id=>typeof id==='string'&&C.cases.some(c=>c.id===id)))]:[],
      history:Array.isArray(s.history)?s.history.filter(validRecord).map(cleanRecord).slice(-1000):[],
      session:E.validSession(s.session,C)?cleanSession(s.session):null,
      stats:cleanStats(s.stats),
      badges:Array.isArray(s.badges)?[...new Set(s.badges.filter(id=>typeof id==='string'&&Object.prototype.hasOwnProperty.call(BADGE_ICONS,id)))]:[],
      lastDuty:DUTIES.includes(s.lastDuty)?s.lastDuty:'night',
      // Shifts and morning reports already counted, so an older copy of the same shift cannot count them again.
      countedShifts:Array.isArray(s.countedShifts)?[...new Set(s.countedShifts.filter(key=>typeof key==='string'&&key.length<=130))].slice(-300):[]
    };
  }
  // The game file holds everything needed to carry on; the interface language and sound stay as they are on the device.
  function saveFile() {
    return {format:SAVE_FORMAT,version:3,exportedAt:new Date().toISOString(),name:state.name,avatar:state.avatar,lastDuty:state.lastDuty,
      history:state.history,stats:state.stats,badges:state.badges,bookmarks:state.bookmarks,session:state.session,countedShifts:state.countedShifts};
  }
  // Reads a downloaded game file. Logbooks exported before version 3 held the history only and still load.
  function readSaveFile(data) {
    if (!data || typeof data!=='object' || Array.isArray(data)) return null;
    const full=data.format===SAVE_FORMAT&&data.version===3,logbook=!('format' in data)&&data.version===2&&Array.isArray(data.history);
    if (!full && !logbook) return null;
    const save=cleanSave(full?data:{history:data.history});
    if (full ? !hasProgress(save) : !save.history.length) return null;
    return {save,full,named:full&&save.name.trim()!=='',skipped:Array.isArray(data.history)?data.history.length-data.history.filter(validRecord).length:0,
      exportedAt:typeof data.exportedAt==='string'&&Number.isFinite(Date.parse(data.exportedAt))?data.exportedAt:null};
  }
  // Which shift continues after loading: the same shift is kept where it got further; otherwise an open shift wins over a finished one,
  // and the file's shift wins when both are open or both finished.
  const openShift=s=>!!s&&!s.finished;
  const shiftProgress=s=>(s.bossCounted?8e6:0)+(s.boss?(s.boss.done?4e6:0)+s.boss.answers.length:0)+(s.counted?2e6:0)+(s.finished?1e6:0)+
    s.patients.reduce((n,p)=>n+p.index*4+(p.feedback?2:0)+(p.logged?1:0),0);
  function chooseShift(current,incoming) {
    if (!incoming) return {session:current,outcome:'none'};
    if (current && current.seed===incoming.seed) return shiftProgress(incoming)>shiftProgress(current)?{session:incoming,outcome:'same'}:{session:current,outcome:'ahead'};
    if (openShift(current) && !openShift(incoming)) return {session:current,outcome:'kept'};
    return {session:incoming,outcome:openShift(current)?'replaces':'takes'};
  }
  // Loading never loses progress: both logbooks are combined (an attempt counts once), counters keep the higher value, stickers,
  // bookmarks and counted shifts are united, and the shift is chosen by chooseShift. The rank is recalculated from the logbook afterwards.
  function mergeSave(current,found) {
    const incoming=found.save,seen=new Set(),history=[];
    const records=[...current.history,...incoming.history].map((r,i)=>[r,i]).sort((a,b)=>Date.parse(a[0].completedAt)-Date.parse(b[0].completedAt)||a[1]-b[1]).map(([r])=>r);
    for (const r of records) {
      const key=r.shift?'shift|'+r.shift+'|'+r.caseId:r.caseId+'|'+r.completedAt+'|'+r.answers.map(a=>a.stepId+':'+a.optionId).join(',');
      if (!seen.has(key)) { seen.add(key); history.push(r); }
    }
    const stats={};for (const key of STAT_KEYS) stats[key]=key==='rank'?count(current.stats.rank):Math.max(count(current.stats[key]),count(incoming.stats[key]));
    const takeProfile=found.named||(found.full&&!current.name.trim());
    return {history:history.slice(-1000),stats,badges:[...new Set([...current.badges,...incoming.badges])],bookmarks:[...new Set([...current.bookmarks,...incoming.bookmarks])],
      session:chooseShift(current.session,incoming.session).session,name:found.named?incoming.name:current.name,avatar:takeProfile?incoming.avatar:current.avatar,
      lastDuty:found.full?incoming.lastDuty:current.lastDuty,countedShifts:[...new Set([...(current.countedShifts||[]),...incoming.countedShifts])].slice(-300)};
  }
  // Career XP counts each case once, at its best result: replaying improves XP, farming does not.
  const MAX_XP=C.cases.reduce((n,c)=>n+caseMaximum(c),0);
  const RANK_XP=[0,80,250,550,1000,1600,2300,3000,MAX_XP];
  function bestScores(history=state.history) {
    const best=new Map();for(const r of history)best.set(r.caseId,Math.max(best.has(r.caseId)?best.get(r.caseId):-1,r.score));
    return best;
  }
  function xp(history=state.history) { let n=0;for(const v of bestScores(history).values())n+=v;return n; }
  function rankIndex(points=xp()) { let rank=0;RANK_XP.forEach((need,i)=>{if(points>=need)rank=i;});return rank; }
  function rankName() { return comedy().careerRanks[rankIndex()]; }
  function earnedBadges() {
    const h=state.history,st=state.stats,best=bestScores(),domains=new Map(),low=new Set();
    for(const c of C.cases)if(c.source){if(!domains.has(c.source.domain))domains.set(c.source.domain,[]);domains.get(c.source.domain).push(c);}
    let comeback=false;
    for(const r of h){if(r.score<r.maxScore)low.add(r.caseId);else if(low.has(r.caseId))comeback=true;}
    const earned={
      firstCase:h.length>0,firstShift:st.shifts>0,streak5:st.bestStreak>=5,streak10:st.bestStreak>=10,perfectShift:st.perfectShifts>0,bossPerfect:st.bossPerfect>0,
      coffee5:st.maxCoffees>=5||count(state.session?.coffees)>=5,allAreas:C.areas.every(a=>h.some(r=>r.area===a.id)),comeback,joker10:st.jokers>=10,
      specialist:[...domains.values()].some(list=>list.every(c=>best.get(c.id)===caseMaximum(c))),cases50:best.size>=50,
      nightOwl:h.some(r=>new Date(r.completedAt).getHours()<5),anatomist:st.atlasPerfect>0
    };
    return Object.keys(BADGE_ICONS).filter(id=>earned[id]);
  }
  function syncRewards() {
    // Credit existing progress quietly, e.g. after an update or an import from an older version.
    state.badges=[...new Set([...state.badges,...earnedBadges()])];
    state.stats.rank=Math.max(state.stats.rank,rankIndex());
  }
  function checkRewards() {
    const fresh=earnedBadges().filter(id=>!state.badges.includes(id)),rank=rankIndex(),promoted=rank>state.stats.rank;
    if(!fresh.length&&!promoted)return;
    state.badges.push(...fresh);state.stats.rank=Math.max(rank,state.stats.rank);persist();
    if(promoted)showPromotion(rank,fresh);
    else toast('🏅 '+t('newSticker')+': '+fresh.map(id=>BADGE_ICONS[id]+' '+comedy().badges[id].title).join(' · '),'sticker');
  }
  function showPromotion(rank,fresh) {
    const line=quip('rankUp',String(rank)),role=speakerFor(line);
    const dlg=openDialog('<div class="story-dialogue promotion"><div class="story-portrait">'+A.avatar(state.avatar,156)+'</div><div class="story-bubble"><p class="eyebrow">'+esc(t('rankUpTitle'))+'</p><h2>'+esc(comedy().careerRanks[rank])+'</h2><p class="career-joke">'+esc(comedy().careerJokes[rank])+'</p><p><b>'+esc(comedy().staff[role].name)+':</b> '+esc(lineWithoutName(line,role))+'</p>'+(fresh.length?'<p class="promotion-stickers">🏅 '+esc(t('newSticker'))+': '+fresh.map(id=>BADGE_ICONS[id]+' '+esc(comedy().badges[id].title)).join(' · ')+'</p>':'')+'<button class="btn primary" data-action="close-dialog">'+esc(t('dialogNext'))+' ▶</button></div></div>');
    dlg.classList.add('story-modal');celebrate(true);sound('good');
  }
  function celebrate(big) {
    try{if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;}catch(_){return;}
    const box=document.createElement('div'),colors=['#ffcf5a','#91dfcd','#c4b5f0','#ffa0aa','#fff4d6','#7fb4ff'];
    box.className='confetti';box.setAttribute('aria-hidden','true');
    for(let i=0;i<(big?90:30);i++){
      const piece=document.createElement('i');
      piece.style.left=(Math.random()*100)+'%';piece.style.background=colors[i%colors.length];
      piece.style.animationDelay=(Math.random()*.3)+'s';piece.style.animationDuration=(1.2+Math.random()*1.1)+'s';
      piece.style.setProperty('--drift',Math.round(Math.random()*180-90)+'px');piece.style.setProperty('--spin',Math.round(Math.random()*900-450)+'deg');
      box.append(piece);
    }
    (document.querySelector('dialog[open]')||document.body).append(box);setTimeout(()=>box.remove(),2700);
  }
  const isMilestone=n=>n===3||n===5||n%5===0&&n>0;
  function afterAnswer(choice) {
    const s=state.session,p=s.patients.find(p=>p.id===s.selected);
    s.streak=choice.score===10?s.streak+1:0;s.bestStreak=Math.max(s.bestStreak,s.streak);
    const milestone=choice.score===10&&isMilestone(s.streak);
    s.streakAt=milestone?p.id+':'+(p.index):null;
    state.stats.bestStreak=Math.max(state.stats.bestStreak,s.streak);
    return milestone;
  }
  function answerEffects(choice,milestone) {
    if(choice.score===10){celebrate(milestone);return;}
    const wrong=document.querySelector('.chart .option.wrong,.chart .option.meh');
    wrong?.classList.add('shake');splash(wrong);
  }
  function splash(target) {
    // A wrong answer gets a cartoon urine splash: droplets, a puddle and a "Splash!" — pure slapstick.
    try{if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;}catch(_){return;}
    const r=target&&target.getBoundingClientRect?target.getBoundingClientRect():{left:window.innerWidth/2-60,top:window.innerHeight/2,width:120,height:40};
    const box=document.createElement('div');box.className='splash';box.setAttribute('aria-hidden','true');
    // The punchline spans 60 px left to 180 px right of the anchor; keep it on screen on phones.
    const x=Math.min(Math.max(r.left+r.width*.8,70),Math.max(70,window.innerWidth-190));
    box.style.left=Math.round(x)+'px';box.style.top=Math.round(r.top+r.height/2)+'px';
    let drops='';
    for(let i=0;i<18;i++){
      const angle=(-170+i*(160/17)+(Math.random()*12-6))*Math.PI/180,dist=45+Math.random()*80;
      drops+='<i class="drop" style="--dx:'+Math.round(Math.cos(angle)*dist)+'px;--dy:'+Math.round(Math.sin(angle)*dist)+'px;--s:'+(.55+Math.random()*.7).toFixed(2)+';--r:'+Math.round(angle*180/Math.PI+90)+'deg;animation-delay:'+(Math.random()*.08).toFixed(2)+'s"></i>';
    }
    const words=comedy().splash||['Splash!'];
    box.innerHTML='<i class="puddle"></i>'+drops+'<b class="splash-word">'+esc(words[Math.floor(Math.random()*words.length)])+'</b>';
    (document.querySelector('dialog[open]')||document.body).append(box);setTimeout(()=>box.remove(),1500);
  }
  function afterCaseFinished() {
    const s=state.session;
    if(!s.finished||s.counted)return;
    s.counted=true;if(state.countedShifts.includes('shift:'+s.seed))return;
    state.countedShifts=[...state.countedShifts,'shift:'+s.seed].slice(-300);state.stats.shifts++;state.stats.maxCoffees=Math.max(state.stats.maxCoffees,count(s.coffees));
    if(s.patients.length>=5&&s.patients.every(p=>p.score===caseMaximum(getCase(p.id))))state.stats.perfectShifts++;
  }
  function afterBoss() {
    const s=state.session,b=s?.boss;
    if(!b||!b.done||s.bossCounted)return;
    s.bossCounted=true;if(state.countedShifts.includes('boss:'+s.seed)){persist();return;}
    state.countedShifts=[...state.countedShifts,'boss:'+s.seed].slice(-300);if(bossCorrect(b)===b.items.length)state.stats.bossPerfect++;
    persist();checkRewards();
  }
  function missedCases() {
    const last=new Map();for(const r of state.history)last.set(r.caseId,r);
    return [...last.values()].filter(r=>r.score<r.maxScore).sort((a,b)=>Date.parse(b.completedAt)-Date.parse(a.completedAt)).map(r=>r.caseId);
  }
  function pickCases(pool,size,salt,missedFirst) {
    // Unplayed and imperfect cases come first; ties keep a fresh random order.
    const best=bestScores(),tier=c=>!best.has(c.id)?(missedFirst?1:0):best.get(c.id)<caseMaximum(c)?(missedFirst?0:1):2;
    return E.shuffle(pool,E.random(nowSeed()+'-'+salt)).sort((a,b)=>tier(a)-tier(b)).slice(0,size).map(c=>c.id);
  }
  function topicGroups() {
    const groups=new Map();
    for(const c of C.cases){const key=c.source?c.source.domain:'story';if(!groups.has(key))groups.set(key,{key,label:c.source?loc(c.topic):t('storyTopic'),cases:[]});groups.get(key).cases.push(c);}
    return [...groups.values()];
  }
  function persist() {
    try{localStorage.setItem(STORAGE,JSON.stringify(state));}catch(_){storageFailed=true;}
  }
  function navigate(next,focus=true) {
    view=next;location.hash=next;render();
    if(focus){window.scrollTo({top:0,behavior:'instant'});document.getElementById('main')?.focus({preventScroll:true});}
  }
  function toast(message,kind) {
    document.querySelector('.toast')?.remove();
    const el=document.createElement('div');el.className='toast'+(kind?' '+kind+'-toast':'');el.setAttribute('role','status');el.textContent=message;
    (document.querySelector('dialog[open]')||document.body).append(el);setTimeout(()=>el.remove(),4500);
  }
  function badge(acuity) { return '<span class="badge '+acuity+'">'+esc(t(acuity))+'</span>'; }
  function bookmark(id) { return '<button class="bookmark '+(state.bookmarks.includes(id)?'on':'')+'" data-bookmark="'+esc(id)+'" aria-label="'+esc(t(state.bookmarks.includes(id)?'unsaveCase':'saveCase'))+'" aria-pressed="'+state.bookmarks.includes(id)+'">'+(state.bookmarks.includes(id)?'★':'☆')+'</button>'; }
  function header() {
    return '<header class="topbar"><div class="container top-inner"><a href="#intro" class="brand" data-view="intro"><span class="brand-icon" aria-hidden="true">✚</span><div><strong>Night Shift Academy</strong><small>'+esc(t('tagline'))+'</small></div></a><nav class="nav" aria-label="'+esc(t('intro'))+'">'+['intro','library','atlas','protocols','progress','sources'].map(v=>'<button class="nav-btn '+(view===v?'active':'')+'" data-view="'+v+'" '+(view===v?'aria-current="page"':'')+'>'+esc(t(v))+'</button>').join('')+'</nav><div class="lang" role="group" aria-label="Language / Sprache / Idioma">'+['en','de','es'].map(l=>'<button data-lang="'+l+'" class="'+(state.lang===l?'active':'')+'" aria-pressed="'+(state.lang===l)+'" aria-label="'+({en:'English',de:'Deutsch',es:'Español'}[l])+'">'+l.toUpperCase()+'</button>').join('')+'</div></div></header>';
  }
  function footer() { return '<footer class="footer"><div class="container footer-inner"><p>'+esc(t('education'))+'<br>'+esc(t('clockNote'))+'</p><button data-view="sources">'+esc(t('sources'))+' ↗</button></div></footer>'; }
  function hospital() {
    return '<div class="cartoon-hero-art">'+A.hero(state.lang)+'<div class="cartoon-sticker">'+esc(t('caseCount'))+'</div></div>';
  }
  function castStrip() {
    return '<section class="cast-intro"><div class="section-head"><div><h2>'+esc(t('meetTeam'))+'</h2><p>'+esc(t('castSub'))+'</p></div></div><div class="cast-grid">'+['nurse','attending','chief','radiotherapist'].map(role=>{const person=comedy().staff[role];const quote=castLine(role);return '<button class="cast-card" data-talk="'+role+'">'+A.portrait(role,role==='attending'?'sleepy':role==='chief'?'stern':'smile',110,state.avatar)+'<div><h3>'+esc(person.name)+'</h3><small>'+esc(person.role)+'</small><p>“'+esc(quote)+'”</p></div></button>';}).join('')+'</div></section>';
  }

  function intro() {
    const has=!!state.session;
    return '<section class="hero comic-intro"><div><p class="eyebrow">'+esc(t('eyebrow'))+'</p><h1>'+t('hero')+'</h1><p class="lede">'+esc(t('lede'))+'</p><div class="actions"><button class="btn primary" data-action="'+(has?'resume':'setup')+'">'+esc(t(has?'resume':'start'))+' <span class="arrow">▶</span></button><button class="btn blitz-button" data-action="blitz" title="'+esc(t('blitzText'))+'">⚡ '+esc(t('blitz'))+'</button><button class="btn quiet" data-view="library">'+esc(t('explore'))+' →</button></div>'+(state.history.length?'<button class="rank-chip" data-view="progress">🎖️ '+esc(rankName())+' · '+xp()+' '+esc(t('xpLabel'))+' · '+state.badges.length+' 🏅</button>':'')+'<p class="offline">'+esc(t('offline'))+'</p></div>'+hospital()+'</section><div class="stats-band">'+[[C.cases.length,'cases'],[C.areas.length,'areas'],[3,'languages']].map(([n,k])=>'<div class="stat"><strong>'+n+'</strong><span>'+esc(t(k))+'</span></div>').join('')+'</div>'+castStrip()+dutyCards()+'<section class="section"><div class="section-head"><div><h2>'+esc(t('map'))+'</h2><p>'+esc(t('mapSub'))+'</p></div></div><div class="area-grid">'+C.areas.map(a=>'<button class="area-card" data-area="'+a.id+'" aria-label="'+esc(loc(a.title))+': '+esc(t('mapHint'))+'"><span class="area-cartoon" aria-hidden="true">'+A.areaIcon(a.id)+'</span><h3>'+esc(loc(a.title))+'</h3><p>'+esc(loc(a.description))+'</p><footer><span>'+C.cases.filter(c=>c.area===a.id).length+' '+esc(t('cases'))+'</span><span>▶</span></footer></button>').join('')+'</div></section><section class="intro-bottom"><div><h2>'+esc(t('how'))+'</h2><p class="muted" style="font-size:.83rem;margin-top:12px">'+esc(t('howSub'))+'</p><div class="how-steps">'+[1,2,3].map(n=>'<div class="how-step"><span class="step-number">0'+n+'</span><div><h3>'+esc(t('how'+n))+'</h3><p>'+esc(t('how'+n+'Text'))+'</p></div></div>').join('')+'</div></div><div class="mode-card"><h2>'+esc(t('mode'))+'</h2>'+['learn','shift'].map(k=>'<div class="mode-detail"><h3>'+esc(t(k))+'</h3><p>'+esc(t(k+'Text'))+'</p></div>').join('')+'<div class="actions" style="margin-top:24px"><button class="btn small" data-action="setup">'+esc(t('start'))+' ▶</button></div></div></section><section class="classic-bar"><div><h3>'+esc(t('classic'))+'</h3><p>'+esc(t('classicText'))+'</p></div><a class="btn quiet" href="classic/'+({en:'urology-night-shift.html',de:'nachtdienst-urologie.html',es:'guardia-urologia.html'}[state.lang])+'" target="_blank" rel="noopener">'+esc(t('openClassic'))+' ↗</a></section>';
  }

  function dutyCards() {
    return '<section class="section duty-section"><div class="section-head"><div><h2>'+esc(t('dutiesTitle'))+'</h2><p>'+esc(t('dutiesSub'))+'</p></div></div><div class="duty-grid">'+PLAYABLE.map(d=>'<article class="duty-card duty-'+d+'"><span class="duty-icon" aria-hidden="true">'+DUTY_ICON[d]+'</span><h3>'+esc(t('duty_'+d))+'</h3><p class="duty-time">'+esc(t('dutyTime_'+d))+' · '+esc(t('dutyCount').replace('{n}',String(C.cases.filter(c=>dutyOf(c)===d).length)))+'</p><p>'+esc(t('dutyText_'+d))+'</p><button class="btn small primary" data-duty-start="'+d+'">'+esc(t('dutyStart'))+' ▶</button></article>').join('')+'</div></section>';
  }
  function caseCard(c) {
    const attempts=state.history.filter(h=>h.caseId===c.id),best=attempts.length?Math.max(...attempts.map(pct)):null;
    return '<article class="case-card"><div class="case-cartoon-portrait">'+casePortrait(c,'neutral',76)+'</div><div class="case-meta"><span>'+esc(loc(getArea(c.area).title))+'</span>'+badge(c.acuity)+'</div><h3>'+esc(loc(c.title))+'</h3><div class="case-duty duty-'+dutyOf(c)+'">'+esc(dutyName(dutyOf(c)))+'</div>'+caseOriginBadge(c)+'<p>'+esc(loc(c.presenting))+'</p><div class="case-meta"><span>'+esc(patientLabel(c))+'</span><span>'+esc(t('level'))+' '+c.level+'</span></div><div class="case-meta"><span>'+(best===null?esc(t('notPlayed')):esc(t('best'))+' '+best+'%')+'</span></div><div class="card-footer"><button class="btn small" data-practice="'+c.id+'">'+esc(t('practice'))+' →</button>'+bookmark(c.id)+'</div></article>';
  }
  function filteredCases() {
    const q=query.toLocaleLowerCase(state.lang).trim();
    return C.cases.filter(c=>(areaFilter==='all'||c.area===areaFilter)&&(dutyFilter==='all'||dutyOf(c)===dutyFilter)&&(topicFilter==='all'||c.source?.domain===topicFilter)&&(!savedOnly||state.bookmarks.includes(c.id))&&(!q||[loc(c.title),loc(c.presenting),c.patient.name,patientName(c),c.id,c.source?.questionId||'',c.topic?loc(c.topic):''].some(x=>x.toLocaleLowerCase(state.lang).includes(q))));
  }
  function library() {
    const topics=[...new Map(C.cases.filter(c=>c.source&&c.topic).map(c=>[c.source.domain,c.topic])).entries()].sort((a,b)=>loc(a[1]).localeCompare(loc(b[1]),state.lang));
    return '<div class="page-head"><p class="eyebrow">02 / '+esc(t('mark'))+'</p><h1>'+esc(t('library'))+'</h1><p>'+esc(t('schematic'))+'</p></div><div class="toolbar"><input class="search" id="case-search" type="search" value="'+esc(query)+'" placeholder="'+esc(t('search'))+'" aria-label="'+esc(t('search'))+'"><label class="topic-select"><span>'+esc(t('dutyLabel'))+'</span><select id="duty-filter" aria-label="'+esc(t('dutyLabel'))+'">'+['all',...PLAYABLE].map(d=>'<option value="'+d+'" '+(dutyFilter===d?'selected':'')+'>'+esc(d==='all'?t('allDuties'):dutyName(d))+'</option>').join('')+'</select></label><label class="topic-select"><span>'+esc(t('topic'))+'</span><select id="topic-filter" aria-label="'+esc(t('topic'))+'"><option value="all">'+esc(t('allTopics'))+'</option>'+topics.map(([id,label])=>'<option value="'+esc(id)+'" '+(topicFilter===id?'selected':'')+'>'+esc(loc(label))+'</option>').join('')+'</select></label><button class="btn small quiet" data-action="saved-only" aria-pressed="'+savedOnly+'">'+esc(t(savedOnly?'showAll':'viewSaved'))+'</button></div><div class="chips" role="group" aria-label="'+esc(t('filter'))+'">'+[{id:'all',title:{en:t('all'),de:t('all'),es:t('all')}},...C.areas].map(a=>'<button class="chip '+(a.id===areaFilter?'active':'')+'" data-filter="'+a.id+'" aria-pressed="'+(a.id===areaFilter)+'">'+esc(loc(a.title))+'</button>').join('')+'</div><div id="case-results">'+libraryResults()+'</div>';
  }
  function libraryResults() {
    const cases=filteredCases(),size=18,pages=Math.max(1,Math.ceil(cases.length/size));libraryPage=Math.min(libraryPage,pages-1);
    const start=libraryPage*size,shown=cases.slice(start,start+size);
    return '<div class="library-pagination"><p role="status">'+(cases.length?(start+1)+'–'+(start+shown.length)+' / '+cases.length+' '+esc(t(cases.length===1?'caseSingular':'cases')):esc(t('empty')))+'</p>'+(cases.length?'<button class="btn small primary" data-action="practice-selection">🎯 '+esc(t('practiceSelection').replace('{n}',String(Math.min(10,cases.length))))+'</button>':'')+'<div class="actions"><button class="btn small quiet" data-action="page-prev" '+(libraryPage===0?'disabled':'')+'>'+esc(t('previousPage'))+'</button><span class="mono">'+(libraryPage+1)+' / '+pages+'</span><button class="btn small quiet" data-action="page-next" '+(libraryPage===pages-1?'disabled':'')+'>'+esc(t('nextPage'))+'</button></div></div><div class="case-grid" id="case-grid">'+shown.map(caseCard).join('')+'</div>';
  }
  const updatedBadge=c=>c.update?' <span class="badge routine">↻ '+esc(t('updatedBadge').replace('{date}',c.update.date.slice(0,7)))+'</span>':'';
  // Reviewed corrections from data/case-updates.json are always disclosed, with their reason and sources.
  function updateNote(c) {
    if(!c.update)return '';
    const refs=c.update.references.map(id=>C.references.find(r=>r.id===id)).filter(Boolean);
    return '<aside class="update-note"><b>↻ '+esc(t('updatedBadge').replace('{date}',c.update.date))+'</b> '+esc(loc(c.update.reason))+(refs.length?'<br><span>'+esc(t('updatedSources'))+': '+refs.map(r=>'<a href="'+esc(r.url)+'" target="_blank" rel="noopener noreferrer">'+esc(r.title)+' ↗</a>').join(' · ')+'</span>':'')+'</aside>';
  }
  function caseOriginBadge(c) {
    if(!c.source)return '<div class="case-format">'+esc(t('storyCase'))+updatedBadge(c)+'</div>';
    return '<div class="case-format">'+esc(loc(c.topic))+' · '+esc(t('bankCase'))+(c.source.status==='draft'?' <span class="badge urgent">'+esc(t('sourceDraft'))+'</span>':'')+(c.source.evidenceFlag?' <span class="badge urgent">'+esc(t('sourceEvidenceFlag'))+'</span>':'')+updatedBadge(c)+'</div>';
  }
  function vitalPanel(c) {
    if(!c.vitals)return '<p class="source-note">'+esc(t('sourceNotRecorded'))+'</p>';
    return '<div class="vital-grid" aria-label="'+esc(t('vitals'))+'">'+[[state.lang==='de'?'RR mmHg':state.lang==='es'?'PA mmHg':'BP mmHg',c.vitals.bp],[state.lang==='de'?'HF /min':state.lang==='es'?'FC /min':'HR /min',c.vitals.hr],['°C',c.vitals.temp.toLocaleString(state.lang)],['SpO₂ %',c.vitals.spo2],[state.lang==='de'?'AF /min':state.lang==='es'?'FR /min':'RR /min',c.vitals.rr]].map(([l,v])=>'<div class="vital"><small>'+esc(l)+'</small><strong>'+esc(v)+'</strong></div>').join('')+'</div>';
  }
  function sourceOrigin(c) {
    if(!c.source)return '';
    const s=c.source,notes=(s.evidenceNotes||[]).filter(note=>note.language===state.lang),citations=s.originalSources||[];
    return '<details class="source-origin"><summary>'+esc(t('sourceOrigin'))+' · '+esc(loc(c.topic))+(s.status==='draft'?' · '+esc(t('sourceDraft')):'')+(s.evidenceFlag?' · '+esc(t('sourceEvidenceFlag')):'')+'</summary><p>'+esc(t('sourceQuestion'))+': <span class="mono">'+esc(s.questionId)+'</span> · '+esc(t('sourceVersion'))+' '+s.version+'</p><p>'+esc(t('sourceApproval'))+': '+esc(t(s.clinicalSignoffLanguages.includes(state.lang)?'sourceApproved':'sourceUnapproved'))+'</p>'+notes.map(note=>'<p class="source-evidence-note">'+esc(note.text)+'</p>').join('')+'<h3>'+esc(t('sourceCitations'))+'</h3><ul>'+citations.map(reference=>'<li>'+esc(reference.title||reference.code||'')+(reference.year?' ('+esc(reference.year)+')':'')+(typeof reference.url==='string'&&reference.url.startsWith('https://')?' <a href="'+esc(reference.url)+'" target="_blank" rel="noopener noreferrer">↗</a>':'')+'</li>').join('')+'</ul></details>';
  }
  function optionButton(step,match,p,i) {
    const o=step.options.find(match),answered=!!p.feedback,struck=state.session.struck[p.id+':'+p.index]===o.id&&o.id!==step.best;
    const verdict=!answered?'':o.id===step.best?' correct':o.id===p.feedback?(o.score>0?' meh':' wrong'):'';
    const mark=!answered?'':o.id===step.best?'✓':o.id===p.feedback?(o.score>0?'◐':'✗'):'';
    return '<button class="option'+(p.feedback===o.id?' chosen':'')+verdict+(struck?' struck':'')+'" data-option="'+o.id+'" '+(answered||struck?'disabled':'')+'><span class="option-letter" aria-hidden="true">'+String.fromCharCode(65+i)+'</span><span class="option-text">'+esc(loc(o.text))+(struck?'<span class="sr-only"> ('+esc(t('struckMark'))+')</span>':'')+(answered&&o.id===step.best?'<span class="sr-only"> ('+esc(t('correctMark'))+')</span>':'')+'</span>'+(mark?'<span class="option-mark" aria-hidden="true">'+mark+'</span>':'<span class="option-time">'+o.minutes+' '+esc(t('minute'))+'</span>')+'</button>';
  }
  function preferredAnswer(step,chosen) {
    if(chosen===step.best)return '';
    const best=step.options.find(o=>o.id===step.best);
    return '<div class="preferred"><p><b>'+esc(t('recommended'))+':</b> '+esc(loc(best.text))+'</p><p class="why-correct"><b>'+esc(t('whyCorrect'))+':</b> '+esc(loc(best.feedback))+'</p></div>';
  }
  function optionsExplained(step,order,chosen) {
    return '<details class="all-options"><summary>'+esc(t('allOptions'))+'</summary><ol>'+order.map((id,i)=>{
      const o=step.options.find(o=>o.id===id),kind=o.id===step.best?'correct':o.score>0?'meh':'wrong';
      return '<li class="'+kind+(o.id===chosen?' chosen':'')+'"><span class="option-letter" aria-hidden="true">'+String.fromCharCode(65+i)+'</span><div><b>'+esc(loc(o.text))+'</b> <span class="explain-tag">'+(kind==='correct'?'✓ '+esc(t('correctMark')):kind==='meh'?'◐ '+o.score+' / 10':'✗')+(o.id===chosen?' · '+esc(t('yourChoice')):'')+'</span><p>'+esc(loc(o.feedback))+'</p></div></li>';
    }).join('')+'</ol></details>';
  }
  // Teaching schemas are inline SVG drawn for the game. Every structure is tappable; a case's key structures glow.
  const SCHEMAS=new Map((C.schemas||[]).map(s=>[s.id,s]));
  function schemaFigure(id,highlight=[],mode='explore') {
    const s=SCHEMAS.get(id);if(!s)return '';
    const label=part=>loc(s.parts.find(p=>p.id===part).label),hl=highlight.filter(part=>s.parts.some(p=>p.id===part));
    const svg=s.svg.replace(/data-part="([^"]+)"/g,(match,part)=>match+' tabindex="0" role="button" aria-label="'+esc(mode==='quiz'?t('atlasQuiz'):label(part))+'"'+(hl.includes(part)?' class="hl"':''));
    const order=[...hl,...s.parts.map(p=>p.id).filter(part=>!hl.includes(part))];
    // The note starts right under the drawing so the fact a tap reveals stays in view; selectPart moves it under the legend for chip taps.
    return '<figure class="schema" data-schema="'+esc(s.id)+'" data-mode="'+mode+'"><figcaption><b>'+esc(loc(s.title))+'</b><small>'+esc(loc(s.caption))+' '+esc(t('schemaNotice'))+'</small></figcaption><div class="schema-svg"><svg viewBox="'+esc(s.viewBox)+'" role="group" aria-label="'+esc(loc(s.title))+'" xmlns="http://www.w3.org/2000/svg">'+svg+'</svg></div>'+
      '<p class="schema-note" aria-live="polite">'+(mode==='quiz'?'':esc(t(hl.length?'schemaHintCase':'schemaHint')))+'</p>'+
      (mode==='quiz'?'':'<div class="schema-legend">'+order.map(part=>'<button type="button" class="schema-chip'+(hl.includes(part)?' hl':'')+'" data-legend-part="'+esc(part)+'">'+(hl.includes(part)?'★ ':'')+esc(label(part))+'</button>').join('')+'</div>')+'</figure>';
  }
  function caseVisuals(c) {
    const schema=c.schema&&SCHEMAS.has(c.schema.id)?schemaFigure(c.schema.id,c.schema.parts||[]):'';
    const media=(c.media||[]).map(m=>'<figure class="case-media"><img src="'+esc(m.src)+'" alt="'+esc(loc(m.alt))+'" loading="lazy"><figcaption>'+esc(loc(m.caption))+'<small>'+esc(t('imageSource'))+': '+esc(m.credit)+' · '+esc(t('imageLicense'))+': '+esc(m.license)+'</small></figcaption></figure>').join('');
    return schema||media?'<div class="case-visuals">'+schema+media+'</div>':'';
  }
  // Scroll an element into view inside its dialog or the page; on the page it must not end up under the sticky header.
  function reveal(el) {
    el.scrollIntoView?.({block:'nearest'});
    if(el.closest('dialog'))return;
    const bar=document.querySelector('.topbar'),cover=bar?bar.getBoundingClientRect().bottom:0,top=el.getBoundingClientRect().top;
    if(top<cover+8)window.scrollBy(0,top-cover-8);
  }
  function selectPart(figure,id,fromLegend=false) {
    const s=SCHEMAS.get(figure.dataset.schema),part=s&&s.parts.find(p=>p.id===id);if(!part)return;
    figure.classList.add('focus');
    figure.querySelectorAll('[data-part],[data-legend-part]').forEach(el=>el.classList.toggle('on',(el.dataset.part||el.dataset.legendPart)===id));
    // The fact appears next to what was tapped: under the drawing for a structure, under the legend for a chip.
    // A tapped chip must not move under the finger, so any shift of the legend is scrolled back and nothing else scrolls.
    const note=figure.querySelector('.schema-note'),legend=figure.querySelector('.schema-legend');
    const chip=fromLegend&&legend?[...legend.querySelectorAll('[data-legend-part]')].find(el=>el.dataset.legendPart===id):null,before=chip?.getBoundingClientRect().top;
    if(legend)(chip?legend.after(note):legend.before(note));
    note.innerHTML='<b>'+esc(loc(part.label))+'</b> – '+esc(loc(part.note));
    if(chip){const shift=chip.getBoundingClientRect().top-before;if(shift)(figure.closest('dialog')||window).scrollBy(0,shift);}
    else reveal(note);
  }
  // Therapy protocols: a learning overview of cycles and doses per tumour, each with its questions to practise. A switch shows
  // the radiotherapy schemes (total dose, dose per fraction, fractions, target) in the same layout.
  function protocols() {
    const rt=protocolKind==='radiotherapy'&&(C.radiotherapy||[]).length>0,entities=(rt?C.radiotherapy:C.protocols)||[],current=entities.find(e=>e.id===protocolEntity)||entities[0];
    const kinds=(C.radiotherapy||[]).length?'<div class="protocol-kinds" role="group" aria-label="'+esc(t('protocols'))+'">'+[['systemic','💊'],['radiotherapy','☢️']].map(([k,icon])=>'<button class="protocol-kind'+((k==='radiotherapy')===rt?' active':'')+'" aria-pressed="'+((k==='radiotherapy')===rt)+'" data-protocol-kind="'+k+'">'+icon+' '+esc(t(k==='radiotherapy'?'protocolKindRadiotherapy':'protocolKindSystemic'))+'</button>').join('')+'</div>':'';
    const head='<div class="page-head"><p class="eyebrow">'+esc(t('protocols'))+'</p><h1>'+esc(t(rt?'rtTitle':'protocolsTitle'))+'</h1><p>'+esc(t(rt?'rtSub':'protocolsSub'))+'</p></div>'+kinds+'<p class="warning-note protocol-warning" role="note">⚠️ '+esc(t(rt?'rtWarning':'protocolsWarning'))+'</p>';
    if(!current)return head;
    return head+'<div class="protocol-tabs" role="group" aria-label="'+esc(t('protocols'))+'">'+entities.map(e=>'<button class="protocol-tab'+(e===current?' active':'')+'" aria-pressed="'+(e===current)+'" data-protocol-entity="'+esc(e.id)+'">'+esc(loc(e.title))+' <span class="mono" aria-hidden="true">'+e.regimens.length+'</span></button>').join('')+'</div>'+
      '<div class="protocol-grid">'+current.regimens.map(rt?rtCard:protocolCard).join('')+'</div>';
  }
  const gy=value=>(state.lang==='en'?String(value):String(value).replace('.',','))+' Gy';
  function practiceButton(r) {
    const questions=[...new Set((r.questions||[]).filter(id=>getCase(id)))];
    return questions.length?'<div class="actions"><button class="btn" data-protocol-practice="'+esc(r.id)+'">🎯 '+esc(t('protocolPractice').replace('{n}',questions.length))+'</button></div>':'';
  }
  function protocolDetails(r) {
    return '<details class="protocol-more"><summary>'+esc(t('protocolSupport'))+' · '+esc(t('protocolCautions'))+' · '+esc(t('protocolEvidence'))+'</summary><p><b>'+esc(t('protocolSupport'))+':</b> '+esc(loc(r.support))+'</p><p><b>'+esc(t('protocolCautions'))+':</b> '+esc(loc(r.cautions))+'</p><p><b>'+esc(t('protocolEvidence'))+':</b> '+esc(loc(r.evidence))+'</p><p class="protocol-sources"><b>'+esc(t('protocolSources'))+':</b> '+r.sources.map(source=>'<a href="'+esc(source.url)+'" target="_blank" rel="noopener noreferrer">'+esc(source.label)+' ↗</a>').join(' · ')+'</p></details>';
  }
  function rtCard(r) {
    return '<article class="protocol-card rt-card" id="protocol-'+esc(r.id)+'"><h2>'+esc(loc(r.name))+'</h2><p class="protocol-setting"><b>'+esc(t('protocolSetting'))+':</b> '+esc(loc(r.setting))+'</p>'+
      '<p class="protocol-cycle"><b>'+esc(t('rtTechnique'))+':</b> '+esc(loc(r.technique))+'</p><p class="protocol-cycle"><b>'+esc(t('rtCombined'))+':</b> '+esc(loc(r.combined))+'</p>'+
      '<div class="protocol-table-wrap"><table class="protocol-table"><thead><tr><th scope="col">'+esc(t('rtTarget'))+'</th><th scope="col">'+esc(t('rtTotal'))+'</th><th scope="col">'+esc(t('rtPerFraction'))+'</th><th scope="col">'+esc(t('rtFractions'))+'</th><th scope="col">'+esc(t('protocolSchedule'))+'</th></tr></thead><tbody>'+
      r.phases.map(ph=>'<tr><th scope="row">'+esc(loc(ph.target))+'</th><td class="mono" data-label="'+esc(t('rtTotal'))+'">'+esc(gy(ph.totalGy))+'</td><td class="mono" data-label="'+esc(t('rtPerFraction'))+'">'+esc(ph.fractionGy==null?'–':gy(ph.fractionGy))+'</td><td class="mono" data-label="'+esc(t('rtFractions'))+'">'+esc(ph.fractions==null?t('rtContinuous'):String(ph.fractions))+'</td><td data-label="'+esc(t('protocolSchedule'))+'">'+esc(loc(ph.schedule))+'</td></tr>').join('')+'</tbody></table></div>'+
      protocolDetails(r)+practiceButton(r)+'</article>';
  }
  function protocolCard(r) {
    const route=d=>d.route==='intravesical'?t('routeIntravesical'):d.route;
    return '<article class="protocol-card" id="protocol-'+esc(r.id)+'"><h2>'+esc(loc(r.name))+'</h2><p class="protocol-setting"><b>'+esc(t('protocolSetting'))+':</b> '+esc(loc(r.setting))+'</p>'+
      '<p class="protocol-cycle"><b>'+esc(t('protocolCycle'))+':</b> '+esc(r.cycleDays?t('protocolCycleDays').replace('{n}',r.cycleDays):t('protocolContinuous'))+' · <b>'+esc(t('protocolCycles'))+':</b> '+esc(loc(r.cycles))+'</p>'+
      '<div class="protocol-table-wrap"><table class="protocol-table"><thead><tr><th scope="col">'+esc(t('protocolDrug'))+'</th><th scope="col">'+esc(t('protocolDose'))+'</th><th scope="col">'+esc(t('protocolRoute'))+'</th><th scope="col">'+esc(t('protocolSchedule'))+'</th></tr></thead><tbody>'+
      r.drugs.map(d=>'<tr><th scope="row">'+esc(loc(d.name))+'</th><td class="mono" data-label="'+esc(t('protocolDose'))+'">'+esc(loc(d.dose))+'</td><td data-label="'+esc(t('protocolRoute'))+'">'+esc(route(d))+'</td><td data-label="'+esc(t('protocolSchedule'))+'">'+esc(loc(d.schedule))+'</td></tr>').join('')+'</tbody></table></div>'+
      protocolDetails(r)+practiceButton(r)+'</article>';
  }

  function atlas() {
    const used=id=>C.cases.filter(c=>c.schema&&c.schema.id===id).length;
    return '<div class="page-head"><p class="eyebrow">'+esc(t('atlas'))+'</p><h1>'+esc(t('atlasTitle'))+'</h1><p>'+esc(t('atlasSub'))+'</p></div><div class="atlas-grid">'+[...SCHEMAS.values()].map(s=>'<article class="atlas-card"><div class="atlas-thumb" aria-hidden="true"><svg viewBox="'+esc(s.viewBox)+'" xmlns="http://www.w3.org/2000/svg">'+s.svg+'</svg></div><h3>'+esc(loc(s.title))+'</h3><p>'+esc(loc(s.caption))+'</p><small>'+esc(t(used(s.id)===1?'atlasUsedOne':'atlasUsed').replace('{n}',String(used(s.id))))+' · '+s.parts.length+' ⦿</small><div class="actions"><button class="btn small quiet" data-atlas-open="'+esc(s.id)+'">'+esc(t('atlasExplore'))+'</button><button class="btn small primary" data-atlas-quiz="'+esc(s.id)+'">🎯 '+esc(t('atlasQuiz'))+'</button></div></article>').join('')+'</div>';
  }
  let quiz=null;
  function openAtlas(id) {
    if(!SCHEMAS.has(id))return;
    const dlg=openDialog('<h2>'+esc(loc(SCHEMAS.get(id).title))+'</h2>'+schemaFigure(id)+'<div class="actions"><button class="btn primary" data-atlas-quiz="'+esc(id)+'">🎯 '+esc(t('atlasQuiz'))+'</button><button class="btn quiet" data-action="close-dialog">'+esc(t('close'))+'</button></div>');
    dlg.classList.add('schema-modal');
  }
  function startQuiz(id) {
    const s=SCHEMAS.get(id);if(!s)return;
    quiz={id,rounds:E.shuffle(s.parts.map(p=>p.id),E.random(nowSeed())).slice(0,5),index:0,score:0,answered:null};
    showQuiz();
  }
  function showQuiz() {
    const s=SCHEMAS.get(quiz.id),done=quiz.index>=quiz.rounds.length;
    if(done){
      const perfect=quiz.score===quiz.rounds.length,line=comedy().atlasResult[perfect?'perfect':quiz.score>=3?'good':'poor'],role=speakerFor(line);
      const dlg=openDialog('<div class="boss-finish">'+A.portrait(role,perfect?'smile':'stern',140,state.avatar)+'<h2>'+esc(t('quizDone').replace('{score}',quiz.score).replace('{total}',quiz.rounds.length))+'</h2><p><b>'+esc(comedy().staff[role].name)+':</b> '+esc(lineWithoutName(line,role))+'</p><div class="actions"><button class="btn primary" data-atlas-quiz="'+esc(quiz.id)+'">🎯 '+esc(t('quizAgain'))+'</button><button class="btn quiet" data-action="close-dialog">'+esc(t('close'))+'</button></div></div>');
      dlg.classList.add('schema-modal');
      if(perfect){state.stats.atlasPerfect++;persist();celebrate(true);checkRewards();}
      return;
    }
    const target=s.parts.find(p=>p.id===quiz.rounds[quiz.index]);
    const dlg=openDialog('<p class="eyebrow">'+esc(t('quizRound').replace('{n}',quiz.index+1).replace('{total}',quiz.rounds.length))+' · ★ '+quiz.score+'</p><h2 class="quiz-prompt">'+esc(t('quizPrompt').replace('{part}',loc(target.label)))+'</h2>'+schemaFigure(quiz.id,[],'quiz')+'<div class="actions quiz-actions" hidden><button class="btn primary" data-action="quiz-next">'+esc(t('dialogNext'))+' ▶</button></div>');
    dlg.classList.add('schema-modal');
  }
  function answerQuiz(figure,id,element) {
    if(!quiz||quiz.answered!==null||quiz.index>=quiz.rounds.length)return;
    const s=SCHEMAS.get(quiz.id),target=quiz.rounds[quiz.index],right=id===target,part=s.parts.find(p=>p.id===target);
    if(!s.parts.some(p=>p.id===id))return;
    quiz.answered=id;if(right)quiz.score++;
    figure.classList.add('focus');
    figure.querySelector('[data-part="'+target+'"]')?.classList.add('right','on');
    if(!right)figure.querySelector('[data-part="'+id+'"]')?.classList.add('wrong');
    figure.querySelector('.schema-note').innerHTML='<b>'+esc(right?t('quizRight'):t('quizWrong').replace('{part}',loc(s.parts.find(p=>p.id===id).label)))+'</b> '+esc(loc(part.label))+': '+esc(loc(part.note));
    document.querySelector('dialog[open] .quiz-actions')?.removeAttribute('hidden');
    // Focusing the button scrolls the verdict and the way forward into view on short laptop screens.
    document.querySelector('dialog[open] [data-action="quiz-next"]')?.focus();
    sound(right?'good':'splash');if(right)celebrate(false);else splash(element);
  }
  function sourceLinks(c) { return '<div class="case-refs"><span class="label">'+esc(t(c.source?'sourceRelated':'reviewSources'))+'</span><ul>'+c.references.map(id=>{const r=C.references.find(r=>r.id===id);return r?'<li><a href="'+esc(r.url)+'" target="_blank" rel="noopener noreferrer">'+esc(r.title)+' ↗</a></li>':'';}).join('')+'</ul></div>'; }
  function chart(p) {
    const c=getCase(p.id),a=getArea(c.area);
    let body='';
    if(p.finished) body=debrief(p,c);
    else {
      const s=c.steps[p.index];
      body='<section class="story"><span class="label">'+esc(t('story'))+'</span><p>'+esc(loc(c.presenting))+'</p></section>'+vitalPanel(c);
      if(state.session.mode==='learn')body+='<aside class="goals"><span class="label">'+esc(t('goals'))+'</span><ul>'+loc(c.objectives).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul></aside>';
      body+='<section class="decision-panel"><div class="step-track" aria-hidden="true">'+c.steps.map((_,i)=>'<span class="'+(i<p.index?'past':i===p.index?'now':'')+'"></span>').join('')+'</div><div class="step-meta"><span>'+esc(t(c.source?'sourceQuestion':s.kind))+'</span><span>'+esc(t('decision'))+' '+(p.index+1)+' / '+c.steps.length+'</span></div><h3 id="decision-prompt">'+esc(loc(s.prompt))+'</h3><div class="options" role="group" aria-labelledby="decision-prompt">'+p.order[p.index].map((id,i)=>optionButton(s,o=>o.id===id,p,i)).join('')+'</div>';
      if(p.feedback){const o=s.options.find(o=>o.id===p.feedback),cls=o.score===10?'good':o.score>0||c.source?'partial':'unsafe';
        const streak=cls==='good'&&state.session.streakAt===p.id+':'+p.index?state.session.streak:0;
        body+=(o.critical?attendingWarning(c,s,p.id+':'+p.index):characterComment(cls,p.id,p.index,streak,!!c.source))+'<div class="feedback '+cls+'" role="status"><span class="label">'+esc(t('feedback'))+'</span><h3>'+esc(t(c.source&&o.score!==10?'sourceIncorrect':cls))+(o.critical?' · '+esc(t('safety')):'')+'</h3><p>'+esc(loc(o.feedback))+'</p>'+preferredAnswer(s,o.id)+(p.index===c.steps.length-1?caseVisuals(c):'')+optionsExplained(s,p.order[p.index],o.id)+'<div class="actions"><button class="btn primary" data-action="next">'+esc(t(p.index===c.steps.length-1?'finishCase':'next'))+' →</button></div></div>';
      } else {
        body+='<p class="keys-hint">⌨️ '+esc(t('keysHint'))+'</p>';
        if(state.session.mode==='learn')body+='<details class="hint-box"><summary>'+esc(t('hint'))+'</summary><p>'+esc(t('hintText'))+'</p></details>';
      }
      body+='</section>';
    }
    return '<article class="chart"><div class="chart-top"><span>'+esc(loc(a.title))+' / '+esc(t(p.finished?'debrief':'open'))+'</span><span class="mono">'+esc(c.id.toUpperCase())+'</span></div><div class="chart-body"><div class="patient-head"><div class="patient-identity"><div class="patient-cartoon" aria-hidden="true">'+casePortrait(c,p.finished?'relieved':c.acuity==='critical'?'worried':'neutral',100)+'</div><div class="patient-name"><h2>'+esc(patientName(c))+' <span class="muted">'+(c.patient.age===null?'':c.patient.age)+'</span></h2><p>'+esc(loc(c.title))+'</p></div></div>'+bookmark(c.id)+'</div>'+sourceOrigin(c)+updateNote(c)+body+'</div></article>';
  }
  function debrief(p,c) {
    const max=c.steps.reduce((n,s)=>n+Math.max(...s.options.map(o=>o.score)),0);
    return '<div class="debrief-score">'+Math.round(p.score/max*100)+'<small> / 100</small></div><p class="muted" style="font-size:.76rem">'+esc(t('elapsed'))+': '+p.elapsed+' '+esc(t('minute'))+' · '+esc(t('safetyConcerns'))+': '+p.criticalErrors+'</p><section class="takeaway" style="margin-top:22px"><span class="label">'+esc(t('takeaway'))+'</span><p>'+esc(loc(c.takeaway))+'</p></section>'+caseVisuals(c)+p.answers.map((ans,i)=>{const s=c.steps[i],o=s.options.find(o=>o.id===ans.optionId);return '<div class="answer-review"><h3>'+esc(loc(s.prompt))+'</h3><p><b>'+esc(t('yourChoice'))+':</b> '+esc(loc(o.text))+'</p><p>'+esc(loc(o.feedback))+'</p>'+preferredAnswer(s,o.id)+'<span class="badge '+(o.score===10?'done':'urgent')+'">'+o.score+' / 10</span>'+optionsExplained(s,p.order[i],o.id)+'</div>';}).join('')+sourceLinks(c)+'<div class="actions"><button class="btn primary" data-action="'+(state.session.finished?'report':'next-patient')+'">'+esc(t(state.session.finished?'report':'nextPatient'))+' →</button></div>';
  }
  function play() {
    const s=state.session;
    if(!s)return '<div class="page-head"><h1>'+esc(t('dashboard'))+'</h1><p>'+esc(t('noActive'))+'</p><div class="actions" style="margin-top:20px"><button class="btn primary" data-action="setup">'+esc(t('start'))+'</button></div></div>';
    const p=s.patients.find(p=>p.id===s.selected),done=s.patients.filter(p=>p.finished).length;
    return '<div class="play-head"><div><p class="eyebrow">'+esc(dutyName(s.duty))+' · '+esc(t(s.mode))+' · '+esc(state.name||t('namePlaceholder'))+' · '+esc(rankName())+'</p><h1>'+esc(t('dashboard'))+'</h1></div><div class="play-kpis"><div class="play-kpi streak-kpi'+(s.streak>=3?' hot':'')+'" title="'+esc(t('streakBest'))+': '+s.bestStreak+'">'+esc(t('streakLabel'))+'<strong>🔥 '+s.streak+'</strong></div><div class="play-kpi">'+esc(t('simTime'))+'<strong>'+clock(s.clock)+'</strong></div><div class="play-kpi">'+esc(t('completed'))+'<strong>'+done+' / '+s.patients.length+'</strong></div></div></div>'+gameStage(s,p)+'<div class="play-grid"><aside class="queue" aria-label="'+esc(t('queue'))+'"><div class="queue-head"><span>'+esc(t('queue'))+'</span><span class="mono">'+s.patients.length+'</span></div>'+s.patients.map(q=>{const c=getCase(q.id),future=q.availableAt>s.clock;return '<button class="queue-item '+(q.id===s.selected?'active ':'')+(future?'future':'')+'" data-patient="'+q.id+'" '+(future?'disabled':'')+' '+(q.id===s.selected?'aria-current="true"':'')+'><div class="queue-top">'+(q.finished?'<span class="badge done">'+esc(t('finished'))+'</span>':badge(c.acuity))+'<span class="mono" style="font-size:.6rem">'+(q.finished?Math.round(q.score/caseMaximum(c)*100)+'%':clock(q.availableAt))+'</span></div><b>'+esc(patientName(c))+'</b><small>'+esc(loc(getArea(c.area).title))+'</small><small>'+(future?esc(t('arrives'))+' '+clock(q.availableAt):!q.finished?esc(t('waiting'))+' '+Math.max(0,s.clock-q.availableAt)+' '+esc(t('minute')):'')+'</small></button>';}).join('')+'<div class="queue-foot">'+(s.patients.some(q=>!q.finished&&q.availableAt>s.clock)?'<button class="btn quiet" data-action="wait">'+esc(t('wait'))+' →</button>':'<button class="btn quiet" data-action="'+(s.finished?'report':'setup')+'">'+esc(t(s.finished?'report':'start'))+'</button>')+'</div></aside>'+chart(p)+'</div><p class="game-note">'+esc(t('clockNote'))+'</p>';
  }
  function metrics(items) {
    const sum=items.reduce((n,r)=>n+r.score,0),max=items.reduce((n,r)=>n+r.maxScore,0);
    const mastered=new Set(items.filter(r=>pct(r)>=80).map(r=>r.caseId)).size;
    return '<div class="metric-grid">'+[[items.length,'attempts'],[max?Math.round(sum/max*100)+'%':'—','average'],[mastered,'mastered'],[items.reduce((n,r)=>n+r.criticalErrors,0),'safetyConcerns']].map(([v,k])=>'<div class="metric-card"><span>'+esc(t(k))+'</span><strong>'+v+'</strong></div>').join('')+'</div>';
  }
  function progress() {
    return '<div class="page-head"><p class="eyebrow">03 / '+esc(t('progress'))+'</p><h1>'+esc(t('progressTitle'))+'</h1><p>'+esc(t('progressSub'))+'</p></div>'+careerPanel()+metrics(state.history)+'<div class="actions" style="margin-bottom:25px"><button class="btn primary" data-action="revenge">🔁 '+esc(t('revenge'))+' ('+missedCases().length+')</button><button class="btn quiet" data-action="export" '+(!hasProgress(state)?'disabled':'')+'>'+esc(t('export'))+' ↓</button><button class="btn quiet" data-action="import">'+esc(t('importSave'))+' ↑</button><input type="file" id="save-file" accept=".json,application/json" hidden><button class="btn quiet danger" data-action="reset-dialog">'+esc(t('reset'))+'</button>'+(state.session?'<button class="btn" data-action="resume">'+esc(t('resume'))+' →</button>':'')+'</div><p class="small-note save-note">'+esc(t('saveHelp'))+'</p><div class="progress-grid"><section class="progress-panel"><h2>'+esc(t('byDuty'))+'</h2>'+PLAYABLE.map(d=>({id:d,title:dutyName(d)})).map(a=>{const h=state.history.filter(r=>dutyOf(getCase(r.caseId))===a.id);const average=h.length?Math.round(h.reduce((n,r)=>n+pct(r),0)/h.length):0;return '<div class="bar-row"><div class="bar-label"><span>'+esc(a.title)+'</span><span>'+h.length+' · '+(h.length?average+'%':'—')+'</span></div><div class="bar-track" role="meter" aria-label="'+esc(a.title)+'" aria-valuemin="0" aria-valuemax="100" aria-valuenow="'+average+'"><div class="bar-fill" style="width:'+average+'%"></div></div></div>';}).join('')+'</section><section class="progress-panel"><h2>'+esc(t('recent'))+'</h2>'+(state.history.length?state.history.slice(-8).reverse().map(r=>historyRow(r)).join(''):'<p class="muted" style="font-size:.8rem">'+esc(t('noHistory'))+'</p>')+'</section></div>'+topicPanel()+stickerAlbum()+'<div class="section-head"><h2>'+esc(t('bookmarks'))+'</h2></div><div class="case-grid">'+(state.bookmarks.length?state.bookmarks.map(id=>caseCard(getCase(id))).join(''):'<p class="empty">'+esc(t('noBookmarks'))+'</p>')+'</div>';
  }
  function careerPanel() {
    const points=xp(),rank=rankIndex(points),ranks=comedy().careerRanks,next=RANK_XP[rank+1];
    const fill=next===undefined?100:Math.round((points-RANK_XP[rank])/(next-RANK_XP[rank])*100);
    return '<section class="career-card"><div class="career-avatar" aria-hidden="true">'+A.avatar(state.avatar,104)+'<span class="career-medal">'+(rank+1)+'</span></div><div class="career-body"><p class="eyebrow">'+esc(t('careerTitle'))+'</p><h2>'+esc(ranks[rank])+'</h2><p class="career-joke">'+esc(comedy().careerJokes[rank])+'</p><div class="xp-track" role="meter" aria-label="'+esc(t('xpLabel'))+'" aria-valuemin="0" aria-valuemax="100" aria-valuenow="'+fill+'"><div class="xp-fill" style="width:'+fill+'%"></div></div><p class="xp-line"><b>'+points+' '+esc(t('xpLabel'))+'</b> · '+(next===undefined?esc(t('maxRank')):esc(t('nextRank'))+': '+esc(ranks[rank+1])+' ('+next+' '+esc(t('xpLabel'))+')')+'</p><small>'+esc(t('xpNote'))+'</small></div><ol class="career-ladder" aria-label="'+esc(t('careerTitle'))+'">'+ranks.map((name,i)=>'<li class="'+(i<rank?'past':i===rank?'now':'')+'"'+(i===rank?' aria-current="step"':'')+'><span>'+esc(name)+'</span></li>').join('')+'</ol></section>';
  }
  function topicPanel() {
    const best=bestScores();
    const rows=topicGroups().map(g=>({...g,played:g.cases.filter(c=>best.has(c.id)).length,mastered:g.cases.filter(c=>best.get(c.id)===caseMaximum(c)).length}))
      .sort((a,b)=>a.mastered/a.cases.length-b.mastered/b.cases.length||a.label.localeCompare(b.label,state.lang));
    return '<section class="progress-panel topic-panel"><h2>'+esc(t('topicsTitle'))+'</h2><p class="muted">'+esc(t('topicsSub'))+'</p><div class="topic-list">'+rows.map(g=>{const value=Math.round(g.mastered/g.cases.length*100);return '<div class="topic-row"><div class="bar-row"><div class="bar-label"><span>'+esc(g.label)+'</span><span>'+g.mastered+'/'+g.cases.length+' '+esc(t('masteredLabel'))+' · '+g.played+' '+esc(t('playedLabel'))+'</span></div><div class="bar-track" role="meter" aria-label="'+esc(g.label)+'" aria-valuemin="0" aria-valuemax="100" aria-valuenow="'+value+'"><div class="bar-fill" style="width:'+value+'%"></div></div></div><button class="btn small quiet" data-train="'+esc(g.key)+'">'+esc(t('train'))+' →</button></div>';}).join('')+'</div></section>';
  }
  function stickerAlbum() {
    const all=Object.keys(BADGE_ICONS),texts=comedy().badges;
    return '<section class="sticker-section"><div class="section-head"><div><h2>'+esc(t('stickers'))+'</h2><p>'+esc(t('stickersSub').replace('{got}',String(state.badges.length)).replace('{all}',String(all.length)))+'</p></div></div><ul class="sticker-grid">'+all.map((id,i)=>{const got=state.badges.includes(id);return '<li class="sticker '+(got?'got':'locked')+'" style="--tilt:'+(((i*7)%5)-2)*1.5+'deg"><span class="sticker-icon" aria-hidden="true">'+BADGE_ICONS[id]+'</span><b>'+esc(texts[id].title)+'</b><small>'+esc(texts[id].text)+'</small>'+(got?'<span class="sticker-check" aria-label="✓">✓</span>':'')+'</li>';}).join('')+'</ul></section>';
  }
  function historyRow(r) {
    const c=getCase(r.caseId);
    return '<div class="history-row"><div><button data-review="'+r.caseId+'" data-time="'+esc(r.completedAt)+'"><b>'+esc(loc(c.title))+'</b></button><small>'+esc(loc(getArea(c.area).title))+' · '+new Date(r.completedAt).toLocaleDateString(state.lang)+'</small></div><span class="score">'+pct(r)+'%</span></div>';
  }
  function report() {
    const s=state.session;
    if(!s || !s.finished)return play();
    const records=s.patients.map(p=>E.record(s,C,p.id));
    return chiefResult(s,records)+'<div class="page-head"><p class="eyebrow">'+esc(t('report'))+'</p><h1>'+esc(t('reportTitle'))+'</h1><p>'+esc(t('reportText'))+'</p></div>'+metrics(records)+'<div class="actions" style="margin-bottom:28px"><button class="btn boss-button" data-action="chief-challenge">'+esc(t('chiefChallenge'))+' ⚡</button><button class="btn primary" data-action="setup">'+esc(t('startAnother'))+' →</button>'+(s.patients.some(p=>p.score<caseMaximum(getCase(p.id)))?'<button class="btn" data-action="shift-revenge">🔁 '+esc(t('shiftRevenge'))+'</button>':'')+'<button class="btn quiet" data-action="export">'+esc(t('export'))+' ↓</button><button class="btn quiet" data-view="progress">'+esc(t('progress'))+'</button></div><div class="report-list">'+s.patients.map(p=>{const c=getCase(p.id);return '<div class="history-row"><div><button data-patient="'+p.id+'"><b>'+esc(loc(c.title))+'</b></button><small>'+esc(loc(getArea(c.area).title))+' · '+p.elapsed+' '+esc(t('minute'))+' · '+esc(t('safetyConcerns'))+': '+p.criticalErrors+'</small></div><span class="score">'+Math.round(p.score/caseMaximum(c)*100)+'%</span></div>';}).join('')+'</div>';
  }
  function sources() {return '<div class="page-head"><p class="eyebrow">04 / '+esc(t('sources'))+'</p><h1>'+esc(t('sourceTitle'))+'</h1><p>'+esc(t('sourceSub'))+'</p></div><div class="refs-list">'+C.references.map(r=>'<article class="ref-card"><h3><a href="'+esc(r.url)+'" target="_blank" rel="noopener noreferrer">'+esc(r.title)+' ↗</a></h3><p class="mono">'+esc(r.id)+'</p><small>'+esc(t('checked'))+' '+esc(r.checked)+'</small></article>').join('')+'</div>';}
  function render() {
    document.documentElement.lang=state.lang;document.title='Night Shift Academy · '+({en:'Urology',de:'Urologie',es:'Urología'}[state.lang]);
    document.querySelector('.skip').textContent=t('skip');
    root.innerHTML=header()+'<main class="container" id="main" tabindex="-1">'+(storageFailed?'<div class="storage-banner" role="status">'+esc(t('storageError'))+'</div>':'')+({intro,library,atlas,protocols,progress,sources,play,report}[view]||intro)()+'</main>'+footer();
  }
  function openDialog(content) {
    document.querySelector('dialog')?.remove();
    const dlg=document.createElement('dialog');dlg.className='dialog';dlg.innerHTML=content;document.body.append(dlg);
    const title=dlg.querySelector('h2');if(title){title.id='dialog-title-'+(++dialogSequence);dlg.setAttribute('aria-labelledby',title.id);}
    dlg.addEventListener('close',()=>dlg.remove());dlg.showModal();return dlg;
  }
  function dutyChoices() {
    return '<fieldset class="duty-field"><legend class="field">'+esc(t('dutyPick'))+'</legend><div class="duty-choices">'+PLAYABLE.map(d=>'<label class="duty-choice duty-'+d+'"><input type="radio" name="duty" value="'+d+'" '+(d===pendingDuty?'checked':'')+'><span class="duty-icon" aria-hidden="true">'+DUTY_ICON[d]+'</span><b>'+esc(t('duty_'+d))+'</b><small>'+esc(t('dutyTime_'+d))+' · '+esc(t('dutyCount').replace('{n}',String(C.cases.filter(c=>dutyOf(c)===d).length)))+'</small><span>'+esc(t('dutyText_'+d))+'</span></label>').join('')+'</div></fieldset>';
  }
  function setup(ids=null,duty=null) {
    pendingIds=ids;customSchedule=null;pendingDuty=PLAYABLE.includes(duty)?duty:PLAYABLE.includes(state.lastDuty)?state.lastDuty:PLAYABLE[0];
    openDialog('<form id="setup-form"><p class="eyebrow">'+esc(t('briefing'))+'</p><h2>'+esc(t('briefingTitle'))+'</h2><p>'+esc(t(ids?'learnText':'setupText'))+'</p>'+(state.session&&!state.session.finished?'<p class="warning-note">'+esc(t('newSession'))+'</p>':'')+avatarChoices()+'<label class="field" for="player-name">'+esc(t('player'))+'</label><input class="text-input" id="player-name" maxlength="32" autocomplete="nickname" value="'+esc(state.name)+'" placeholder="'+esc(t('namePlaceholder'))+'">'+(ids?'':dutyChoices())+'<fieldset style="border:0;margin:0;padding:0"><legend class="field">'+esc(t('modeLabel'))+'</legend><div class="radio-grid">'+(ids?['learn']:['learn','shift']).map(k=>'<label class="radio-card"><input type="radio" name="mode" value="'+k+'" '+(k===(ids?'learn':'shift')?'checked':'')+'>'+esc(t(k))+'</label>').join('')+'</div></fieldset>'+(ids?'':'<div style="margin-top:20px"><label class="file-label" for="schedule-file">'+esc(t('importSchedule'))+' ↑</label><input type="file" id="schedule-file" accept="application/json,.json" hidden><p class="small-note" id="schedule-status">'+esc(t('scheduleHelp'))+'</p></div>')+'<p class="small-note">'+esc(t('clockNote'))+'</p><div class="actions"><button class="btn primary" type="submit">'+esc(t('begin'))+' →</button><button class="btn quiet" type="button" data-action="close-dialog">'+esc(t('cancel'))+'</button></div></form>');
  }
  function completeNext() {
    const s=state.session,p=s.patients.find(p=>p.id===s.selected);
    const finished=E.next(s,C,p.id);
    // A patient counts once per shift, even when an older copy of this shift was loaded from a game file.
    if(finished&&!p.logged){if(!state.history.some(r=>r.shift===s.seed&&r.caseId===p.id)){state.history.push({...E.record(s,C,p.id),shift:s.seed});state.history=state.history.slice(-1000);}p.logged=true;}
    afterCaseFinished();
    persist();render();document.querySelector('.chart h2')?.scrollIntoView({block:'start',behavior:'instant'});
    document.querySelector(p.finished?'.chart [data-action]':'.option:not(:disabled)')?.focus({preventScroll:true});
    checkRewards();
  }
  function nextPatient() {
    const s=state.session;
    let p=s.patients.find(p=>!p.finished&&p.availableAt<=s.clock);
    if(!p){E.wait(s);p=s.patients.find(p=>!p.finished&&p.availableAt<=s.clock);}
    if(p){s.selected=p.id;persist();navigate('play');}else navigate('report');
  }
  function exportHistory() {
    const blob=new Blob([JSON.stringify(saveFile(),null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='night-shift-save-'+new Date().toLocaleDateString('sv-SE')+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  // Reads a chosen game file and asks before anything changes; nothing is stored until the player confirms.
  async function offerSave(file) {
    let found=null;
    try { if (file.size<=SAVE_LIMIT) found=readSaveFile(JSON.parse(await file.text())); } catch (_) { found=null; }
    if (!found) { pendingSave=null; toast('⚠️ '+t('saveInvalid')); return; }
    pendingSave=found;
    const save=found.save,records=save.history.length,cases=new Set(save.history.map(r=>r.caseId)).size,s=save.session,shift=chooseShift(state.session,s);
    const plural=(one,many,n)=>t(n===1?one:many).replace('{n}',n);
    const date=found.exportedAt?new Date(found.exportedAt).toLocaleString(state.lang):'—';
    const lines=[(found.named?'<b>'+esc(save.name)+'</b> · ':'')+esc(t('loadSaveFrom').replace('{date}',date)),
      records?esc(plural('loadSaveEntry','loadSaveEntries',records)+' · '+plural('loadSaveCase','loadSaveCasesCount',cases)):'',
      esc(t('loadSaveRank').replace('{rank}',comedy().careerRanks[rankIndex(xp(save.history))])+' · '+plural('loadSaveSticker','loadSaveStickers',save.badges.length)),
      s?esc(t(s.finished?'loadSaveShiftDone':'loadSaveShift').replace('{done}',s.patients.filter(p=>p.finished).length).replace('{total}',s.patients.length)):''].filter(Boolean);
    const shiftNote={replaces:['warning-note','loadSaveReplaces'],kept:['small-note','loadSaveShiftKept'],ahead:['small-note','loadSaveShiftAhead']}[shift.outcome];
    const dlg=openDialog('<h2>'+esc(t('loadSaveTitle'))+'</h2><ul class="save-summary">'+lines.map(line=>'<li>'+line+'</li>').join('')+'</ul><p>'+esc(t('loadSaveMerge'))+'</p>'+
      (shiftNote?'<p class="'+shiftNote[0]+'">'+esc(t(shiftNote[1]))+'</p>':'')+(found.skipped>0?'<p class="small-note">'+esc(plural('loadSaveSkippedOne','loadSaveSkipped',found.skipped))+'</p>':'')+
      '<div class="actions"><button class="btn primary" data-action="load-save">'+esc(t('loadSaveConfirm'))+'</button><button class="btn quiet" data-action="close-dialog">'+esc(t('cancel'))+'</button></div>');
    // Start at the top, so the player reads which file and date they are loading before confirming (small phones too).
    const title=dlg.querySelector('h2');title.tabIndex=-1;title.focus({preventScroll:true});dlg.scrollTop=0;
  }
  function loadSave() {
    if (!pendingSave) return;
    Object.assign(state,mergeSave(state,pendingSave));pendingSave=null;
    syncRewards();persist();document.querySelector('dialog')?.close();render();
    document.querySelector('[data-action="import"]')?.focus({preventScroll:true});toast('✅ '+t('saveLoaded'));
  }
  function reviewHistory(id,time) {
    const r=state.history.find(r=>r.caseId===id&&r.completedAt===time),c=getCase(id);if(!r)return;
    openDialog('<p class="eyebrow">'+esc(t('debrief'))+'</p><h2>'+esc(loc(c.title))+'</h2><div class="debrief-score">'+pct(r)+'<small> / 100</small></div><section class="takeaway"><p>'+esc(loc(c.takeaway))+'</p></section>'+caseVisuals(c)+r.answers.map((ans,i)=>{const step=c.steps[i],option=step.options.find(o=>o.id===ans.optionId);return '<div class="answer-review"><h3>'+esc(loc(step.prompt))+'</h3><p><b>'+esc(t('yourChoice'))+':</b> '+esc(loc(option.text))+'</p><p>'+esc(loc(option.feedback))+'</p>'+preferredAnswer(step,option.id)+optionsExplained(step,step.options.map(o=>o.id),option.id)+'</div>';}).join('')+sourceLinks(c)+'<button class="btn" data-action="close-dialog">'+esc(t('close'))+'</button>');
  }
  function avatarChoices() {
    return '<fieldset class="avatar-field"><legend>'+esc(t('playerAvatar'))+'</legend><div class="avatar-choices">'+[0,1,2].map(i=>'<button class="avatar-choice '+(state.avatar===i?'selected':'')+'" type="button" data-avatar="'+i+'" aria-pressed="'+(state.avatar===i)+'" aria-label="'+esc(t('playerAvatar'))+' '+(i+1)+'">'+A.avatar(i,92)+'</button>').join('')+'</div></fieldset>';
  }
  function quip(kind,salt='') {
    const lines=comedy()[kind];let hash=0;
    for(const char of String(salt))hash=(hash*31+char.charCodeAt(0))>>>0;
    return lines[hash%lines.length];
  }
  function castLine(role) {
    return comedy().opening.find(line=>line.speaker===role)?.text||(comedy().dutyOpening?.radiotherapy||[]).find(line=>line.speaker===role)?.text||comedy().castWelcome;
  }
  function speakerFor(text) {
    return ['nurse','attending','chief','radiotherapist'].find(role=>text.startsWith(comedy().staff[role].name+':'))||'nurse';
  }
  function lineWithoutName(text,role) {
    const prefix=comedy().staff[role].name+':';
    return text.startsWith(prefix)?text.slice(prefix.length).trim():text;
  }
  function characterComment(kind,id,index,streak=0,source=false) {
    // Wrong source answers get exam-style teasing; streak milestones get a celebration line.
    const text=streak?quip('streak',id+'-'+index+'-'+streak).replaceAll('{n}',String(streak)):quip(kind==='partial'&&source?'miss':kind,id+'-'+index),role=speakerFor(text);
    return '<aside class="character-comment '+kind+(streak?' streak':'')+'">'+A.portrait(role,kind==='good'?'smile':role==='chief'?'stern':'worried',92,state.avatar)+'<div class="comic-speech"><b>'+esc(comedy().staff[role].name)+'</b><p>'+esc(lineWithoutName(text,role))+'</p></div></aside>';
  }
  function gameStage(session,selected) {
    const area=getCase(selected.id).area;
    const patients=session.patients.map(p=>{
      const c=getCase(p.id),step=c.steps[p.index],choice=p.feedback&&step?.options.find(o=>o.id===p.feedback);
      return {id:p.id,name:c.patient.label?loc(c.patient.label):c.patient.name,age:c.patient.age,sex:c.patient.sex,ageBand:c.patient.ageBand,area:c.area,acuity:c.acuity,finished:p.finished,available:p.availableAt<=session.clock,selected:p.id===selected.id,feedback:choice?(choice.score===10?'good':choice.score>0||c.source?'partial':'unsafe'):null};
    });
    const duty=session.duty,board=duty==='board',room=board?t('duty_board'):loc(getArea(area).title),consultant=consultantOf(getCase(selected.id));
    return '<section class="cartoon-stage duty-'+esc(duty||'mixed')+'" aria-label="'+esc(room)+'"><div class="game-scene-heading"><h2>'+esc(room)+'</h2><span class="scene-tip">'+esc(t(board?'sceneHintBoard':'sceneHint'))+'</span></div>'+A.scene(area,patients,selected.id,clock(session.clock),state.avatar,state.lang,{duty,label:comedy().dutyBoard&&comedy().dutyBoard[duty]})+'<div class="game-team">'+['nurse',consultant,'chief'].map(role=>'<button class="team-character" data-action="'+({nurse:'ask-nurse',attending:'ask-attending',radiotherapist:'ask-attending',chief:'chief-challenge'}[role])+'">'+A.portrait(role,role==='attending'?attendingMood():role==='chief'?'stern':'smile',52,state.avatar)+'<span><b>'+esc(comedy().staff[role].name)+'</b><small>'+esc(t({nurse:'jokerLabel',attending:'askAttending',radiotherapist:'askRadiotherapist',chief:'chiefChallenge'}[role]))+(role===consultant?' · 📞 '+(ATTENDING_CALLS-count(session.calls))+'/'+ATTENDING_CALLS:'')+'</small></span></button>').join('')+'<button class="btn coffee-button" data-action="coffee" '+(session.finished?'disabled':'')+' title="'+esc(t('coffeeNote'))+'">☕ '+esc(t('coffeeLabel'))+' <span class="mono">+5 '+esc(t('minute'))+'</span></button><button class="btn quiet sound-button" data-action="sound" aria-pressed="'+state.sound+'">'+(state.sound?'♫ ':'♪ ')+esc(t(state.sound?'soundOn':'soundOff'))+'</button></div><p class="scene-banter">'+esc(board?comedy().dutyIntro.board:comedy().areaIntro[area])+'</p></section>';
  }
  function attendingMood() {
    // The attending sleeps through the night shift's quiet moments but is awake for daytime duties.
    const duty=state.session&&state.session.duty;
    return duty&&duty!=='night'&&duty!=='mixed'?'smile':'sleepy';
  }
  function handleScene(element) {
    if(element.dataset.sceneCoffee){coffeeBreak();return;}
    const session=state.session;
    if(element.dataset.scenePatient){
      const p=session?.patients.find(p=>p.id===element.dataset.scenePatient);
      if(p&&p.availableAt<=session.clock){session.selected=p.id;sound('pager');persist();render();document.querySelector('.chart')?.scrollIntoView({block:'start',behavior:'smooth'});}
      return;
    }
    const area=element.dataset.sceneArea;
    if(!getArea(area))return;
    if(!session){areaFilter=area;query='';savedOnly=false;navigate('library');return;}
    const candidates=session.patients.filter(p=>getCase(p.id).area===area&&p.availableAt<=session.clock);
    const p=candidates.find(p=>!p.finished)||candidates[0];
    if(p){session.selected=p.id;sound('pager');persist();render();}
    else talk('nurse',comedy().areaIntro[area]+'\n\n'+t('noPatientsYet'));
  }
  let dialogueLines=[],dialogueIndex=0,audio=null;
  function talk(role,text,expression) {
    const person=comedy().staff[role]||comedy().staff.nurse;
    const dlg=openDialog('<div class="story-dialogue"><div class="story-portrait">'+A.portrait(role,expression||(role==='attending'?attendingMood():role==='chief'?'stern':'smile'),156,state.avatar)+'</div><div class="story-bubble"><p class="eyebrow">'+esc(person.role)+'</p><h2>'+esc(person.name)+'</h2><p>'+esc(lineWithoutName(text,role)).replace(/\n/g,'<br>')+'</p><button class="btn primary" data-action="close-dialog">'+esc(t('dialogNext'))+' ▶</button></div></div>');
    dlg.classList.add('story-modal');
  }
  function startOpening() {
    // Newcomers meet the whole cast first; every session then opens with its duty's briefing.
    const duty=state.session&&state.session.duty,lines=(comedy().dutyOpening&&comedy().dutyOpening[duty])||[];
    const newcomer=!(state.history||[]).length&&!(state.stats&&state.stats.shifts);
    dialogueLines=newcomer||!lines.length?[...comedy().opening,...lines]:lines;dialogueIndex=0;showOpening();
  }
  function showOpening() {
    const line=dialogueLines[dialogueIndex],person=comedy().staff[line.speaker];
    const dlg=openDialog('<div class="story-dialogue"><div class="story-portrait">'+A.portrait(line.speaker,line.speaker==='chief'?'stern':line.speaker==='attending'?attendingMood():'smile',156,state.avatar)+'</div><div class="story-bubble"><p class="eyebrow">'+esc(person.role)+'</p><h2>'+esc(person.name)+'</h2><p>'+esc(line.text)+'</p><div class="actions"><button class="btn primary" data-action="story-next">'+esc(t('dialogNext'))+' ▶</button><button class="btn quiet small" data-action="story-skip">'+esc(t('dialogSkip'))+'</button></div><small class="mono">'+(dialogueIndex+1)+' / '+dialogueLines.length+'</small></div></div>');
    dlg.classList.add('story-modal');
  }
  function advanceOpening() {
    if(++dialogueIndex>=dialogueLines.length){document.querySelector('dialog')?.close();sound('pager');return;}
    showOpening();
  }
  function sound(kind) {
    if(!state.sound)return;
    try {
      const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)return;
      audio=audio||new Audio();audio.resume();
      const start=audio.currentTime;
      if(kind==='splash'){
        const length=Math.floor(audio.sampleRate*.35),buffer=audio.createBuffer(1,length,audio.sampleRate),samples=buffer.getChannelData(0);
        for(let i=0;i<length;i++)samples[i]=(Math.random()*2-1)*Math.pow(1-i/length,2.5);
        const noise=audio.createBufferSource(),filter=audio.createBiquadFilter(),gain=audio.createGain();
        noise.buffer=buffer;filter.type='bandpass';filter.frequency.setValueAtTime(1800,start);filter.frequency.exponentialRampToValueAtTime(500,start+.3);gain.gain.value=.25;
        noise.connect(filter);filter.connect(gain);gain.connect(audio.destination);noise.start(start);
        return;
      }
      (kind==='good'?[523,659,784]:[880,660]).forEach((frequency,i)=>{
        const osc=audio.createOscillator(),gain=audio.createGain(),at=start+i*.11;
        osc.type='sine';osc.frequency.value=frequency;gain.gain.setValueAtTime(.0001,at);gain.gain.exponentialRampToValueAtTime(.06,at+.008);gain.gain.exponentialRampToValueAtTime(.0001,at+.09);
        osc.connect(gain);gain.connect(audio.destination);osc.start(at);osc.stop(at+.1);
      });
    }catch(_){/* Sound is optional; visual play always works. */}
  }
  function coffeeBreak() {
    const session=state.session;
    if(!session||session.finished){const line=quip('coffee',session?.coffees||Date.now());talk(speakerFor(line),line);return;}
    session.clock+=5;session.coffees=(Number.isInteger(session.coffees)?session.coffees:0)+1;persist();render();
    const line=quip('coffee',session.coffees);talk(speakerFor(line),line+'\n\n'+t('coffeeNote'));
  }
  // Calling the attending gives the decision's hint: the rule that decides it, never the answer itself. A second call about the
  // same decision is free; after the answer the hint is a free debrief. Without hints left in the shift the nurse answers.
  function callAttending() {
    // Radiotherapy questions go to the radiation oncologist; the calls of a shift are shared.
    const session=state.session,p=session?.patients.find(p=>p.id===session.selected);
    if(!p||session.finished){const role=session?.duty==='radiotherapy'?'radiotherapist':'attending';talk(role,quip(role==='radiotherapist'?'radioIdle':'attendingIdle',session?.seed||'idle'));return;}
    const c=getCase(p.id),index=Math.min(p.index,c.steps.length-1),key=p.id+':'+index,step=c.steps[index];
    const role=consultantOf(c),radio=role==='radiotherapist';
    const hint=step.hint?loc(step.hint):loc(c.objectives)[0];
    if(p.finished||p.feedback){talk(role,quip(radio?'radioAfter':'attendingAfter',key)+'\n\n💡 '+hint);return;}
    session.called=session.called&&typeof session.called==='object'?session.called:{};
    if(!session.called[key]){
      if(count(session.calls)>=ATTENDING_CALLS){talk('nurse',quip(radio?'radioBusy':'attendingBusy',key));return;}
      session.calls=count(session.calls)+1;session.called[key]=true;session.clock+=CALL_MINUTES;persist();render();
    }
    talk(role,quip(radio?'radioCall':attendingMood()==='sleepy'?'attendingNight':'attendingDay',key)+'\n\n💡 '+hint+'\n\n'+t('attendingNote').replace('{n}',ATTENDING_CALLS-count(session.calls)));
  }
  // After an answer that would have harmed the patient, the consultant steps in with the decisive rule.
  function attendingWarning(c,step,key) {
    const role=consultantOf(c),hint=step.hint?loc(step.hint):loc(c.takeaway);
    return '<aside class="character-comment unsafe attending-warning">'+A.portrait(role,'worried',92,state.avatar)+'<div class="comic-speech"><b>'+esc(comedy().staff[role].name)+'</b><p>'+esc(lineWithoutName(quip(role==='radiotherapist'?'radioWarn':'attendingWarn',key),role))+'</p><p class="attending-hint"><b>'+esc(t('attendingImportant'))+':</b> '+esc(hint)+'</p></div></aside>';
  }

  function askNurse() {
    // The nurse's joker crosses out one of the weakest wrong answers. It costs game time, never points.
    const session=state.session,p=session?.patients.find(p=>p.id===session.selected);
    if(!p){talk('nurse',comedy().castWelcome);return;}
    const c=getCase(p.id),goals=c.source?'':'\n\n'+loc(c.objectives).map(goal=>'• '+goal).join('\n'),key=p.id+':'+p.index;
    if(session.finished||p.finished||p.feedback){talk('nurse',quip('hint',key)+goals);return;}
    session.struck=session.struck&&typeof session.struck==='object'?session.struck:{};
    if(session.struck[key]){talk('nurse',comedy().strikeUsed+goals);return;}
    const step=c.steps[p.index],wrong=step.options.filter(o=>o.id!==step.best),lowest=Math.min(...wrong.map(o=>o.score));
    const pool=wrong.filter(o=>o.score===lowest),pick=pool[Math.floor(E.random(session.seed+'-joker-'+key)()*pool.length)];
    if(!pick){talk('nurse',quip('hint',key)+goals);return;}
    session.struck[key]=pick.id;session.clock+=5;session.jokers=(Number.isInteger(session.jokers)?session.jokers:0)+1;
    if(state.stats)state.stats.jokers++;
    persist();render();
    talk('nurse',quip('strike',key)+'\n\n'+t('jokerNote')+goals);
  }
  function chiefResult(session,records) {
    const max=records.reduce((n,r)=>n+r.maxScore,0),sum=records.reduce((n,r)=>n+r.score,0),score=max?sum/max*100:0;
    const text=quip(score>=80?'reportGood':'reportMixed',session.seed),role=speakerFor(text),ranks=comedy().gameRank;
    return '<section class="chief-verdict"><div class="verdict-portrait">'+A.portrait(role,score>=80?'smile':'stern',136,state.avatar)+'</div><div class="comic-speech"><span class="label">'+esc(comedy().staff[role].name)+'</span><h2>'+esc(ranks[score>=85?0:score>=70?1:score>=50?2:3])+'</h2><p>'+esc(lineWithoutName(text,role))+'</p>'+(validBoss(session.boss)&&session.boss.done?'<p class="boss-score">'+esc(t('bossScore'))+': '+bossCorrect(session.boss)+' / '+session.boss.items.length+' ★</p>':'')+'</div></section>';
  }
  function validBoss(boss) {
    try {
      if(!boss||!Array.isArray(boss.items)||!boss.items.length||boss.items.length>5||!Array.isArray(boss.answers)||!Number.isInteger(boss.index)||boss.index<0||boss.index>=boss.items.length||typeof boss.done!=='boolean')return false;
      if(boss.answers.length<boss.index||boss.answers.length>boss.index+1)return false;
      if(boss.done&&(boss.index!==boss.items.length-1||boss.answers.length!==boss.items.length))return false;
      const seen=new Set();
      return boss.items.every((item,i)=>{
        if(!item||!Number.isInteger(item.stepIndex)||item.stepIndex<0)return false;
        const c=getCase(item.caseId),step=c?.steps[item.stepIndex];
        const key=item.caseId+'-'+item.stepIndex;if(seen.has(key))return false;seen.add(key);
        return step&&Array.isArray(item.order)&&item.order.length===step.options.length&&new Set(item.order).size===step.options.length&&item.order.every(id=>step.options.some(o=>o.id===id))&&(i>=boss.answers.length||typeof boss.answers[i]==='string'&&step.options.some(o=>o.id===boss.answers[i]));
      });
    }catch(_){return false;}
  }
  function bossCorrect(boss) {
    return boss.items.reduce((count,item,i)=>count+(boss.answers[i]===getCase(item.caseId).steps[item.stepIndex].best?1:0),0);
  }
  function startBoss() {
    const s=state.session;
    if(!s?.finished){talk('chief',t('bossLocked'));return;}
    if(!validBoss(s.boss)){
      const rng=E.random(s.seed+'-morning');
      const pool=s.patients.flatMap(p=>getCase(p.id).steps.map((_,i)=>({caseId:p.id,stepIndex:i})));
      const shuffled=E.shuffle(pool,rng),onePerArea=[];
      for(const area of C.areas){const item=shuffled.find(x=>getCase(x.caseId).area===area.id);if(item)onePerArea.push(item);}
      const selected=[...onePerArea,...shuffled.filter(x=>!onePerArea.some(y=>y.caseId===x.caseId&&y.stepIndex===x.stepIndex))].slice(0,5);
      s.boss={index:0,answers:[],done:false,items:E.shuffle(selected,rng).map(item=>({...item,order:E.shuffle(getCase(item.caseId).steps[item.stepIndex].options.map(o=>o.id),rng)}))};
      persist();
    }
    showBoss();
  }
  function showBoss() {
    const boss=state.session.boss;
    if(boss.done){
      const dlg=openDialog('<div class="boss-finish">'+A.portrait('chief',bossCorrect(boss)>=boss.items.length*.8?'smile':'stern',156,state.avatar)+'<h2>'+esc(t('challengeDone'))+'</h2><div class="debrief-score">'+bossCorrect(boss)+'<small> / '+boss.items.length+'</small></div><button class="btn primary" data-action="close-dialog">'+esc(t('dialogNext'))+' ▶</button></div>');dlg.classList.add('boss-modal');return;
    }
    const item=boss.items[boss.index],c=getCase(item.caseId),step=c.steps[item.stepIndex],answer=boss.answers[boss.index],choice=step.options.find(o=>o.id===answer),best=step.options.find(o=>o.id===step.best);
    const dlg=openDialog('<div class="boss-header">'+A.portrait('chief',answer?(answer===step.best?'smile':'stern'):'stern',106,state.avatar)+'<div><p class="eyebrow">'+esc(t('round'))+' '+(boss.index+1)+' / '+boss.items.length+'</p><h2>'+esc(comedy().staff.chief.name)+'</h2></div></div><p class="boss-intro">'+esc(boss.index===0&&!answer?comedy().chiefQuizIntro:t('challengeExplanation'))+'</p><div class="boss-case"><small>'+esc(loc(getArea(c.area).title))+' · '+esc(c.patient.label?loc(c.patient.label):c.patient.name)+'</small><h3>'+esc(loc(step.prompt))+'</h3></div><div class="options">'+item.order.map((id,i)=>{const option=step.options.find(o=>o.id===id);return '<button class="option '+(answer===id?'chosen':'')+'" data-boss-option="'+id+'" '+(answer?'disabled':'')+'><span class="option-letter">'+String.fromCharCode(65+i)+'</span><span class="option-text">'+esc(loc(option.text))+'</span></button>';}).join('')+'</div>'+(choice?'<div class="feedback '+(answer===step.best?'good':'partial')+'" role="status"><h3>'+esc(t(answer===step.best?'challengeCorrect':'challengeRetry'))+'</h3><p>'+esc(loc(choice.feedback))+'</p>'+(answer!==step.best?'<p class="preferred"><b>'+esc(t('recommended'))+':</b> '+esc(loc(best.text))+'</p>':'')+'<button class="btn primary" data-action="boss-next">'+esc(t('dialogNext'))+' ▶</button></div>':'')+'<p class="small-note">'+esc(t('clockNote'))+'</p>');
    dlg.classList.add('boss-modal');
  }
  function answerBoss(id) {
    const boss=state.session?.boss;if(!validBoss(boss)||boss.done||boss.answers[boss.index])return;
    const item=boss.items[boss.index],step=getCase(item.caseId).steps[item.stepIndex];if(!step.options.some(o=>o.id===id))return;
    boss.answers.push(id);persist();sound(id===step.best?'good':'splash');showBoss();
  }
  function nextBoss() {
    const boss=state.session?.boss;if(!validBoss(boss)||boss.done||!boss.answers[boss.index])return;
    if(boss.index===boss.items.length-1){boss.done=true;persist();render();showBoss();sound('good');}
    else{boss.index++;persist();showBoss();}
  }

  document.addEventListener('click',e=>{
    const schemaHit=e.target.closest('.schema [data-part],.schema [data-legend-part]');
    if(schemaHit){const figure=schemaHit.closest('.schema'),id=schemaHit.dataset.part||schemaHit.dataset.legendPart;if(figure.dataset.mode==='quiz')answerQuiz(figure,id,schemaHit);else selectPart(figure,id,!!schemaHit.dataset.legendPart);return;}
    const scene=e.target.closest('[data-scene-area],[data-scene-patient],[data-scene-coffee]');if(scene){handleScene(scene);if(scene.dataset.sceneCoffee)checkRewards();return;}
    const b=e.target.closest('button,a[data-view]');if(!b||b.disabled)return;
    if(b.dataset.avatar!==undefined){state.avatar=Number(b.dataset.avatar);persist();document.querySelectorAll('[data-avatar]').forEach(el=>{el.classList.toggle('selected',Number(el.dataset.avatar)===state.avatar);el.setAttribute('aria-pressed',String(Number(el.dataset.avatar)===state.avatar));});return;}
    if(b.dataset.talk){talk(b.dataset.talk,castLine(b.dataset.talk));return;}
    if(b.dataset.bossOption){
      const before=state.session?.boss?.answers.length;answerBoss(b.dataset.bossOption);
      const boss=state.session?.boss;
      if(boss&&boss.answers.length>before){const item=boss.items[boss.index],right=boss.answers[boss.index]===getCase(item.caseId).steps[item.stepIndex].best;if(right)celebrate(false);else splash(document.querySelector('dialog[open] .option.chosen'));}
      return;}
    if(b.dataset.view){e.preventDefault();navigate(b.dataset.view);return;}
    if(b.dataset.lang){state.lang=b.dataset.lang;persist();render();document.querySelector('[data-lang="'+state.lang+'"]')?.focus({preventScroll:true});return;}
    if(b.dataset.area){areaFilter=b.dataset.area;topicFilter='all';libraryPage=0;query='';savedOnly=false;navigate('library');return;}
    if(b.dataset.filter){areaFilter=b.dataset.filter;libraryPage=0;render();document.querySelector('[data-filter="'+areaFilter+'"]')?.focus({preventScroll:true});return;}
    if(b.dataset.bookmark){const id=b.dataset.bookmark;state.bookmarks=state.bookmarks.includes(id)?state.bookmarks.filter(x=>x!==id):[...state.bookmarks,id];persist();render();document.querySelector('[data-bookmark="'+id+'"]')?.focus({preventScroll:true});return;}
    if(b.dataset.practice){setup([b.dataset.practice]);return;}
    if(b.dataset.protocolKind){protocolKind=b.dataset.protocolKind==='radiotherapy'?'radiotherapy':'systemic';protocolEntity=null;render();document.querySelector('[data-protocol-kind="'+protocolKind+'"]')?.focus({preventScroll:true});return;}
    if(b.dataset.protocolEntity){protocolEntity=b.dataset.protocolEntity;render();document.querySelector('[data-protocol-entity="'+protocolEntity+'"]')?.focus({preventScroll:true});return;}
    if(b.dataset.protocolPractice){const r=((protocolKind==='radiotherapy'&&(C.radiotherapy||[]).length?C.radiotherapy:C.protocols)||[]).flatMap(e=>e.regimens).find(r=>String(r.id)===b.dataset.protocolPractice),ids=[...new Set((r?.questions||[]).filter(id=>getCase(id)))];if(ids.length)setup(pickCases(ids.map(getCase),10,'protocol-'+r.id,false));return;}
    if(b.dataset.dutyStart){setup(null,b.dataset.dutyStart);return;}
    if(b.dataset.atlasOpen){openAtlas(b.dataset.atlasOpen);return;}
    if(b.dataset.atlasQuiz){startQuiz(b.dataset.atlasQuiz);return;}
    if(b.dataset.patient){state.session.selected=b.dataset.patient;persist();navigate('play');return;}
    if(b.dataset.option){let choice;try{choice=E.answer(state.session,C,state.session.selected,b.dataset.option);}catch(_){return;}
      const milestone=afterAnswer(choice);sound(choice.score===10?'good':'splash');persist();render();answerEffects(choice,milestone);
      document.querySelector('.feedback [data-action]')?.focus({preventScroll:true});checkRewards();return;}
    if(b.dataset.train){const group=topicGroups().find(g=>g.key===b.dataset.train);if(group)setup(pickCases(group.cases,10,'topic-'+group.key,true));return;}
    if(b.dataset.review){reviewHistory(b.dataset.review,b.dataset.time);return;}
    switch(b.dataset.action){
      case'setup':setup();break;
      case'page-prev':libraryPage=Math.max(0,libraryPage-1);render();document.querySelector('#case-results')?.scrollIntoView({block:'start'});document.querySelector('[data-action="page-prev"]')?.focus({preventScroll:true});break;
      case'page-next':libraryPage++;render();document.querySelector('#case-results')?.scrollIntoView({block:'start'});document.querySelector('[data-action="page-next"]')?.focus({preventScroll:true});break;
      case'coffee':coffeeBreak();checkRewards();break;
      case'ask-nurse':askNurse();checkRewards();break;
      case'blitz':setup(pickCases(C.cases,5,'blitz',false));break;
      case'revenge':{const ids=missedCases().slice(0,10);if(ids.length)setup(ids);else talk('nurse',comedy().revengeNone);break;}
      case'shift-revenge':{const ids=state.session?.patients.filter(p=>p.score<caseMaximum(getCase(p.id))).map(p=>p.id)||[];if(ids.length)setup(ids);break;}
      case'practice-selection':{const pool=filteredCases();if(pool.length)setup(pickCases(pool,10,'selection',false));break;}
      case'ask-attending':callAttending();break;
      case'sound':state.sound=!state.sound;persist();sound('pager');render();document.querySelector('[data-action="sound"]')?.focus({preventScroll:true});break;
      case'story-next':advanceOpening();break;
      case'story-skip':document.querySelector('dialog')?.close();break;
      case'chief-challenge':startBoss();break;
      case'boss-next':nextBoss();afterBoss();break;
      case'quiz-next':if(quiz&&quiz.answered!==null){quiz.index++;quiz.answered=null;showQuiz();}break;
      case'resume':navigate(state.session?.finished?'report':'play');break;
      case'next':completeNext();break;
      case'next-patient':nextPatient();break;
      case'wait':E.wait(state.session);persist();render();break;
      case'report':navigate('report');break;
      case'export':exportHistory();break;
      case'import':document.getElementById('save-file')?.click();break;
      case'load-save':loadSave();break;
      case'saved-only':savedOnly=!savedOnly;libraryPage=0;render();document.querySelector('[data-action="saved-only"]')?.focus({preventScroll:true});break;
      case'close-dialog':document.querySelector('dialog')?.close();break;
      case'reset-dialog':openDialog('<h2>'+esc(t('resetTitle'))+'</h2><p>'+esc(t('resetText'))+'</p><div class="actions"><button class="btn danger" data-action="reset">'+esc(t('resetConfirm'))+'</button><button class="btn quiet" data-action="close-dialog">'+esc(t('cancel'))+'</button></div>');break;
      case'reset':state.history=[];state.bookmarks=[];state.session=null;state.stats=cleanStats(null);state.badges=[];state.countedShifts=[];persist();document.querySelector('dialog')?.close();render();break;
    }
  });
  document.addEventListener('keydown',e=>{
    if((e.key==='Enter'||e.key===' ')&&e.target.matches('.schema [data-part]')){e.preventDefault();e.target.dispatchEvent(new MouseEvent('click',{bubbles:true}));return;}
    if((e.key==='Enter'||e.key===' ')&&e.target.matches('[data-scene-area],[data-scene-patient],[data-scene-coffee]')){e.preventDefault();handleScene(e.target);}
  });
  document.addEventListener('keydown',e=>{
    if(e.altKey||e.ctrlKey||e.metaKey||e.repeat||e.target.closest?.('input,textarea,select,summary'))return;
    const key=e.key.toLowerCase(),index=/^[1-6]$/.test(key)?Number(key)-1:/^[a-f]$/.test(key)?key.charCodeAt(0)-97:-1;
    if(index<0)return;
    const dlg=document.querySelector('dialog[open]');
    const buttons=dlg?[...dlg.querySelectorAll('[data-boss-option]')]:view==='play'?[...document.querySelectorAll('.chart [data-option]')]:[];
    const target=buttons[index];
    if(target&&!target.disabled){e.preventDefault();target.click();}
  });
  document.addEventListener('input',e=>{if(e.target.id==='case-search'){query=e.target.value;libraryPage=0;document.getElementById('case-results').innerHTML=libraryResults();}});
  document.addEventListener('change',async e=>{
    if(e.target.id==='duty-filter'){dutyFilter=['all',...DUTIES].includes(e.target.value)?e.target.value:'all';libraryPage=0;document.getElementById('case-results').innerHTML=libraryResults();return;}
    if(e.target.id==='topic-filter'){topicFilter=e.target.value;libraryPage=0;document.getElementById('case-results').innerHTML=libraryResults();return;}
    if(e.target.id==='save-file'){const file=e.target.files[0];e.target.value='';if(file)offerSave(file);return;}
    if(e.target.id!=='schedule-file')return;
    const status=document.getElementById('schedule-status');
    try{
      const file=e.target.files[0];if(!file||file.size>100000)throw new Error('size');
      const data=JSON.parse(await file.text());
      const ids=data&&data.caseIds,single=DUTIES.includes(data&&data.duty);
      if(data.version!==2||!Array.isArray(ids)||!ids.length||ids.length>10||new Set(ids).size!==ids.length||ids.some(id=>!getCase(id))||
        (single?ids.some(id=>dutyOf(getCase(id))!==data.duty):ids.length!==10||C.areas.some(a=>ids.filter(id=>getCase(id).area===a.id).length!==2)))throw new Error('schema');
      customSchedule=data;status.textContent=t('imported')+' · '+(typeof data.date==='string'?data.date:'');
    }catch(_){customSchedule=null;status.textContent=t('invalidSchedule');}
  });
  document.addEventListener('submit',e=>{
    if(e.target.id!=='setup-form')return;e.preventDefault();
    const form=new FormData(e.target),mode=form.get('mode')||'shift',chosen=PLAYABLE.includes(form.get('duty'))?form.get('duty'):null;
    state.name=document.getElementById('player-name').value.trim().slice(0,32);
    const seed=customSchedule?String(customSchedule.seed||nowSeed()):nowSeed();
    const ids=pendingIds||customSchedule?.caseIds||E.scheduleDuty(C,seed,chosen||'night');
    const duty=pendingIds?commonDuty(pendingIds):customSchedule?(DUTIES.includes(customSchedule.duty)?customSchedule.duty:'mixed'):(chosen||'night');
    // A duty without cases cannot start; the last duty is remembered only once a session exists.
    let session;
    try{session=E.create(C,ids,mode,seed);}catch(_){toast('⚠️ '+t('dutyEmpty'));return;}
    if(chosen&&!customSchedule)state.lastDuty=chosen;
    state.session=cleanSession(Object.assign(session,{duty}));persist();document.querySelector('dialog').close();navigate('play');startOpening();
  });
  window.addEventListener('hashchange',()=>{const v=location.hash.slice(1);if(v!==view&&['intro','library','atlas','protocols','progress','sources','play','report'].includes(v)){view=v;render();}});
  syncRewards();
  render();
})();
