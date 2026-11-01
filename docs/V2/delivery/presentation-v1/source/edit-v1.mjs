import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
const modules=process.env.BONGHWA_ARTIFACT_MODULES;
const require=createRequire(path.join(modules,'package.json'));
const {PresentationFile,FileBlob}=require('@oai/artifact-tool');
const input=process.argv[2],out=path.resolve(process.argv[3]);
await fs.mkdir(out,{recursive:true});
const deck=await PresentationFile.importPptx(await FileBlob.load(input));
const inspected=(await deck.inspect({kind:'shape,textbox,table,image',maxChars:2000000})).ndjson;
const recs=inspected.split('\n').filter(Boolean).map(l=>JSON.parse(l));
const P={navy:'#062F5B',ink:'#20324C',muted:'#65707C',paper:'#F7F6F2',line:'#CCD3D8',gold:'#FFB515',blue:'#E9EFF5',lightGold:'#FFF1C9'};
const cmap={'#172E2A':P.ink,'#132A44':P.ink,'#1C7055':P.navy,'#146C76':'#245B80','#61736F':P.muted,'#71817D':P.muted,'#DAE3DC':P.line,'#E7F1E8':P.blue,'#E6F1F2':P.blue,'#EBEFEB':P.blue,'#EAEDEB':P.blue,'#F7F8F5':P.paper,'#000000':P.ink};
const font='Apple SD Gothic Neo';
const seen=new Set();
for(const r of recs){
 if(!r.id.startsWith('sh/')||seen.has(r.id))continue;seen.add(r.id);
 const s=deck.resolve(r.id);
 if(r.fillColor&&cmap[r.fillColor])s.fill=cmap[r.fillColor];
 if(r.lineColor&&cmap[r.lineColor])s.line={fill:cmap[r.lineColor],width:r.lineWidth??1,style:'solid'};
 if(r.style){
  s.text.style={typeface:r.slideIndex===0&&/team =|print\(/.test(r.text??'')?'Courier New':font,...(cmap[r.style.color]?{color:cmap[r.style.color]}:{})};
 }
}
// Presentation fields and body objects remain in place; no removed headings are recreated.
const titleTexts=['10월27일 구룡 마을 화재, 남일이 아닙니다.','개인 상황에 맞춘 재난대응 추천 서비스','모바일 핵심 기능','봉화지기 전체 서비스 흐름','긴급 알림과 개인별 안내 갱신','AI 모델별 역할','직접 개발 범위 · 실행 환경 · 검증','팀원별 역할 분담','외부 자원 활용 내역','기대 효과와 확장 가능성'];
const sourceText=(s)=>recs.filter(r=>r.slideIndex===s&&r.kind==='textbox');
const match=(slide,text)=>{
 const r=sourceText(slide).find(r=>(r.text??'').trim()===text.trim());
 if(!r)throw new Error(`Missing source text on ${slide+1}: ${text}`);
 return deck.resolve(r.id);
};
for(let i=1;i<11;i++){
 deck.slides.items[i].background.fill=P.paper;
 const t=match(i,titleTexts[i-1]);
 t.position={left:64,top:48,width:1152,height:58};
 t.text.style={typeface:font,fontSize:36,bold:true,color:P.navy,wrap:'none',autoFit:'none',insets:0};
 const titleRec=sourceText(i).find(r=>(r.text??'').trim()===titleTexts[i-1]);
 const sub=sourceText(i).filter(r=>r.id!==titleRec?.id&&r.position?.top<170&&r.position?.width>350&&r.text?.trim()).sort((a,b)=>a.position.top-b.position.top)[0];
 if(sub&&i!==3){const x=deck.resolve(sub.id);x.position={...sub.position,left:64,top:112,width:1152,height:48};x.text.style={typeface:font,fontSize:19,color:P.muted,wrap:'square',autoFit:'none',insets:0};}
 for(const r of sourceText(i)){
  const raw=(r.text??'').trim();
  if(/^\d{2}$/.test(raw)&&r.position?.top>640){let x=deck.resolve(r.id);x.position={left:1148,top:680,width:68,height:26};x.text.style={typeface:font,fontSize:16,bold:true,color:P.navy,alignment:'right',insets:0};}
  if(raw.includes('CODYSSEY AI HACKATHON')&&r.position?.top>640){let x=deck.resolve(r.id);x.position={...r.position,left:64,top:681,height:25};x.text.style={typeface:font,fontSize:11,color:P.muted,insets:0};}
 }
}
// Keep existing yellow emphasis shapes, soften only the large service panel.
for(const r of recs){
 if(r.id.startsWith('sh/')&&r.fillColor==='#FFB515'&&r.slideIndex===2&&r.position.width>300&&r.position.height>100)deck.resolve(r.id).fill=P.lightGold;
 if(r.id.startsWith('sh/')&&r.slideIndex>=4&&r.slideIndex<=7&&r.position?.height<=5&&r.position?.top<160&&r.fillColor)deck.resolve(r.id).fill=P.gold;
}
// Extend the original role text boxes so every existing sentence can wrap naturally.
for(const r of sourceText(8)){
 if(r.position.top>360&&r.position.top<435&&r.position.width<300){const s=deck.resolve(r.id);s.position={...r.position,top:375,height:76};s.text.style={typeface:font,fontSize:16.5,wrap:'square',autoFit:'none',insets:0};}
 if(r.position.top>450&&r.position.top<530&&r.position.width<300){const s=deck.resolve(r.id);s.position={...r.position,top:468,height:119};s.text.style={typeface:font,fontSize:16.5,wrap:'square',autoFit:'none',insets:0};}
}
// Slide 10: edit the existing native table, adding rows inside that same object.
const resourceRows=[
 ['구분','명칭','용도','라이선스·이용 조건'],
 ['오픈소스','Qwen3-4B-Instruct-2507\nQwen3-Embedding-0.6B','근거 자료 요약·정리\n1024차원 벡터 생성·유사 근거 검색','Apache-2.0 (두 모델)'],
 ['오픈소스','XGBoost 3.4.1','산불 접근 예측 연구·학습 (서비스 미연결)','Apache-2.0'],
 ['오픈소스','PyTorch 2.11.0+cu128\nTransformers 4.57.6 · Sentence Transformers 5.7.0','GPU 추론 실행\nQwen 모델 로딩·텍스트 생성·임베딩','PyTorch: BSD-3-Clause\nTransformers 계열: Apache-2.0'],
 ['오픈소스','FastAPI 0.162.0 · SQLAlchemy 2.1.6\nCelery 5.6.3 · Uvicorn 0.54.0','HTTP API·DB 처리\n긴급·분석·전달 작업 실행','FastAPI·SQLAlchemy: MIT\nCelery·Uvicorn: BSD-3-Clause'],
 ['오픈소스','PostgreSQL 16 · pgvector DB 확장','사건·정책·프로필·벡터 저장 및 검색','PostgreSQL License'],
 ['기타','Redis 7.4','작업 대기열·Celery broker·AOF 저장','RSALv2 또는 SSPLv1'],
 ['외부 API','NAVER Maps Android SDK\n@mj-studio/react-native-naver-map 2.9.1','앱 배경 지도 표시\nReact Native 지도 연결','NAVER Maps 약관·SDK 저작권 고지\n연결 라이브러리: MIT'],
 ['오픈소스','expo-speech-recognition 58.0.1\nAndroid SpeechRecognizer','단말 한국어 음성 인식\n인식한 텍스트를 서버 대화 API로 전달','연결 라이브러리: MIT\n단말 인식 서비스 이용 조건 별도'],
 ['외부 API','Google News RSS','산불 기사 제목·설명·URL 검색','Google 약관 및 언론사별 저작권'],
 ['기타','NAVER Cloud · NVIDIA L4/CUDA 12.8\nDocker Engine/Moby · Docker Compose','일반·GPU 서버 운영 및 모델 실행\nAPI·DB·워커 컨테이너 배포','Ncloud 약관 / NVIDIA CUDA EULA\nMoby·Compose: Apache-2.0'],
 ['외부 API','기상청 API Hub · GK2A FF','국내 위성 화재 관측·학습 자료 확보','인증·활용 승인 필요, 제품별 재이용 조건 확인'],
 ['기타','NOAA GOES · ISD · GFS','화재 관측·과거 기상·예보 연구 자료','NOAA NODD 조건·출처 표시·가공 여부 구분'],
 ['기타','Next Day Wildfire Spread v2\nGOFER v0.2','초기 일별 산불 확산 학습\n시간별 산불 경계·접근 시간 연구','CC BY 4.0 (두 데이터셋)\n저자·원문·판본·가공 사실 표시'],
 ['외부 API','Open-Meteo GFS Forecast API','국내 지형 확산 연구용 기상예보 수신','데이터: CC BY 4.0 / 무료 API: 비상업 용도'],
 ['기타','ELMFIRE 1.1','바람·지형 기반 산불 확산 시뮬레이션 연구','AGPL-3.0 + Commons Clause·상업 별도 계약'],
 ['기타','정책브리핑 · 안전한TV · 국민안전24\n대한민국정부상징체 R','공식 경보·산불 행동요령의 근거\n앱 로고 서체','정책브리핑 텍스트: 공공누리 1유형\n안전한TV·서체: 4유형 / 국민안전24: 조건 미확인'],
 ['사전 보유 코드','해당 없음','행사 전 보유 코드 미반입','해당 없음'],
];
const rowHeights=resourceRows.map((row,r)=>r===0?28:row.some(v=>v.includes('\n'))?33:22);
const tr=recs.find(r=>r.kind==='table'&&r.slideIndex===9);const table=deck.resolve(tr.id);
if(resourceRows.length>tr.rows)table.insertRows({index:tr.rows,count:resourceRows.length-tr.rows});
table.position={left:64,top:150,width:1152,height:490};
table.columnTracks=[{mode:'fixed',value:106},{mode:'fixed',value:360},{mode:'fixed',value:316},{mode:'fixed',value:370}];
table.styleOptions={headerRow:true,bandedRows:false,firstColumn:false};
table.borders.assign({fill:P.line,width:0.6,style:'solid'});
table.cells.block({row:0,column:0,rowCount:resourceRows.length,columnCount:4}).assign({margins:{left:8,right:8,top:1,bottom:1},anchor:'center'});
for(let r=0;r<resourceRows.length;r++){
 table.rows[r].height=rowHeights[r];
 for(let c=0;c<4;c++){
  const cell=table.getCell(r,c);cell.value=resourceRows[r][c];cell.fill=r===0?P.navy:r%2?'#FFFFFF':'#F0F3F6';
  cell.text.style={typeface:font,fontSize:r===0?18:12,lineSpacing:1,bold:r===0||c===0,color:r===0?'#FFFFFF':c===0?P.navy:P.ink,wrap:'square',autoFit:'none',verticalAlignment:'middle',insets:{left:8,right:8,top:1,bottom:1}};
 }
}
match(9,'실제 사용·시연 기록 기준 / 상세 출처와 조건은 별도 명세').text='서비스·학습·연구에 활용한 주요 자원과 라이선스';
const details=match(9,'상세: 서버 docs/V2/delivery/external-resources-and-licenses.md');
details.text='상세 출처·조건: external-resources-and-licenses.md';details.position={left:64,top:651,width:1152,height:20};details.text.style={typeface:font,fontSize:11,color:P.muted,insets:0};
// Slide 11: reuse all existing headings, text blocks and dividers.
const replacements=[
 ['개인 안내의 유용성은 실제 재난 현장에서 추가 검증이 필요합니다.','개인별 대응과 빠른 알림, 서비스 안정성과 재난 대응 범위 확대'],
 ['BEFORE','기대 효과 01'],['정보가 흩어진 상황','10m 이내에서도 사람마다 다른 대응'],
 ['같은 경보를 받아도\n내 위치·이동 제약에 맞는\n다음 행동을 고르기 어려움','10m 이내에 있는 사람도 각자의 상황이 다르므로\n개인별 상태를 반영한 대응 절차를 제시'],
 ['AFTER','기대 효과 02'],['원문 + 개인 행동 안내','재난 발생 전 알림으로 대피 시간 확보'],
 ['공식 경보는 그대로 전달하고\n규칙이 개인 대응 단계를 제시','재난이 발생하기 전에 위험을 빠르게 알려\n사용자가 대피할 시간을 확보'],
 ['기대 효과·확인 지표','확장 가능성 · 클라우드와 대피지도'],
 ['행동 이해도·전달 성공률·중복 감소','클라우드 간 하이브리드 전략으로 장애에 대응\n대피지도를 3D로 구현해 더 정확한 대피경로 제시'],
 ['현재 확인한 범위','확장 가능성 · 위치와 사용자 모드'],
 ['서버 모의 시나리오와 앱 웹 화면','추가 위치 등록으로 안내 대상 위치 확대\n시니어·색약자 버전 등 사용자에 맞는 모드 제공'],
 ['실제 검증 결과','재난 범위 확대'],
 ['모의 사용자 재생·GPU 단절 경로·자동 검사 확인','산불에서 홍수·지진·전쟁·태풍 등으로 확장'],
];
for(const [old,value]of replacements){const s=match(10,old);s.text=value;s.text.style={typeface:font};}
for(const [old]of replacements){
 const r=sourceText(10).find(r=>(r.text??'').trim()===old.trim());const s=deck.resolve(r.id);
 if(['같은 경보를 받아도\n내 위치·이동 제약에 맞는\n다음 행동을 고르기 어려움','공식 경보는 그대로 전달하고\n규칙이 개인 대응 단계를 제시'].includes(old)){s.position={...r.position,top:335,height:92};s.text.style={fontSize:20,color:P.ink,wrap:'square',insets:0};}
 if(['행동 이해도·전달 성공률·중복 감소','서버 모의 시나리오와 앱 웹 화면'].includes(old)){s.position={...r.position,top:540,height:64};s.text.style={fontSize:18,color:P.ink,wrap:'square',insets:0};}
 if(['기대 효과·확인 지표','현재 확인한 범위'].includes(old))s.text.style={fontSize:21,bold:true,color:P.navy,insets:0};
 if(['실제 검증 결과','모의 사용자 재생·GPU 단절 경로·자동 검사 확인'].includes(old))s.text.style={fontSize:old==='실제 검증 결과'?22:18,color:P.navy,insets:0};
}
deck.slides.items[9].speakerNotes.text='출처: external-resources-and-licenses.md, 사용자 제공, 최종 작성일 2026-11-01. 모델·코드·데이터·서비스 약관은 별도 조건을 따른다. 상세 버전·고정 revision·원문 링크·고지 조건은 해당 명세 참조. Qwen 공식 모델: https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 및 https://huggingface.co/Qwen/Qwen3-Embedding-0.6B. GOFER: Liu et al. (2025), v0.2, doi:10.5281/zenodo.14642378. 기상예보: Weather data by Open-Meteo.com, https://open-meteo.com/, CC BY 4.0, 연구용 가공. 대한민국정부상징체: 문화체육관광부, https://www.mcst.go.kr/site/s_about/intro/symbol.jsp, 공공누리 제4유형. 전이 패키지와 조사·미사용 자원의 전체 조건은 별도 명세 참조.';
deck.slides.items[10].speakerNotes.text='기대 효과와 향후 확장 방향. 10m는 가까운 사람 간 개인별 상황 차이를 설명하는 예시다. 재난 발생 전 알림은 조기 위험 예측을 통한 서비스 목표다. 하이브리드 클라우드, 3D 대피경로, 추가 위치, 접근성 모드, 재난 범위 확장은 향후 계획이다.';
await (await PresentationFile.exportPptx(deck)).save(path.join(out,'candidate.pptx'));
for(const [i,s]of deck.slides.items.entries()){
 await fs.writeFile(path.join(out,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await(await deck.export({slide:s,format:'png',scale:1.5})).arrayBuffer()));
 console.log(`rendered ${i+1}`);
}
await fs.writeFile(path.join(out,'after-inspect.ndjson'),(await deck.inspect({kind:'shape,textbox,image,table,slide',maxChars:2000000})).ndjson);
console.log('candidate ready');
