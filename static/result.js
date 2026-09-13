const $ = id => document.getElementById(id);
const TYPES = {
  INTJ:['Perancang yang visioner','Kamu cenderung mencari pola besar, membangun arah, dan memikirkan langkah yang masuk akal untuk mewujudkan ide.'],
  INTP:['Penjelajah ide','Kamu cenderung menikmati pertanyaan yang menantang, menelusuri logika, dan membuka kemungkinan baru sebelum menarik kesimpulan.'],
  ENTJ:['Penggerak yang terarah','Kamu cenderung melihat tujuan, menyusun strategi, dan mengajak orang lain bergerak menuju hasil yang jelas.'],
  ENTP:['Pemantik kemungkinan','Kamu cenderung menikmati pertukaran ide, mempertanyakan kebiasaan, dan mencoba sudut pandang yang belum terpikirkan.'],
  INFJ:['Pencari makna','Kamu cenderung membaca pola di balik pengalaman, menghargai hubungan yang dalam, dan mencari arah yang terasa bermakna.'],
  INFP:['Penjaga nilai','Kamu cenderung mendengarkan nilai pribadi, membayangkan kemungkinan, dan mencari cara hidup yang terasa selaras dengan dirimu.'],
  ENFJ:['Penghubung yang peduli','Kamu cenderung peka pada orang di sekitarmu dan senang membantu mereka bergerak menuju tujuan bersama.'],
  ENFP:['Penjelajah yang antusias','Kamu cenderung melihat banyak kemungkinan, tertarik pada cerita orang lain, dan memberi ruang bagi ide yang terasa bermakna.'],
  ISTJ:['Pembangun yang konsisten','Kamu cenderung mengandalkan pengalaman, memperhatikan detail, dan menuntaskan tanggung jawab dengan langkah yang teratur.'],
  ISFJ:['Pendamping yang perhatian','Kamu cenderung memperhatikan kebutuhan sehari-hari, mengingat detail yang penting, dan menunjukkan kepedulian lewat tindakan.'],
  ESTJ:['Pengelola yang praktis','Kamu cenderung menyukai kejelasan, mengatur langkah kerja, dan mengubah rencana menjadi hasil yang bisa dilihat.'],
  ESFJ:['Perawat kebersamaan','Kamu cenderung menikmati keterhubungan, memperhatikan kebutuhan orang lain, dan menciptakan keseharian yang tertata.'],
  ISTP:['Pemecah masalah praktis','Kamu cenderung mengamati dengan tenang, mencari cara kerja sesuatu, dan menyesuaikan langkah berdasarkan situasi nyata.'],
  ISFP:['Penikmat yang autentik','Kamu cenderung dekat dengan pengalaman saat ini, menjaga nilai pribadi, dan memilih cara berekspresi yang terasa milikmu sendiri.'],
  ESTP:['Pengambil langkah','Kamu cenderung cepat membaca keadaan, nyaman mencoba secara langsung, dan belajar dari apa yang terjadi di lapangan.'],
  ESFP:['Pembawa kehangatan','Kamu cenderung menikmati momen, terhubung lewat pengalaman bersama, dan merespons peluang yang ada di depanmu.'],
};

