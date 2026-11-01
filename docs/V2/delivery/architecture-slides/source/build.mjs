// Native, editable slide objects and SVGs share one geometry source.
// Usage: BONGHWA_ARTIFACT_MODULES=<bundled node_modules> node build.mjs <build-dir>
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
const require=createRequire(path.join(process.env.BONGHWA_ARTIFACT_MODULES,'package.json'));
const {Presentation,PresentationFile}=require('@oai/artifact-tool');
const out=path.resolve(process.argv[2]);
await fs.mkdir(out,{recursive:true});
const W=1600,H=900,FONT='Apple SD Gothic Neo';
const C={paper:'#F7F8F5',ink:'#172E2A',muted:'#61736F',line:'#DAE3DC',green:'#1C7055',pale:'#E7F1E8',teal:'#146C76',tealLight:'#E6F1F2',red:'#BD463E',redLight:'#FBEDE8',orange:'#B96928',orangeLight:'#F8EDDD',yellow:'#F0BD4B',white:'#FFFFFF',gray:'#71817D',soft:'#EBEFEB'};
const pages=[];let p;
function page(title,subtitle,n){p={title,items:[],notes:''};pages.push(p);rect(0,0,W,H,C.paper);text(72,48,1300,62,title,48,C.ink,true);text(74,120,1440,38,subtitle,25,C.muted);rect(72,179,55,5,C.green);text(72,853,1300,26,'봉화지기  /  산불 MVP 시연 구성  /  2026.11.01 기준',18,C.muted);text(1450,847,78,32,`${n} / 3`,20,C.muted,false,'right');}
function rect(x,y,w,h,fill,stroke='none',r=0,sw=1,dash=false){p.items.push({kind:'rect',x,y,w,h,fill,stroke,r,sw,dash});}
function circle(x,y,r,fill,stroke='none',sw=1){p.items.push({kind:'ellipse',x:x-r,y:y-r,w:r*2,h:r*2,fill,stroke,sw});}
function text(x,y,w,h,value,size=26,color=C.ink,bold=false,align='left'){p.items.push({kind:'text',x,y,w,h,value,size,color,bold,align});}
function lines(x,y,w,values,size=24,color=C.muted,leading=34,bold=false){values.forEach((v,i)=>text(x,y+i*leading,w,leading+5,v,size,color,bold));}
function poly(points,stroke=C.ink,sw=3,fill='none',close=false,dash=false){p.items.push({kind:'poly',points,stroke,sw,fill,close,dash});}
function arrow(x1,y,x2,color=C.line,sw=3){poly([[x1,y],[x2-8,y]],color,sw);poly([[x2-16,y-7],[x2,y],[x2-16,y+7]],color,sw);}
function down(x,y1,y2,color=C.line){poly([[x,y1],[x,y2-8]],color,3);poly([[x-7,y2-16],[x,y2],[x+7,y2-16]],color,3);}
function pill(x,y,w,label,fill,color=C.ink,size=20){rect(x,y,w,36,fill,'none',18);text(x,y+2,w,30,label,size,color,true,'center');}
function dot(x,y,color){circle(x,y,5,color);}
function doc(x,y,s,color=C.green){rect(x,y,58*s,74*s,C.white,color,7*s,3*s);for(let i=0;i<3;i++)poly([[x+13*s,y+(23+i*13)*s],[x+(i===2?36:45)*s,y+(23+i*13)*s]],color,3*s);}
function stack(x,y,s,color=C.green){rect(x+16*s,y-11*s,58*s,74*s,C.pale,'none',7*s);rect(x+8*s,y-5*s,58*s,74*s,C.white,C.line,7*s,2*s);doc(x,y,s,color);}
function search(x,y,s,color=C.green){circle(x+30*s,y+30*s,24*s,'none',color,5*s);poly([[x+47*s,y+48*s],[x+69*s,y+70*s]],color,6*s);circle(x+22*s,y+26*s,3*s,color);circle(x+35*s,y+21*s,3*s,color);circle(x+35*s,y+35*s,3*s,color);poly([[x+22*s,y+26*s],[x+35*s,y+21*s],[x+35*s,y+35*s],[x+22*s,y+26*s]],color,2*s);}
function user(x,y,s,color=C.green){circle(x+30*s,y+18*s,14*s,'none',color,4*s);poly([[x+4*s,y+70*s],[x+4*s,y+53*s],[x+13*s,y+43*s],[x+47*s,y+43*s],[x+56*s,y+53*s],[x+56*s,y+70*s]],color,4*s);}
function chip(x,y,s,color=C.teal){rect(x+10*s,y+10*s,54*s,54*s,C.white,color,8*s,3*s);for(let i=0;i<3;i++){let t=(22+i*15)*s;poly([[x+t,y],[x+t,y+10*s]],color,3*s);poly([[x+t,y+64*s],[x+t,y+74*s]],color,3*s);poly([[x,y+t],[x+10*s,y+t]],color,3*s);poly([[x+64*s,y+t],[x+74*s,y+t]],color,3*s);}poly([[x+24*s,y+30*s],[x+35*s,y+30*s],[x+35*s,y+43*s],[x+48*s,y+43*s]],color,4*s);}
function chart(x,y,s,color=C.gray){poly([[x,y],[x,y+70*s],[x+85*s,y+70*s]],color,3*s);poly([[x+12*s,y+56*s],[x+30*s,y+47*s],[x+49*s,y+51*s],[x+67*s,y+26*s],[x+82*s,y+13*s]],color,4*s);for(const [a,b] of [[12,56],[30,47],[49,51],[67,26],[82,13]])circle(x+a*s,y+b*s,4*s,C.white,color,2*s);}
function phone(x,y,s){rect(x,y,111*s,180*s,C.white,C.ink,18*s,3*s);rect(x+35*s,y+7*s,41*s,7*s,C.ink,'none',4*s);for(let i=0;i<3;i++){rect(x+12*s,y+(39+i*38)*s,87*s,29*s,[C.orangeLight,'#F6E1CC',C.redLight][i],'none',5*s);text(x+19*s,y+(42+i*38)*s,74*s,24*s,`${i+1}  ${['경고','대피','위급'][i]}`,17*s,[C.orange,C.orange,C.red][i],true);}rect(x+40*s,y+166*s,32*s,4*s,C.line,'none',2*s);}
function bell(x,y,s,color=C.red){poly([[x+10*s,y+54*s],[x+14*s,y+44*s],[x+14*s,y+25*s],[x+21*s,y+12*s],[x+39*s,y+12*s],[x+46*s,y+25*s],[x+46*s,y+44*s],[x+50*s,y+54*s]],color,4*s);poly([[x+10*s,y+54*s],[x+50*s,y+54*s]],color,4*s);circle(x+30*s,y+65*s,6*s,color);poly([[x+30*s,y+5*s],[x+30*s,y+12*s]],color,4*s);}
function database(x,y,s,color=C.green){rect(x,y+10*s,66*s,56*s,C.white,color,2*s,3*s);p.items.push({kind:'ellipse',x,y,w:66*s,h:22*s,fill:C.pale,stroke:color,sw:3*s});poly([[x,y+36*s],[x+10*s,y+43*s],[x+56*s,y+43*s],[x+66*s,y+36*s]],color,2*s);}
function step(x,n,title,detail,color){text(x,283,315,38,`0${n}`,26,color,true);text(x,326,326,47,title,33,C.ink,true);lines(x,561,325,detail,24,C.muted,34);}

