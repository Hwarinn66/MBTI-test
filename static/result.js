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
const DIMENSIONS = [
  ['EI','Ekstroversi','Introversi','Energi sosial'], ['SN','Sensing','Intuisi','Cara memahami'],
  ['TF','Thinking','Feeling','Cara memutuskan'], ['JP','Judging','Perceiving','Ritme keseharian'],
];
const FUNCTIONS={Ni:'Introverted Intuition',Ne:'Extraverted Intuition',Si:'Introverted Sensing',Se:'Extraverted Sensing',Ti:'Introverted Thinking',Te:'Extraverted Thinking',Fi:'Introverted Feeling',Fe:'Extraverted Feeling'};
const CATEGORIES={all:'Semua',anime:'Anime',artis:'Tokoh publik',movies:'Film & TV',kartun:'Kartun'};
let currentResult=null, allPeople=[], filter='all', count=8, toastTimer;
const isNumber=value=>typeof value==='number'&&Number.isFinite(value);
const clamp=(n,min,max)=>Math.max(min,Math.min(max,n));
function element(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;}
function validResult(result){return result && typeof result==='object' && /^[EIX][SNX][TFX][JPX]$/.test(result.final_result) && result.success!==false;}
function toast(text){clearTimeout(toastTimer);$('toast').textContent=text;$('toast').hidden=false;toastTimer=setTimeout(()=>{$('toast').hidden=true;},4500);}
function renderDimensions(result){
  const holder=$('dimensions-chart');holder.replaceChildren();
  for(const [dim,first,second,title] of DIMENSIONS){
    const a=result.dimension_scores?.[dim[0]], b=result.dimension_scores?.[dim[1]];
    const usable=isNumber(a)&&isNumber(b)&&a>=0&&b>=0&&a+b>0;
    const left=usable?Math.round(100*a/(a+b)):null;
    const row=element('div','dimension-row');
    const caption=element('div','dimension-labels');
    caption.append(element('strong','',`${first} (${dim[0]})`),element('strong','',`${second} (${dim[1]})`));
    const track=element('div','dimension-track');
    const bar=element('span');bar.style.width=`${left??0}%`;track.append(bar);track.setAttribute('role','img');
    track.setAttribute('aria-label',usable?`${title}: ${left}% ${first}, ${100-left}% ${second}`:`${title}: skor tidak tersedia`);
    const value=element('p','dimension-value',usable?(left===50?'50% · Seimbang · 50%':`${left}% / ${100-left}%`):'Rincian skor tidak tersedia untuk hasil ini.');
    row.append(caption,track,value);holder.append(row);
  }
}
function renderFunctions(result){
  const holder=$('function-stack');holder.replaceChildren();
  const stack=Array.isArray(result.function_stack)?result.function_stack.filter(f=>Object.hasOwn(FUNCTIONS,f)).slice(0,4):[];
  if(result.final_result.includes('X')||stack.length!==4){
    $('function-note').textContent='Susunan fungsi belum ditampilkan karena tipe belum lengkap. X menandakan dua sisi yang seimbang, sehingga belum ada satu susunan yang bisa dipilih.';
    $('cognitive-details').hidden=true;return;
  }
  const roles=['Dominan','Pendukung','Tersier','Inferior'];
  stack.forEach((f,i)=>{const item=element('div','stack-item');item.title=FUNCTIONS[f];item.append(element('small','',`${i+1} · ${roles[i]}`),element('strong','',f));holder.append(item);});
  $('function-note').textContent='Ilustrasi dari tipe dan skor dimensi, bukan pengukuran langsung kemampuan kognitif.';
  const chart=$('cognitive-chart');chart.replaceChildren();
  let items=0;
  for(const [f,name] of Object.entries(FUNCTIONS)){
    const score=result.cognitive_scores?.[f];if(!isNumber(score))continue;
    items++;
    const row=element('div','function-row');row.title=name;
    const track=element('span','mini-track');const bar=element('span');bar.style.width=`${clamp(score/50*100,0,100)}%`;track.append(bar);
    row.append(element('strong','',f),track,element('span','',`${clamp(score,0,50).toFixed(1)}`));chart.append(row);
  }
  $('cognitive-details').hidden=!items;
}
function renderAnalysis(result){
  const source={available:'Ulasan AI berdasarkan jawaban dan konteks yang kamu berikan.',not_requested:'Refleksi dasar dari skor jawabanmu.',not_configured:'Refleksi dasar · Ulasan AI belum tersedia.',unavailable:'Refleksi dasar · Layanan AI sedang tidak tersedia.'};
  $('analysis-source').textContent=source[result.ai_status]||'Ulasan dari hasil yang tersimpan.';
  const note=typeof result.ai_note==='string'?result.ai_note:'Ulasan tidak tersedia. Kamu tetap bisa membaca rincian skor di atas.';
  const holder=$('ai-note');holder.replaceChildren();
  // All dynamic copy, including model output, is text. Never execute stored HTML.
  note.slice(0,18000).replace(/\\n/g,'\n').split(/\n\s*\n/).filter(Boolean).forEach(p=>holder.append(element('p','',p.trim())));
  const details=[];
  if(isNumber(result.neutral_percentage))details.push(`${Math.round(clamp(result.neutral_percentage,0,100))}% jawaban netral`);
  if(isNumber(result.dataset_similarity))details.push(`Kemiripan teks referensi ${Math.round(clamp(result.dataset_similarity,0,1)*100)}% (indikator kemiripan, bukan akurasi)`);
  $('analysis-metrics').textContent=details.join(' · ');$('analysis-metrics').hidden=!details.length;
}
function drawPeople(){
  const grid=$('famous-people-grid');grid.replaceChildren();
  const people=allPeople.filter(p=>filter==='all'||p.category===filter);
  for(const person of people.slice(0,count)){
    const card=element('article','person-card');
    const avatar=element('div','person-avatar');
    const initials=person.name.split(/\s+/).slice(0,2).map(s=>[...s][0]).join('').toUpperCase();
    avatar.textContent=initials;avatar.setAttribute('aria-hidden','true');
    if(typeof person.image==='string'&&/^\/famous-people\/[\w./-]+$/.test(person.image)){
      const img=element('img');img.loading='lazy';img.alt='';img.src=person.image;
      img.addEventListener('error',()=>{avatar.textContent=initials;},{once:true});avatar.replaceChildren(img);
    }
    card.append(avatar,element('h3','',person.name),element('p','',person.series||person.profession||''),element('span','person-category',CATEGORIES[person.category]||'Referensi'));
    grid.append(card);
  }
  $('people-empty').hidden=people.length>0;
  $('load-more').hidden=count>=people.length;
  document.querySelectorAll('.filter-button').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.category===filter)));
}
async function loadPeople(type){
  if(type.includes('X')){$('people-section').hidden=true;return;}
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
  const text=type.includes('X')?`Aku sudah berefleksi lewat InnerSelf! Polaku ${type}; X berarti ada preferensi yang masih seimbang.`:`Hasil refleksi kepribadianku di InnerSelf: ${type} — ${TYPES[type][0]}.`;
  if(navigator.share){try{await navigator.share({title:'Hasil InnerSelf',text});return;}catch(error){if(error.name==='AbortError')return;}}
  if(navigator.clipboard&&window.isSecureContext){try{await navigator.clipboard.writeText(text);toast('Ringkasan hasil berhasil disalin.');return;}catch{}}
  $('share-text').value=text;$('share-dialog').showModal();$('share-text').focus();$('share-text').select();
}
export function renderResult(result){
  if(!validResult(result)){showInvalid();return;}
  currentResult=result;
  $('empty-result').hidden=true;$('result-content').hidden=false;
  const type=result.final_result;
  const name=typeof result.user_name==='string'?result.user_name.slice(0,60).trim():'';
  $('result-greeting').textContent=name?`Ini refleksimu, ${name}.`:'Hasil refleksimu.';
  $('mbti-type').textContent=type;
  $('mbti-nickname').textContent=TYPES[type]?.[0]||'Preferensimu masih seimbang';
  $('mbti-description').textContent=TYPES[type]?.[1]||'Beberapa sisi mendapat skor yang sama. Huruf X memberi ruang untuk ketidakpastian, tanpa memaksakan satu tipe kepribadian.';
  const chips=$('result-chips');chips.replaceChildren();
  DIMENSIONS.forEach(([dim,a,b],i)=>chips.append(element('span','result-chip',type[i]==='X'?`${dim[0]}/${dim[1]} seimbang`:type[i]===dim[0]?a:b)));
  const status=$('result-status');const notices=[];
  if(type.includes('X'))notices.push('X berarti belum ada kecenderungan yang lebih kuat. Tinjau jawaban bila ada yang kurang sesuai; jawaban netral tetap valid.');
  if(result.ai_status==='not_configured')notices.push('Ulasan AI belum diaktifkan oleh pengelola situs. Hasil skor dan refleksi dasar tetap tersedia.');
  else if(result.ai_status==='unavailable')notices.push('Layanan AI belum dapat merespons. Hasil di bawah tetap dihitung dari seluruh jawabanmu.');
  status.hidden=!notices.length;status.textContent=notices.join(' ');
  renderDimensions(result);renderFunctions(result);renderAnalysis(result);loadPeople(type);
  $('share-result').onclick=share;
}
function showInvalid(){
  $('empty-result').hidden=false;$('result-content').hidden=true;
  $('empty-title').textContent='Hasil tersimpan belum bisa dibaca.';
  $('empty-description').textContent='Kembali ke tes untuk meninjau jawabanmu dan menghitung hasil lagi. Tidak ada hasil contoh yang ditampilkan.';
}
function loadStoredResult(){
  let raw;
  try{raw=sessionStorage.getItem('mbti_result');}catch{}
  // Read older results without adding new persistent personal data.
  if(!raw){try{raw=localStorage.getItem('mbti_result');}catch{}}
  if(!raw)return;
  try{renderResult(JSON.parse(raw));}catch{showInvalid();}
}
if(document.body.dataset.page==='result')loadStoredResult();