const FUNCTIONS={Te:'Extraverted Thinking',Ti:'Introverted Thinking',Fe:'Extraverted Feeling',Fi:'Introverted Feeling',Ne:'Extraverted Intuition',Ni:'Introverted Intuition',Se:'Extraverted Sensing',Si:'Introverted Sensing'};
const CATEGORIES={all:'Semua',anime:'Anime',artis:'Tokoh publik',movies:'Film & TV',kartun:'Kartun'};
let currentResult=null, allPeople=[], filter='all', count=8, toastTimer;
const isNumber=value=>typeof value==='number'&&Number.isFinite(value);
const clamp=(n,min,max)=>Math.max(min,Math.min(max,n));
function element(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;}
function validResult(r){
  return r?.schema_version===2 && r.success===true && (r.final_result===null||Object.hasOwn(TYPES,r.final_result)) &&
    r.functions && Object.keys(FUNCTIONS).every(f=>isNumber(r.functions[f]?.index)&&isNumber(r.functions[f]?.questionnaire_index)) &&
    Array.isArray(r.reflection?.paragraphs) && Array.isArray(r.reflection?.question_insights) && Array.isArray(r.decision?.candidates);
}
function toast(text){clearTimeout(toastTimer);$('toast').textContent=text;$('toast').hidden=false;toastTimer=setTimeout(()=>{$('toast').hidden=true;},4500);}
function renderFunctions(result){
  const chart=$('cognitive-chart');chart.replaceChildren();
  const ranked=Object.entries(result.functions).filter(([f])=>Object.hasOwn(FUNCTIONS,f)).sort((a,b)=>b[1].index-a[1].index);
  for(const [f,score] of ranked){
    const row=element('div','cognitive-row');
    const label=element('div','cognitive-row-label');
    label.append(element('strong','',f),element('span','',score.title),element('b','',score.index.toFixed(1)));
    const track=element('div','cognitive-track');const bar=element('span','cognitive-fill');
    bar.style.width=clamp(score.index,0,100)+'%';
    const marker=element('span','questionnaire-marker');marker.style.left=clamp(score.questionnaire_index,0,100)+'%';
    track.append(bar,marker);track.setAttribute('role','img');track.setAttribute('aria-label',f+': gabungan '+score.index+', pilihan saja '+score.questionnaire_index+', skala 0 sampai 100');
    const caption=element('p','function-evidence','Pilihan: +'+score.support+' / −'+score.opposition+' · '+score.neutral_count+' netral');
    row.append(label,track,caption);chart.append(row);
  }
  const holder=$('function-stack');holder.replaceChildren();
  const stack=Array.isArray(result.function_stack)?result.function_stack.filter(f=>Object.hasOwn(FUNCTIONS,f)).slice(0,4):[];
  const roles=['Dominan','Pendukung','Tersier','Inferior'];
  stack.forEach((f,i)=>{const item=element('div','stack-item');item.title=FUNCTIONS[f];item.append(element('small','',(i+1)+' · '+roles[i]),element('strong','',f));holder.append(item);});
  $('function-note').textContent=stack.length?'Susunan fungsi kandidat, bukan sekadar empat skor tertinggi. Delapan indeks dicocokkan dengan seluruh 16 susunan.':'Belum ada satu susunan yang cukup berbeda. Semua fungsi tetap ditampilkan tanpa memaksakan tipe.';
  const candidates=$('candidate-list');candidates.replaceChildren();
  result.decision.candidates.slice(0,3).forEach((candidate,i)=>{
    const item=element('div','candidate-row');
    const description=element('div');description.append(element('strong','',candidate.type),element('small','',candidate.stack.join(' – ')));
    item.append(element('span','candidate-number',String(i+1)),description,element('b','',candidate.fit.toFixed(1)));candidates.append(item);
  });
  $('score-comparison').textContent='Pilihan saja: '+(result.questionnaire_result||'belum pasti')+' · Pilihan + alasan: '+(result.final_result||'belum pasti');
}
function renderAnalysis(result){
  const reflection=result.reflection;
  const generative=reflection.mode==='local_llm';
  $('analysis-source').textContent=generative?'Narasi model bahasa lokal · berjalan di server ini, tanpa API AI eksternal.':'Narasi lokal berbasis bukti · disusun dari kutipan, pilihan, dan hasil klasifikasi teks.';
  const note=$('ai-note');note.replaceChildren();
  reflection.paragraphs.filter(p=>typeof p==='string').slice(0,14).forEach(p=>note.append(element('p','',p.slice(0,6000))));
  $('analysis-metrics').textContent=result.neutral_count+' jawaban netral · '+result.reason_count+' alasan tertulis · '+result.recognized_reason_count+' alasan dikenali model';
  const llmStatus=reflection.local_llm_status;
  const hints={not_configured:'Model bahasa lokal belum dipasang. Yang tampil adalah narasi berbasis bukti, bukan tulisan model generatif.',runtime_missing:'File model tersedia, tetapi runtime llama-cpp-python belum dipasang.',fallback:'Model bahasa lokal belum menghasilkan narasi yang lolos pemeriksaan. Narasi berbasis bukti tetap tersedia.',busy:'Model bahasa lokal sedang digunakan. Narasi berbasis bukti tetap ditampilkan.',no_reasons:'Narasi generatif memerlukan alasan tertulis; hasil pilihan tetap tersedia.'};
  $('narrator-notice').hidden=!hints[llmStatus];$('narrator-notice').textContent=hints[llmStatus]||'';
  const select=$('reason-filter');select.checked=result.reason_count>0;
  const draw=()=>{
    const holder=$('question-insights');holder.replaceChildren();
    const entries=reflection.question_insights.filter(i=>!select.checked||i.reason);
    const relation={empty:'Pilihan saja',aligned:'Selaras',contradictory:'Perlu ditinjau',qualified:'Ada nuansa',other_function:'Sudut pandang lain',unclear:'Bukti belum jelas'};
    entries.forEach(insight=>{
      if(!Number.isInteger(insight.question_id)||insight.question_id<1||insight.question_id>32)return;
      const details=element('details','insight-card');
      const summary=element('summary');
      const heading=element('span','insight-heading');heading.append(element('strong','','Soal '+insight.question_id),element('span','',insight.question));
      const badge=element('span','insight-badge',relation[insight.relationship]||'Refleksi');
      if(insight.relationship==='contradictory')badge.classList.add('needs-review');
      summary.append(heading,badge);details.append(summary);
      const body=element('div','insight-body');
      if(insight.reason)body.append(element('blockquote','reason-quote',insight.reason.slice(0,600)));
      body.append(element('p','insight-choice','Pilihanmu: '+insight.choice_label));
      const paragraphs=Array.isArray(insight.paragraphs)?insight.paragraphs:[];
      // The first paragraph repeats the displayed choice/quote.
      paragraphs.slice(1).filter(p=>typeof p==='string').forEach(p=>body.append(element('p','',p.slice(0,3000))));
      details.append(body);holder.append(details);
    });
    $('insights-empty').hidden=entries.length>0;
  };
  select.onchange=draw;draw();
}
function drawPeople(){
  const grid=$('famous-people-grid');grid.replaceChildren();
  const people=allPeople.filter(p=>filter==='all'||p.category===filter);
  for(const person of people.slice(0,count)){
    const card=element('article','person-card');
    const avatar=element('div','person-avatar');
    const initials=person.name.split(/\s+/).slice(0,2).map(s=>[...s][0]).join('').toUpperCase();
    avatar.textContent=initials;avatar.setAttribute('aria-hidden','true');
    const localImage=typeof person.image==='string'&&/^\/famous-people\/[\w./-]+$/.test(person.image);
    const commonsImage=typeof person.image==='string'&&person.image.startsWith('https://commons.wikimedia.org/wiki/Special:Redirect/file/');
    if(localImage||commonsImage){
      const img=element('img');img.loading='lazy';img.alt='';img.src=person.image;
      img.addEventListener('error',()=>{avatar.textContent=initials;},{once:true});avatar.replaceChildren(img);
    }
    card.append(avatar,element('h3','',person.name),element('p','',person.series||person.profession||''),element('span','person-category',CATEGORIES[person.category]||'Referensi'));
    if(commonsImage&&typeof person.image_source==='string'&&person.image_source.startsWith('https://commons.wikimedia.org/wiki/File:')){
      const credit=element('a','image-credit',person.image_credit||'Sumber gambar');
      credit.href=person.image_source;credit.target='_blank';credit.rel='noopener noreferrer';
      credit.title=person.image_license||'Lihat sumber dan lisensi';card.append(credit);
    }
    grid.append(card);
  }
  $('people-empty').hidden=people.length>0;
  $('load-more').hidden=count>=people.length;
  document.querySelectorAll('.filter-button').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.category===filter)));
}
async function loadPeople(type){
  if(!type){$('people-section').hidden=true;return;}
  $('people-section').hidden=false;
  try{
    const response=await fetch('/famous_people.json',{signal:AbortSignal.timeout(10000)});if(!response.ok)throw Error('people');
    const data=await response.json();
    allPeople=Array.isArray(data[type])?data[type].filter(p=>p&&typeof p.name==='string'&&typeof p.category==='string').map(p=>({...p,category:p.category.toLowerCase()})):[];
    const filters=$('people-filters');filters.replaceChildren();filter='all';count=8;
    for(const [key,label] of Object.entries(CATEGORIES)){
      if(key!=='all'&&!allPeople.some(p=>p.category===key))continue;
      const button=element('button','filter-button',label);button.type='button';button.dataset.category=key;
      button.addEventListener('click',()=>{filter=key;count=8;drawPeople();});filters.append(button);
    }
    $('load-more').onclick=()=>{count+=8;drawPeople();};drawPeople();
  }catch{$('people-empty').hidden=false;$('people-empty').textContent='Referensi tokoh belum bisa dimuat. Hasil tesmu tetap tersedia di atas.';}
}