// 01: one page overview with a separate, non-blocking official-alert path.
page('봉화지기 전체 서비스 흐름','산불 자료를 받아, 각 사용자에게 필요한 행동 안내를 갱신합니다',1);
rect(72,206,1456,60,C.redLight,'none',14);bell(88,215,.50,C.red);text(132,219,260,34,'공식 긴급 경보',26,C.red,true);arrow(393,236,457,C.red,2.5);text(478,220,280,33,'발령 대상 확인',24,C.red,true);arrow(742,236,810,C.red,2.5);text(832,220,265,33,'원문 우선 전달',24,C.red,true);text(1138,222,355,30,'AI 분석과 독립적으로 처리',22,C.red,false,'right');
const xs=[72,454,836,1218];
step(xs[0],1,'자료 받기',['공식 경보·기상·관측·뉴스','확보 자료를 시나리오로 입력'],C.green);
step(xs[1],2,'근거 정리하기',['저장 자료와 인터넷 뉴스 검색','관련 근거와 출처를 정리'],C.teal);
step(xs[2],3,'나에게 맞추기',['위치·이동 능력·현재 상태','DB의 기본 지침과 규칙 적용'],C.orange);
step(xs[3],4,'안내 갱신하기',['경고·대피·위급과 행동 안내','새 입력에 맞춰 다시 평가'],C.red);
for(let i=0;i<4;i++)rect(xs[i],385,310,148,[C.pale,C.tealLight,C.orangeLight,C.redLight][i],'none',22);
stack(107,422,.97);text(202,423,162,35,'시연 자료',25,C.green,true);text(202,462,164,32,'수신 API',22,C.muted);
search(487,427,.95,C.teal);doc(582,416,.86,C.teal);text(652,434,100,33,'AI',30,C.teal,true);
user(870,425,.87,C.orange);text(947,438,45,42,'+',32,C.orange);database(1010,429,.88,C.orange);
phone(1248,399,.66);text(1341,424,177,33,'개인 안내',26,C.red,true);text(1341,464,173,31,'화면 업데이트',22,C.muted);
for(let i=0;i<3;i++)arrow(xs[i]+327,459,xs[i+1]-22,C.gray,3);
text(72,642,326,29,'K8s 자동 수집은 보류',19,C.green);
text(454,642,346,29,'AI 지연 시에도 정책 평가는 지속',19,C.teal);
text(1218,642,310,29,'앱 연동·단말 검증 진행 중',19,C.red);
rect(72,690,1456,128,C.white,C.line,18,1.5);
text(96,709,155,34,'실행 위치',23,C.muted,true);
text(282,708,420,35,'일반 서버',25,C.green,true);text(282,750,438,50,'수신 API · 처리 큐 · DB · 대응 규칙',22,C.muted);
text(794,708,320,35,'GPU 서버',25,C.teal,true);text(794,750,345,50,'임베딩과 Qwen 자료 정리',22,C.muted);
text(1195,708,274,35,'모바일 앱',25,C.orange,true);text(1195,750,280,50,'화면 표시 · 기기 음성 읽기',22,C.muted);
poly([[755,712],[755,786]],C.line,1.5);poly([[1154,712],[1154,786]],C.line,1.5);
p.notes='기준: 2026-11-01 KST 작업 트리 및 2026-10-31 배포 검증 기록. 현재 MVP는 simulation이며 실제 K8s 수집은 보류한다. 단계 2의 AI 처리는 개인 정책 평가의 필수 대기 조건이 아니다. 공식 원문과 고정 규칙은 GPU 없이도 처리된다. 서버는 Docker Compose로 PostgreSQL+pgvector, Redis/Celery와 분리 워커를 실행한다. 앱 통합과 실제 단말 검증은 진행 중이다. 실제 예측 모델은 앱에 미연결이며 FCM 실발신은 준비되지 않았다. 근거: deploy/compose/mvp.yaml; src/bonghwajigi/retrieval/pipeline.py; src/bonghwajigi/policy/service.py; src/bonghwajigi/events/urgent.py; docs/V2/delivery/mvp-server-runbook.md; docs/V2/delivery/mvp-server-evidence.json.';

