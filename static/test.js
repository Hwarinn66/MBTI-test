'use strict';
const $ = (id) => document.getElementById(id);
const DRAFT_KEY = 'innerself_draft_cognitive_v2';
const RESULT_KEY = 'mbti_result';
const labels = ['Sangat tidak setuju', 'Tidak setuju', 'Agak tidak setuju', 'Netral · kadang iya, kadang tidak', 'Agak setuju', 'Setuju', 'Sangat setuju'];
const choiceValues = [-3,-2,-1,'neutral',1,2,3];
const choiceLabel = c => labels[choiceValues.indexOf(c)];
const parseChoice = v => v === 'neutral' ? v : Number(v);
let questions = [], sections = {}, version = '', answers = {}, current = 0, busy = false, reviewing = false;
let storageAvailable = true;
const validChoice = (s) => choiceValues.includes(s);
const answeredCount = () => questions.filter(q => validChoice(answers[q.id]?.choice)).length;

function storageNotice() {
  if (!storageAvailable) {
    $('storage-notice').hidden = false;
    $('storage-notice').textContent = 'Penyimpanan tab tidak tersedia. Kamu tetap bisa mengisi tes; biarkan halaman ini terbuka sampai selesai.';
    document.querySelector('.journey-bottom span').textContent = 'Jawaban disimpan selama halaman terbuka.';
  }
}
function saveDraft() {
  const draft = {version, answers, current, profile:{name:$('user-name').value, age:$('user-age').value, gender:$('user-gender').value, local_llm:$('use-local-llm').checked}};
  try { sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft)); }
  catch { storageAvailable = false; storageNotice(); }
}
function restoreDraft() {
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    if (saved?.version !== version || !saved.answers || typeof saved.answers !== 'object') {
      sessionStorage.removeItem(DRAFT_KEY); return;
    }
    for (const q of questions) {
      const item = saved.answers[q.id];
      if (item && (validChoice(item.choice) || item.choice === null)) {
        answers[q.id] = {choice:item.choice, reason:typeof item.reason === 'string' ? item.reason.slice(0,600) : ''};
      }
    }
    current = Number.isInteger(saved.current) ? Math.max(0,Math.min(questions.length-1,saved.current)) : 0;
    const profile = saved.profile || {};
    $('user-name').value = typeof profile.name === 'string' ? profile.name.slice(0,60) : '';
    const age = Number(profile.age);
    $('user-age').value = Number.isInteger(age)&&age>=13&&age<=100 ? String(age) : '';
    $('user-gender').value = ['Perempuan','Laki-laki','Nonbiner'].includes(profile.gender) ? profile.gender : '';
    $('use-local-llm').checked = profile.local_llm === true;
  } catch { try { sessionStorage.removeItem(DRAFT_KEY); } catch { storageAvailable=false; storageNotice(); } }
}
function updateProgress() {
  const count = answeredCount();
  $('progress-count').textContent = `${count} / ${questions.length}`;
  $('total-progress').value = count;
  $('total-progress').max = questions.length;
  $('reset').hidden = !count && !Object.values(answers).some(a=>a.reason);
  document.querySelectorAll('.section-link').forEach(button => {
    const dim=button.dataset.section;
    const items=questions.filter(q=>q.section===dim);
    const done=items.filter(q=>validChoice(answers[q.id]?.choice)).length;
    button.classList.toggle('active', !reviewing && questions[current].section===dim);
    button.classList.toggle('complete',done===items.length);
    if (!reviewing && questions[current].section===dim) button.setAttribute('aria-current','step');
    else button.removeAttribute('aria-current');
    button.querySelector('small').textContent=`${done} dari ${items.length} terjawab`;
    button.setAttribute('aria-label',`${sections[dim].title}, ${done} dari ${items.length} terjawab`);
  });
}
function selectAnswer(choice) {
  if (busy || reviewing) return;
  const q=questions[current];
  answers[q.id] = {...answers[q.id],choice,reason:$('reason').value};
  document.querySelectorAll('input[name="agreement"]').forEach(input=>{input.checked=input.value===String(choice);});
  $('selection-label').textContent = choiceLabel(choice);
  $('next').disabled = false;
  saveDraft(); updateProgress();
}
function renderQuestion(focus = false) {
  reviewing=false;
  $('question-content').hidden=false; $('review-content').hidden=true;
  const q=questions[current], answer=answers[q.id];
  $('section-label').textContent=sections[q.section].title;
  $('question-number').textContent=String(current+1).padStart(2,'0');
  $('question-text').textContent=q.text;
  document.querySelectorAll('input[name="agreement"]').forEach(input=>{input.checked=validChoice(answer?.choice)&&input.value===String(answer.choice);});
  $('selection-label').textContent=validChoice(answer?.choice)?choiceLabel(answer.choice):'Pilih jawaban yang paling mendekati.';
  $('reason').value=answer?.reason||''; $('reason-count').textContent=`${$('reason').value.length}/600`;
  $('reason-details').open=Boolean(answer?.reason);
  $('previous').disabled=current===0;
  $('next').disabled=!validChoice(answer?.choice);
  $('next').querySelector('span').textContent=current===questions.length-1?'Tinjau hasil':'Lanjut';
  updateProgress(); saveDraft();
  if(focus) { $('question-text').focus({preventScroll:true}); $('question-area').scrollIntoView({block:'nearest',behavior:'auto'}); }
}
function renderReview() {
  reviewing=true;
  $('question-content').hidden=true; $('review-content').hidden=false;
  const grid=$('review-grid'); grid.replaceChildren();
  questions.forEach((q,i)=>{
    const complete=validChoice(answers[q.id]?.choice);
    const button=document.createElement('button');button.type='button';button.className='review-item'+(complete?'':' unanswered');
    button.textContent=String(i+1);button.setAttribute('aria-label',`Pertanyaan ${i+1}: ${complete?choiceLabel(answers[q.id].choice):'belum dijawab'}`);
    button.addEventListener('click',()=>{current=i;renderQuestion(true);});grid.append(button);
  });
  updateProgress(); $('review-title').focus({preventScroll:true});
  $('question-area').scrollIntoView({block:'start',behavior:'auto'});
}
function setupControls() {
  const nav=$('section-nav');nav.replaceChildren();
  Object.entries(sections).forEach(([dim,info],i)=>{
    const button=document.createElement('button');button.type='button';button.className='section-link';button.dataset.section=dim;
    const number=document.createElement('span');number.className='section-number';number.textContent=String(i+1).padStart(2,'0');
    const detail=document.createElement('span'),title=document.createElement('strong'),caption=document.createElement('small');
    title.textContent=info.title;detail.append(title,caption);button.append(number,detail);
    button.addEventListener('click',()=>{if(busy)return;current=questions.findIndex(q=>q.section===dim);renderQuestion(true);});nav.append(button);
  });
  const options=$('answer-options'); options.replaceChildren();
  labels.forEach((label,i)=>{
    const choice=choiceValues[i];
    const wrapper=document.createElement('label');wrapper.className='answer-choice';wrapper.dataset.score=i-3;wrapper.dataset.side=i>3?'positive':'negative';wrapper.title=label;
    const input=document.createElement('input');input.type='radio';input.name='agreement';input.value=String(choice);input.setAttribute('aria-label',label);
    const circle=document.createElement('span');circle.className='answer-circle';circle.setAttribute('aria-hidden','true');
    circle.innerHTML='<svg class="icon"><use href="/static/icons.svg#check"/></svg>';
    input.addEventListener('change',()=>selectAnswer(choice));wrapper.append(input,circle);options.append(wrapper);
  });
}
async function init() {
  $('load-state').hidden=false; $('load-error').hidden=true;
  try {
    const response=await fetch('/questions',{cache:'no-store',signal:AbortSignal.timeout(15000)});
    if(!response.ok)throw Error('questions');
    const data=await response.json();
    if(!Array.isArray(data.questions)||data.questions.length!==32||!data.sections)throw Error('schema');
    questions=data.questions;sections=data.sections;version=data.version;
    $('local-model-notice').textContent=data.local_llm_status==='configured'?'Model bahasa lokal terpasang. Narasi generatif akan diproses di server ini.':'Narasi berbasis bukti siap. Mode generatif memerlukan runtime llama-cpp-python dan file model GGUF di server.';
    restoreDraft();setupControls();renderQuestion();
    $('load-state').hidden=true; $('question-area').setAttribute('aria-busy','false');
  } catch {
    $('load-state').hidden=true;$('load-error').hidden=false;$('question-area').setAttribute('aria-busy','false');
  }
}
function setBusy(value) {
  busy=value; $('review-content').setAttribute('aria-busy',String(value));
  document.querySelectorAll('#review-content button,#review-content input,#review-content select,#section-nav button,#reset').forEach(el=>{el.disabled=value;});
  $('submit').querySelector('span').textContent=value?($('use-local-llm').checked?'Menyusun ulasan…':'Menghitung hasil…'):'Lihat hasilku';
  const icon=$('submit').querySelector('svg');icon.classList.toggle('spin',value);
  icon.querySelector('use').setAttribute('href',`/static/icons.svg#${value?'loader-circle':'arrow-right'}`);
}
async function inlineResult(result) {
  const response=await fetch('/result.html');if(!response.ok)throw Error('template');
  const doc=new DOMParser().parseFromString(await response.text(),'text/html');
  const main=doc.querySelector('main');if(!main)throw Error('template');
  document.querySelector('main').replaceWith(main);
  document.title='Hasil refleksimu — InnerSelf';
  const module=await import('/static/result.js');
  module.renderResult(result);window.scrollTo(0,0);
}
async function submit() {
  if(busy)return;
  const missing=questions.findIndex(q=>!validChoice(answers[q.id]?.choice));
  if(missing!==-1){current=missing;renderQuestion(true);return;}
  const age=$('user-age');
  if(!age.checkValidity()){
    document.querySelector('.profile-block').open=true;age.reportValidity();return;
  }
  $('submit-error').hidden=true;saveDraft();
  const payload={version,answers:questions.map(q=>({id:q.id,choice:answers[q.id].choice,reason:answers[q.id].reason||''})),user_name:$('user-name').value.trim(),user_age:age.value?Number(age.value):null,user_gender:$('user-gender').value,use_local_llm:$('use-local-llm').checked};
  setBusy(true);
  try {
    const response=await fetch('/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:AbortSignal.timeout($('use-local-llm').checked?900000:30000)});
    if(!response.ok){
      if(response.status===422)throw Error('validation');
      throw Error('server');
    }
    const result=await response.json();if(!result.success)throw Error('server');
    result.saved_at=new Date().toISOString();
    let saved=false;
    try{sessionStorage.setItem(RESULT_KEY,JSON.stringify(result));saved=true;}catch{storageAvailable=false;}
    if(saved){location.assign('/result.html');return;}
    await inlineResult(result);
  } catch(error) {
    if(!$('submit-error'))return;
    $('submit-error').textContent=error.name==='TimeoutError'?'Proses narasi lokal melewati 15 menit. Jawabanmu masih tersimpan di halaman ini. Kamu bisa mencoba lagi atau menonaktifkan narasi generatif lokal.':error.message==='validation'?'Ada jawaban atau profil yang belum valid. Pastikan usia 13–100 dan semua pertanyaan sudah dijawab.':'Hasil belum bisa diproses. Periksa koneksi, lalu coba lagi. Jawabanmu tetap ada di halaman ini.';
    $('submit-error').hidden=false;setBusy(false);
  }
}
$('previous').addEventListener('click',()=>{if(current>0){current--;renderQuestion(true);}});
$('next').addEventListener('click',()=>{if(!validChoice(answers[questions[current].id]?.choice))return;if(current<questions.length-1){current++;renderQuestion(true);}else renderReview();});
$('back-to-test').addEventListener('click',()=>renderQuestion(true));
$('reason').addEventListener('input',()=>{const q=questions[current];answers[q.id]={choice:answers[q.id]?.choice??null,reason:$('reason').value};$('reason-count').textContent=`${$('reason').value.length}/600`;saveDraft();updateProgress();});
['user-name','user-age','user-gender','use-local-llm'].forEach(id=>$(id).addEventListener('input',saveDraft));
$('reload').addEventListener('click',init);$('submit').addEventListener('click',submit);
$('reset').addEventListener('click',()=>{$('reset-dialog').returnValue='';$('reset-dialog').showModal();});
$('reset-dialog').addEventListener('close',()=>{if($('reset-dialog').returnValue!=='reset')return;answers={};current=0;$('user-name').value='';$('user-age').value='';$('user-gender').value='';$('use-local-llm').checked=false;try{sessionStorage.removeItem(DRAFT_KEY);sessionStorage.removeItem(RESULT_KEY);localStorage.removeItem(RESULT_KEY);}catch{}renderQuestion(true);});
document.addEventListener('keydown',event=>{
  if(busy||reviewing||!questions.length||$('reset-dialog').open||event.ctrlKey||event.metaKey||event.altKey)return;
  if(event.target.matches?.('textarea,select,input:not([type="radio"])'))return;
  if(/^[1-7]$/.test(event.key)){event.preventDefault();selectAnswer(choiceValues[Number(event.key)-1]);document.querySelector(`input[name="agreement"][value="${choiceValues[Number(event.key)-1]}"]`).focus();}
});
init();