async function share(){
  const type=currentResult.final_result;
  const text=type?'Hasil refleksiku di InnerSelf: '+type+' ('+currentResult.function_stack.join('–')+'). Hasil eksploratif, bukan tes MBTI resmi.':'Aku sudah berefleksi lewat InnerSelf. Pola fungsiku belum mengarah pada satu tipe yang cukup jelas.';
  if(navigator.share){try{await navigator.share({title:'Hasil InnerSelf',text});return;}catch(error){if(error.name==='AbortError')return;}}
  if(navigator.clipboard&&window.isSecureContext){try{await navigator.clipboard.writeText(text);toast('Ringkasan hasil berhasil disalin.');return;}catch{}}
  $('share-text').value=text;$('share-dialog').showModal();$('share-text').focus();$('share-text').select();
}
export function renderResult(result){
  if(!validResult(result)){showInvalid();return;}
  currentResult=result;$('empty-result').hidden=true;$('result-content').hidden=false;
  const type=result.final_result;
  const name=typeof result.user_name==='string'?result.user_name.slice(0,60).trim():'';
  $('result-greeting').textContent=name?'Ini refleksimu, '+name+'.':'Hasil refleksimu.';
  $('mbti-type').textContent=type||'Belum pasti';
  $('mbti-type').classList.toggle('unresolved-code',!type);
  $('mbti-nickname').textContent=TYPES[type]?.[0]||'Ada ruang untuk mengenal polamu';
  $('mbti-description').textContent=type?'Kandidat terdekat berdasarkan delapan fungsi kognitif. Cerita di balik jawabanmu lebih penting daripada sekadar empat huruf.':'Beberapa susunan memiliki kecocokan yang sama atau pola skormu belum cukup berbeda. Jawaban netral tetap sah dan tetap dihitung.';
  const chips=$('result-chips');chips.replaceChildren();
  (result.function_stack||[]).forEach(f=>chips.append(element('span','result-chip',f+' · '+FUNCTIONS[f])));
  const messages=Array.isArray(result.warnings)?result.warnings.filter(w=>typeof w==='string'):[];
  if(result.decision.status==='tentative')messages.push('Kandidat masih berdekatan. Jangan membaca hasil ini sebagai tipe yang pasti.');
  if(result.is_adjusted)messages.push('Bukti dari alasan mengubah kandidat dibanding pilihan saja. Lihat rincian agar perbedaannya dapat ditinjau.');
  $('result-status').hidden=!messages.length;$('result-status').textContent=messages.join(' ');
  renderFunctions(result);renderAnalysis(result);loadPeople(type);
  $('share-result').onclick=share;
}
function showInvalid(){
  $('empty-result').hidden=false;$('result-content').hidden=true;
  $('empty-title').textContent='Hasil lama perlu dihitung ulang.';
  $('empty-description').textContent='Tes sekarang menilai delapan fungsi kognitif. Hasil versi empat dimensi tidak dikonversi secara otomatis; silakan isi tes yang baru.';
}
function loadStoredResult(){
  let raw;try{raw=sessionStorage.getItem('mbti_result');}catch{}
  if(!raw)return;
  try{renderResult(JSON.parse(raw));}catch{showInvalid();}
}
if(document.body.dataset.page==='result')loadStoredResult();