// 02: the two running language models are a connected lane; prediction research is separate.
page('AI 모델별 역할','관련 근거를 찾고 정리하며, 최종 대응 단계는 서버의 고정 규칙이 결정합니다',2);
rect(72,207,958,48,C.pale,'none',12);text(93,215,915,32,'현재 연결된 자료 분석 흐름  ·  GPU 서버',23,C.green,true);
rect(1066,207,462,48,C.soft,'none',12);text(1087,215,418,32,'별도 예측 연구  ·  서비스 미연결',23,C.gray,true);
poly([[1048,281],[1048,653]],C.line,2);
search(78,285,.78,C.green);text(163,281,347,42,'근거 찾기',32,C.ink,true);text(163,327,350,30,'Qwen3-Embedding-0.6B',22,C.green,true);
arrow(498,313,541,C.green,3);
chip(566,281,.82,C.teal);text(655,281,365,42,'자료 정리하기',32,C.ink,true);text(655,327,360,30,'Qwen3-4B-Instruct-2507',22,C.teal,true);
chart(1082,282,.83,C.gray);text(1180,281,342,42,'접근 가능성 연구',31,C.ink,true);text(1180,327,340,30,'XGBoost',24,C.gray,true);
const cols=[72,566,1080];
const why=[['표현이 다른 자료에서도','같은 사건의 근거를 찾기 위해'],['여러 문서를 함께 읽고','사건 내용을 짧게 정리하기 위해'],['관측 숫자의 변화로','화재 접근을 추정하기 위해']];
cols.forEach((x,i)=>{text(x,385,430,27,'왜 필요한가',20,C.muted,true);lines(x,423,430,why[i],25,C.ink,34);poly([[x,510],[x+430,510]],C.line,1.5);});
text(72,532,428,29,'입력  관측 내용과 문서',22,C.green,true);lines(72,573,440,['출력  문서 벡터','DB가 유사한 근거와 출처를 검색'],23,C.ink,34);text(72,653,444,30,'인터넷 뉴스는 별도 검색으로 보강',20,C.muted);
text(566,532,438,29,'입력  검색된 근거와 원문',22,C.teal,true);lines(566,573,438,['출력  사건 요약과 인용 출처','참고 설명으로 보관'],23,C.ink,34);text(566,653,440,30,'개인 단계·행동을 직접 생성하지 않음',20,C.muted);
text(1080,532,438,29,'입력  정형 관측과 위치 자료',22,C.gray,true);lines(1080,573,438,['출력 후보  접근 시간·기간별 확률','현재 앱 제공값은 예측 불가'],23,C.ink,34);text(1080,653,440,30,'국내 검증과 보정 후 연결할 후보',20,C.muted);
rect(72,716,1456,104,C.ink,'none',18);text(98,734,1330,33,'최종 행동 안내는 일반 서버에서 결정',26,C.white,true);text(98,777,1320,30,'공식 경보  +  사용자 위치·상태  +  DB의 기본 행동 지침과 대응 규칙',24,'#DBE8DD');
p.notes='현재 활성 모델은 Qwen/Qwen3-Embedding-0.6B 및 Qwen/Qwen3-4B-Instruct-2507. 임베딩은 1024차원 벡터를 만들고 일반 서버 pgvector가 관련 자료를 검색한다. Google News RSS는 제목·설명·링크·발표 시각을 가져오는 별도 검색 어댑터다. Qwen 요약은 summary_review_status=not_reviewed로 보관하며 확률·대응 단계·행동을 결정하지 않는다. XGBoost는 현재 연구 산출물이 여러 개이며 GOFER 접근 시간 AFT의 최초 실험을 포함한다. 연구 결과는 국내 개인 피해 확률이 아니고 확률 보정과 실시간 당시 입력 검증이 미완료다. Qwen 요약을 숫자 모델의 검증된 입력으로 자동 변환하지 않는다. ELMFIRE 등 후속 실험은 별도 연구 도구이며 이 MVP 서비스 배치에 포함하지 않는다. 근거: src/bonghwajigi/retrieval/pipeline.py; src/bonghwajigi/retrieval/web_search.py; src/bonghwajigi/policy/integration.py; src/bonghwajigi/policy/service.py; docs/V2/delivery/gpu-model-readiness.md; docs/V2/delivery/korea-wildfire-improvement.md의 접근 시간 모델 첫 실행 절.';

