// Reuse the existing presentation's title, spacing, font, palette and footer.
// Usage: BONGHWA_ARTIFACT_MODULES=<node_modules> node build-tech-stack.mjs <private-build-dir>
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const require=createRequire(path.join(process.env.BONGHWA_ARTIFACT_MODULES,'package.json'));
const {PresentationFile,FileBlob}=require('@oai/artifact-tool');
const sourceDir=path.dirname(fileURLToPath(import.meta.url));
const template=path.resolve(sourceDir,'../output/bonghwajigi-architecture.pptx');
const out=path.resolve(process.argv[2]);
await fs.mkdir(out,{recursive:true});
const deck=await PresentationFile.importPptx(await FileBlob.load(template));
deck.slides.keep([0]);
const slide=deck.slides.items[0];
const inspected=await deck.inspect({kind:'shape,textbox',maxChars:1000000});
const records=inspected.ndjson.split('\n').filter(Boolean).map(l=>JSON.parse(l));
const keep=new Set(['s1-1-text','s1-2-text']);
deck.delete([...new Set(records.filter(r=>r.id?.startsWith('sh/')&&!keep.has(r.name)).map(r=>r.id))]);
const find=name=>slide.shapes.items.find(s=>s.name===name);
find('s1-1-text').text='직접 개발 범위 · 실행 환경 · 검증';
find('s1-2-text').text='서버 API와 앱 화면을 구현하고, 통합 동작을 검증하고 있습니다';
const C={ink:'#172E2A',muted:'#61736F',line:'#DAE3DC',green:'#1C7055',pale:'#E7F1E8',teal:'#146C76',tealLight:'#E6F1F2',orange:'#B96928',orangeLight:'#F8EDDD',soft:'#EBEFEB',paper:'#F7F8F5'};
let n=0;
function rect(x,y,w,h,fill,r=0){return slide.shapes.add({name:`tech-${++n}`,geometry:r?'roundRect':'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0},...(r?{borderRadius:r}:{})});}
function text(x,y,w,h,value,size=25,color=C.ink,bold=false){
 const shape=slide.shapes.add({name:`tech-${++n}-text`,geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 shape.text=value;shape.text.style={typeface:'Apple SD Gothic Neo',fontSize:size,bold,color,alignment:'left',verticalAlignment:'top',autoFit:'none',wrap:'none',insets:0};return shape;
}
slide.background.fill=C.paper;
rect(72,179,55,5,C.green);
text(72,853,1300,26,'봉화지기  /  CODYSSEY AI HACKATHON 2026',18,C.muted);
text(1495,847,40,32,'06',20,C.muted);
text(72,218,700,42,'기술 스택과 역할',30,C.ink,true);
const cols=[
 ['일반 서버','API와 대응 판단',['자료 수신·사용자 API','개인별 정책과 작업 관리'],C.green,C.pale],
 ['GPU 서버','Qwen 모델 실행',['근거 검색용 벡터 생성','자료 요약·출처 정리'],C.teal,C.tealLight],
 ['PostgreSQL','사건과 근거 보관',['사건·프로필·상태 저장','기본 지침·벡터 검색'],C.green,C.pale],
 ['Redis','작업 대기열',['긴급·분석 작업 분리','처리 대기와 재시도'],C.teal,C.tealLight],
 ['앱','사용자 화면',['프로필·상황 입력','행동 안내·화면 갱신'],C.orange,C.orangeLight],
];
for(const [i,[title,role,details,color,fill]] of cols.entries()){
 const x=72+i*296;
 rect(x,282,272,245,fill,20);
 text(x+22,309,230,45,title,31,color,true);
 text(x+22,367,230,36,role,24,C.ink,true);
 details.forEach((t,j)=>text(x+22,438+j*35,230,33,t,22,C.muted));
}
rect(72,578,690,2,C.line);rect(826,578,702,2,C.line);
text(72,601,650,44,'팀 직접 개발',30,C.green,true);
text(72,663,690,39,'서버 API · 중복 방지 · 긴급 큐 · 정책 갱신',26,C.ink);
text(72,707,690,39,'앱 화면과 서버 API 연결',26,C.ink);
text(826,601,680,44,'검증 범위',30,C.teal,true);
text(826,663,702,39,'모의 사용자 3명 재생 · GPU 단절 시 긴급 경로',25,C.ink);
text(826,707,702,39,'서버 자동 검사 82건 · 앱 14건',27,C.ink,true);
text(826,756,702,30,'검사 건수는 제공 자료 기준',19,C.muted);
slide.speakerNotes.text='내용 출처: 사용자가 제공한 /Users/hongyongjae/Downloads/ppt_8.webp. 기술 구성 5개와 직접 개발·검증 항목을 보존했다. 검증 수치 서버 82건/앱 14건과 모의 사용자 3명은 해당 원본 자료의 수치이며 이번 작업의 새 측정 또는 최신 검사 수치가 아니다. GPU의 검색 역할은 벡터 생성과 Qwen 요약으로 명확히 표현했다. 근거: docs/V2/delivery/presentation-architecture.md, src/bonghwajigi/retrieval/pipeline.py. 디자인 참조: docs/V2/delivery/architecture-slides/output/bonghwajigi-architecture.pptx의 1번 슬라이드. 실제 예측·Firebase 발신·지도는 이 슬라이드에서 완료로 주장하지 않는다.';
await fs.writeFile(path.join(out,'tech-stack.png'),new Uint8Array(await (await deck.export({slide,format:'png',scale:2})).arrayBuffer()));
await fs.writeFile(path.join(out,'tech-stack.layout.json'),await (await slide.export({format:'layout'})).text());
await (await PresentationFile.exportPptx(deck)).save(path.join(out,'candidate.pptx'));
console.log('Created one editable slide and 3200x1800 preview');
