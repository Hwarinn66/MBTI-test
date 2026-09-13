const {JSDOM,VirtualConsole}=require('jsdom');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'../..');
const fixture=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',
  ['import sys,json; sys.path.insert(0,"tests"); from test_app import payload; from main import questionnaire,submit_test,Submission,famous_people',
   'rich = payload("ENTJ")',
   'for answer in rich["answers"]: answer["reason"] = "Saat kegiatan ke-{}, aku mendengarkan sebelum ikut berdiskusi.".format(answer["id"])',
   'print(json.dumps({"questions":questionnaire(),"payload":payload("ENTJ"),"result":submit_test(Submission(**payload("ENTJ"))),"neutral":submit_test(Submission(**payload())),"long_result":submit_test(Submission(**rich)),"people":famous_people()}))'
  ].join('\n')
],{cwd:root,encoding:'utf8'}));
const tick=()=>new Promise(resolve=>setTimeout(resolve,15));
function create(file,options={}){
  const logs=[],submits=[];const vc=new VirtualConsole();vc.on('jsdomError',e=>{if(!e.message.includes('navigation'))logs.push(e);});
  const dom=new JSDOM(fs.readFileSync(path.join(root,file),'utf8'),{url:'http://innerself.test/'+(file==='index.html'?'':file),runScripts:'outside-only',pretendToBeVisual:true,virtualConsole:vc});
  const w=dom.window;w.HTMLElement.prototype.scrollIntoView=function(){};w.scrollTo=()=>{};w.AbortSignal.timeout=()=>undefined;
  w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};
  w.HTMLDialogElement.prototype.close=function(value){this.returnValue=value;this.open=false;this.dispatchEvent(new w.Event('close'));};
  w.fetch=async(url,init)=>{
    if(options.networkError&&url==='/questions')throw Error('offline');
    if(url==='/questions')return{ok:true,json:async()=>fixture.questions};
    if(url==='/famous_people.json')return{ok:true,json:async()=>fixture.people};
    if(url==='/submit'){submits.push(JSON.parse(init.body));if(options.submitError)throw Error('server');return{ok:true,json:async()=>fixture.result};}
    throw Error('Unexpected request '+url);
  };
  if(options.blockStorage)Object.defineProperty(w,'sessionStorage',{get(){throw new w.DOMException('blocked','SecurityError');}});
  if(options.draft)w.sessionStorage.setItem('innerself_draft_cognitive_v2',options.draft);
  return{dom,w,logs,submits};
}
function run(w,file){let code=fs.readFileSync(path.join(root,'static',file),'utf8');if(file==='result.js')code=code.replace('export function renderResult','function renderResult');w.eval(code);}
async function main(){
  let {dom,w,logs,submits}=create('index.html');run(w,'test.js');await tick();
  assert.equal(w.document.querySelector('#question-content').hidden,false);
  assert.equal(w.document.querySelector('#next').disabled,true);
  assert.equal(w.document.querySelectorAll('.answer-choice').length,7);
  assert.equal(w.document.querySelector('input[value="0"]'),null);
  w.document.dispatchEvent(new w.KeyboardEvent('keydown',{key:'4'}));
  assert.equal(w.document.querySelector('input[value="neutral"]').checked,true);
  w.document.querySelector('#reason').value='Aku suka berkumpul tapi aku jarang bicara';w.document.querySelector('#reason').dispatchEvent(new w.Event('input'));
  w.document.querySelector('#next').click();w.document.querySelector('#previous').click();
  assert.equal(w.document.querySelector('#reason').value,'Aku suka berkumpul tapi aku jarang bicara');
  for(let i=0;i<32;i++){w.document.querySelector('input[value="'+fixture.payload.answers[i].choice+'"]').click();w.document.querySelector('#next').click();}
  assert.equal(w.document.querySelector('#review-content').hidden,false);
  assert.equal(w.document.querySelectorAll('.review-item').length,32);
  assert.equal(w.document.querySelector('#progress-count').textContent,'32 / 32');
  w.document.querySelector('#submit').click();await tick();
  assert.equal(submits.length,1);assert.equal(submits[0].answers.length,32);assert.equal(submits[0].use_local_llm,false);
  assert.equal(JSON.parse(w.sessionStorage.getItem('mbti_result')).final_result,'ENTJ');assert.equal(logs.length,0);dom.window.close();
  console.log('PASS 32-item flow, keyboard neutral, reason retention, canonical submission');
  ({dom,w}=create('index.html',{draft:'{broken'}));run(w,'test.js');await tick();assert.equal(w.document.querySelector('#question-content').hidden,false);dom.window.close();
  const saved={version:fixture.questions.version,answers:{1:{choice:'neutral',reason:'Kadang iya kadang tidak'}},current:1,profile:{name:'Dina',local_llm:false}};
  ({dom,w}=create('index.html',{draft:JSON.stringify(saved)}));run(w,'test.js');await tick();
  w.document.querySelector('#previous').click();assert.equal(w.document.querySelector('input[value="neutral"]').checked,true);
  w.document.querySelector('#reset').click();w.document.querySelector('#reset-dialog').close('reset');assert.equal(w.document.querySelector('#progress-count').textContent,'0 / 32');dom.window.close();
  console.log('PASS corrupt draft recovery, restored neutral, explicit reset');
  ({dom,w}=create('index.html',{blockStorage:true}));run(w,'test.js');await tick();assert.equal(w.document.querySelector('#storage-notice').hidden,false);dom.window.close();
  ({dom,w}=create('index.html',{networkError:true}));run(w,'test.js');await tick();assert.equal(w.document.querySelector('#load-error').hidden,false);dom.window.close();
  ({dom,w}=create('index.html',{submitError:true}));run(w,'test.js');await tick();
  for(let i=0;i<32;i++){w.document.querySelector('input[value="neutral"]').click();w.document.querySelector('#next').click();}
  w.document.querySelector('#submit').click();await tick();assert.equal(w.document.querySelector('#submit-error').hidden,false);assert.equal(w.document.querySelector('#submit').disabled,false);dom.window.close();
  console.log('PASS blocked storage, offline questions, retry after submit error');
  ({dom,w,logs}=create('result.html'));
  const result=structuredClone(fixture.result);result.user_name='<img src=x onerror=alert(1)>';
  result.reflection.paragraphs=['<img src=x onerror=alert(1)>','Paragraf kedua'];
  result.reflection.question_insights[0].reason='<script>alert(1)</script>';result.reason_count=1;
  w.sessionStorage.setItem('mbti_result',JSON.stringify(result));run(w,'result.js');await tick();
  assert.equal(w.document.querySelector('#mbti-type').textContent,'ENTJ');assert.equal(w.document.querySelector('#ai-note img'),null);
  assert.equal(w.document.querySelector('.reason-quote script'),null);assert.equal(w.document.querySelectorAll('.cognitive-row').length,8);
  assert.equal(w.document.querySelectorAll('.stack-item').length,4);assert.equal(w.document.querySelectorAll('.candidate-row').length,3);
  assert.equal(w.document.querySelectorAll('.insight-card').length,1);
  w.document.querySelector('#reason-filter').click();assert.equal(w.document.querySelectorAll('.insight-card').length,32);
  w.document.querySelector('#share-result').click();await tick();assert.equal(w.document.querySelector('#share-dialog').open,true);
  assert.ok(w.document.querySelector('#share-text').value.includes('Te–Ni–Se–Fi'));
  assert.ok(!w.document.querySelector('#share-text').value.includes('<script>'));assert.equal(logs.length,0);dom.window.close();
  console.log('PASS 8 functions, ENTJ stack, candidates, per-question filter, XSS-safe quotes, sharing');
  ({dom,w,logs}=create('result.html'));
  const longResult=structuredClone(fixture.long_result);
  longResult.reflection.mode='local_llm_mixed';longResult.reflection.local_llm_status='partial';longResult.reflection.generated_reason_count=2;
  w.sessionStorage.setItem('mbti_result',JSON.stringify(longResult));run(w,'result.js');await tick();
  const displayed=[...w.document.querySelectorAll('#ai-note p')].map(p=>p.textContent);
  assert.ok(displayed.length>14);assert.deepEqual(displayed,longResult.reflection.paragraphs);
  assert.ok(displayed.some(p=>p.startsWith('Di soal 32,')));
  assert.ok(w.document.querySelector('#analysis-metrics').textContent.includes('32 alasan dibahas'));
  assert.ok(w.document.querySelector('#analysis-source').textContent.includes('Narasi gabungan'));
  assert.equal(w.document.querySelector('#narrator-notice').hidden,false);
  assert.equal(w.document.querySelectorAll('.insight-card').length,32);assert.equal(logs.length,0);dom.window.close();
  console.log('PASS complete 32-reason narrative beyond 14 paragraphs, final conclusion, partial-model notice');
  ({dom,w}=create('result.html'));w.sessionStorage.setItem('mbti_result',JSON.stringify(fixture.neutral));run(w,'result.js');await tick();
  assert.equal(w.document.querySelector('#mbti-type').textContent,'Belum pasti');assert.equal(w.document.querySelectorAll('.cognitive-row').length,8);assert.equal(w.document.querySelector('#people-section').hidden,true);dom.window.close();
  ({dom,w}=create('result.html'));w.sessionStorage.setItem('mbti_result',JSON.stringify({schema_version:1,final_result:'ENTJ'}));run(w,'result.js');await tick();assert.equal(w.document.querySelector('#empty-result').hidden,false);dom.window.close();
  ({dom,w}=create('result.html'));run(w,'result.js');await tick();assert.equal(w.document.querySelector('#empty-result').hidden,false);dom.window.close();
  console.log('PASS neutral unresolved profile, old schema rejected, no fake empty results');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