// 03: urgent path and personalization loop have no crossing lines.
page('긴급 알림과 개인별 안내 갱신','공식 원문은 먼저 전달하고, 개인 안내는 변화가 생길 때마다 다시 평가합니다',3);
rect(72,207,1456,183,C.redLight,'none',22);text(98,226,800,36,'공식 경보 우선 처리',28,C.red,true);text(1097,229,400,30,'AI와 개인 정책 계산을 기다리지 않음',21,C.red,false,'right');
const ax=[103,461,818,1190];
text(ax[0],293,280,39,'공식 경보 수신',28,C.ink,true);text(ax[0],340,282,29,'발령·정정·해제',22,C.muted);
text(ax[1],293,280,39,'긴급 전용 처리',28,C.ink,true);text(ax[1],340,290,29,'분석 대기열과 분리',22,C.muted);
text(ax[2],293,280,39,'발령 대상 확인',28,C.ink,true);text(ax[2],340,300,29,'대상 구역과 사용자 위치',22,C.muted);
text(ax[3],293,300,39,'원문 우선 전달',28,C.red,true);text(ax[3],340,300,29,'수정·해제 이력도 반영',22,C.muted);
for(let i=0;i<3;i++)arrow(ax[i]+286,315,ax[i+1]-20,C.red,2.8);
text(74,435,1000,41,'개인별 안내 갱신',31,C.green,true);text(1100,441,425,31,'자료·위치·프로필·답변이 바뀌면 재평가',21,C.muted,false,'right');
const lx=[72,454,836,1218];
const fills=[C.pale,C.pale,C.orangeLight,C.tealLight];
for(let i=0;i<4;i++){rect(lx[i],499,310,166,fills[i],'none',18);circle(lx[i]+31,530,15,[C.green,C.green,C.orange,C.teal][i]);text(lx[i]+18,517,26,27,String(i+1),18,C.white,true,'center');}
text(96,558,266,35,'새 입력 반영',28,C.ink,true);text(96,607,270,30,'자료·위치·사용자 상태',22,C.muted);
text(478,558,266,35,'개인별 재평가',28,C.ink,true);text(478,607,270,30,'기본 지침과 고정 규칙',22,C.muted);
text(860,553,266,35,'대응 단계와 행동',28,C.ink,true);
pill(855,604,86,'1 경고','#F8E4AF',C.orange,19);pill(948,604,86,'2 대피','#F4D8BB',C.orange,19);pill(1041,604,86,'3 위급','#F0C6BE',C.red,19);
text(1242,558,265,35,'화면 갱신',28,C.ink,true);text(1242,607,265,30,'행동이 바뀌면 새 버전',22,C.muted);
for(let i=0;i<3;i++)arrow(lx[i]+328,581,lx[i+1]-20,C.green,3);
poly([[1373,682],[1373,727],[227,727],[227,683]],C.green,2.5);poly([[220,696],[227,682],[234,696]],C.green,2.5);
rect(477,709,645,38,C.paper);text(477,711,645,30,'주기적 만료 확인  +  사용자 위치·상태 변화 반영',22,C.green,true,'center');
text(73,779,1454,32,'화면: 변경 조회 API    /    단말 푸시: 모의 전송, Firebase 연결 전    /    119: 사용자가 직접 연결',22,C.muted);
p.notes='긴급 큐는 발령 원문과 관련성부터 처리하고 사용자 변경 이벤트 및 별도 delivery 큐를 만든다. 실제 FCM 발신은 아직 연결 전이므로 원문 우선 전달은 서버 조회·전달 요청까지의 구현을 뜻하며 잠금 화면 단말 수신을 완료했다고 주장하지 않는다. 같은 단계에서도 행동·근거·버전이 바뀌면 갱신하며 내용이 같으면 반복 생성하지 않는다. 현 Compose 정책 실행 대기 간격은 1초, 만료 점검 간격은 10초지만 종단 지연 보장이 아니므로 도표에는 수치를 싣지 않는다. 위치/상태 만료와 자료 부족은 확인 중이며 안전/0으로 해석하지 않는다. 위급은 지원이 필요한 상황이며 자동 119 신고를 하지 않는다. 사용자가 확정한 명칭은 1 경고, 2 대피, 3 위급. 근거: src/bonghwajigi/events/urgent.py; src/bonghwajigi/notifications/service.py; src/bonghwajigi/policy/three_stage.py; src/bonghwajigi/policy/service.py; src/bonghwajigi/api/mobile.py; deploy/compose/mvp.yaml; docs/V2/delivery/response-policy.md.';

// SVG export keeps the same authored elements, useful for non-PowerPoint editing.
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function svgItem(a){
 const stroke=`stroke="${a.stroke??'none'}" stroke-width="${a.sw??0}"${a.dash?' stroke-dasharray="8 6"':''}`;
 if(a.kind==='rect')return `<rect x="${a.x}" y="${a.y}" width="${a.w}" height="${a.h}" rx="${a.r}" fill="${a.fill}" ${stroke}/>`;
 if(a.kind==='ellipse')return `<ellipse cx="${a.x+a.w/2}" cy="${a.y+a.h/2}" rx="${a.w/2}" ry="${a.h/2}" fill="${a.fill}" ${stroke}/>`;
 if(a.kind==='poly')return `<${a.close?'polygon':'polyline'} points="${a.points.map(q=>q.join(',')).join(' ')}" fill="${a.fill}" ${stroke} stroke-linecap="round" stroke-linejoin="round"/>`;
 const x=a.x+(a.align==='center'?a.w/2:a.align==='right'?a.w:0),anchor=a.align==='center'?'middle':a.align==='right'?'end':'start';
 return `<text x="${x}" y="${a.y+a.size*.95}" font-family="${FONT}, sans-serif" font-size="${a.size}" font-weight="${a.bold?700:400}" fill="${a.color}" text-anchor="${anchor}">${esc(a.value)}</text>`;
}
const deck=Presentation.create({slideSize:{width:W,height:H}});
for(const [idx,pg] of pages.entries()){
 const slide=deck.slides.add();slide.background.fill=C.paper;slide.speakerNotes.text=pg.notes;
 for(const [k,a] of pg.items.entries()){
  const opts={name:`s${idx+1}-${k}-${a.kind}`,position:{left:a.x,top:a.y,width:a.w,height:a.h},fill:a.fill??'none',line:{fill:a.stroke??'none',width:a.sw??0,style:a.dash?'dashed':'solid'}};
  if(a.kind==='text'){
   const sh=slide.shapes.add({...opts,geometry:'textbox'});sh.text=a.value;
   sh.text.style={typeface:FONT,fontSize:a.size,bold:a.bold,color:a.color,alignment:a.align,verticalAlignment:'top',autoFit:'none',wrap:'none',insets:0};
  }else if(a.kind==='poly'){
   const xx=Math.min(...a.points.map(q=>q[0])),yy=Math.min(...a.points.map(q=>q[1]));
   const ww=Math.max(1,Math.max(...a.points.map(q=>q[0]))-xx),hh=Math.max(1,Math.max(...a.points.map(q=>q[1]))-yy);
   const commands=a.points.map((q,i)=>({[i?'lineTo':'moveTo']:{x:q[0]-xx,y:q[1]-yy}}));if(a.close)commands.push({close:{}});
   slide.shapes.add({...opts,geometry:'custom',position:{left:xx,top:yy,width:ww,height:hh},customPaths:[{width:ww,height:hh,commands}]});
  }else slide.shapes.add({...opts,geometry:a.kind==='ellipse'?'ellipse':a.r?'roundRect':'rect',...(a.r?{borderRadius:a.r}:{})});
 }
 const stem=['01-overview','02-ai-roles','03-alert-update'][idx];
 await fs.writeFile(path.join(out,stem+'.svg'),`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><title>${esc(pg.title)}</title>${pg.items.map(svgItem).join('\n')}</svg>`);
 const blob=await deck.export({slide,format:'png',scale:2});
 await fs.writeFile(path.join(out,stem+'.png'),new Uint8Array(await blob.arrayBuffer()));
 await fs.writeFile(path.join(out,stem+'.layout.json'),new Uint8Array(await (await slide.export({format:'layout'})).arrayBuffer()));
 console.log(`Rendered ${stem}`);
}
await (await PresentationFile.exportPptx(deck)).save(path.join(out,'candidate.pptx'));
await fs.writeFile(path.join(out,'source.json'),JSON.stringify(pages,null,2));
console.log('Created 3 editable slides and 3200×1800 PNG images.');
