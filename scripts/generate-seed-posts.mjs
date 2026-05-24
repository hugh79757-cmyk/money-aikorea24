import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

const args = process.argv.slice(2);
const COUNT = parseInt(args.find(a => a.startsWith('--count='))?.split('=')[1] || '100');
const OUT_SQL = args.find(a => a.startsWith('--out='))?.split('=')[1] || `/tmp/seed_posts_${COUNT}.sql`;

console.log(`\n시드 글 생성 시작: ${COUNT}개 목표\n`);

const personaStats = JSON.parse(fs.readFileSync(path.join(ROOT, 'public/persona-stats.json'), 'utf8'));
const benefits     = JSON.parse(fs.readFileSync(path.join(ROOT, 'public/benefits-clean.json'), 'utf8'));
const personaKeys  = Object.keys(personaStats);
console.log(`페르소나 키: ${personaKeys.length}개 / 지원금: ${benefits.length}건`);

const REGION_WEIGHTS = {
  '서울':18,'경기':26,'인천':6,'부산':6,'대구':4,'광주':3,'대전':3,'울산':2,'세종':1,
  '강원':3,'충북':3,'충남':4,'전북':3,'전남':3,'경북':5,'경남':6,'제주':2
};

function weightedRegion() {
  const total = Object.values(REGION_WEIGHTS).reduce((a,b)=>a+b,0);
  let r = Math.random()*total;
  for (const [region,w] of Object.entries(REGION_WEIGHTS)) { r-=w; if(r<=0) return region; }
  return '서울';
}
function pickKey() {
  const region = weightedRegion();
  const m = personaKeys.filter(k=>k.startsWith(region+'_'));
  return m.length ? m[Math.floor(Math.random()*m.length)] : personaKeys[Math.floor(Math.random()*personaKeys.length)];
}
function rand(arr) { return arr[Math.floor(Math.random()*arr.length)]; }
function cleanField(s) {
  return (s||'').replace(/[\r\n]+/g,' ').replace(/\s+/g,' ').replace(/○/g,'').trim().slice(0,80);
}
function escape(s) { return (s||'').replace(/'/g,"''"); }

const NICK_ADJ  = ['행복한','따뜻한','조용한','바쁜','여유로운','고민많은','열심히','웃음꽃','평범한','소소한','긍정적인','성실한'];
const NICK_NOUN = ['직장인','주부','학생','프리랜서','자영업자','취준생','새내기','워킹맘','청년','시민','사회초년생'];
const NICK_SFX  = ['123','_kr','2024','99','_life','77','88','00','_daily','_today'];
function makeNick() {
  return rand(NICK_ADJ)+rand(NICK_NOUN)+rand(NICK_SFX);
}

function parseKey(key) {
  const [region,sexRaw,age] = key.split('_');
  return { region, sex: sexRaw==='남자'?'M':'F', sexLabel: sexRaw==='남자'?'남성':'여성', age };
}

function fmtAge(age) {
  const n = parseInt(age);
  if (n <= 9) return n + '살';
  const d = Math.floor(n / 10) * 10;
  if (d >= 70) return '70대 이상';
  return d + '대';
}
function getInfo(key) {
  const data = personaStats[key];
  const base = parseKey(key);
  const interests = ['재테크','건강관리','맛집탐방','독서','운동','여행','요리'];
  return { ...base, age: fmtAge(base.age),
    job: (base.age === '10대' ? '학생' : (data.jobs&&data.jobs[0]) || '직장인'),
    housing: (data.housing&&data.housing[0]) || '아파트',
    interest: rand(interests),
  };
}
function pickBenefit(region, ageStr) {
  const ageNum = parseInt(ageStr);
  const m = benefits.filter(b=>{
    const rOk = !b.regions||b.regions.includes('전국')||b.regions.includes(region);
    const aOk = !b.age_range||(ageNum>=b.age_range[0]&&ageNum<=b.age_range[1]);
    return rOk&&aOk;
  });
  return rand(m.length?m:benefits);
}
function randomDate30() {
  const now = Date.now(), ago30 = now-30*86400000;
  const ts = Math.random()<0.5 ? now-Math.random()*10*86400000 : ago30+Math.random()*20*86400000;
  return new Date(ts).toISOString().replace('T',' ').slice(0,19);
}
function pickCat(cats) {
  let r=Math.random();
  for(const c of cats){r-=c.r;if(r<=0)return c.s;}
  return cats[0].s;
}

const P_CATS = [{s:'자기소개',r:.20},{s:'일상',r:.25},{s:'고민',r:.25},{s:'질문',r:.15},{s:'후기',r:.15}];
const B_CATS = [{s:'신청후기',r:.25},{s:'질문',r:.30},{s:'정보공유',r:.25},{s:'탈락경험',r:.20}];

const PT = {
  '자기소개': [
    p=>`안녕하세요! ${p.region} 사는 ${p.age} ${p.sexLabel}입니다.\n${p.job} 일을 하고 있고요, 비슷한 분들이랑 정보 나누고 싶어서 가입했어요. 잘 부탁드립니다!`,
    p=>`${p.region}에 거주 중인 ${p.age}이에요. 직업은 ${p.job}이고 평소에 ${p.interest}에 관심이 많습니다. 좋은 정보 많이 얻어가고 싶네요. 반갑습니다.`,
    p=>`처음 글 올려봐요. ${p.region} ${p.age} ${p.sexLabel}입니다. ${p.job} 하면서 틈틈이 정부지원금 정보 찾아보고 있는데 쉽지 않더라고요. 잘 부탁드려요.`,
  ],
  '일상': [
    p=>`${p.region}도 요즘 날씨가 많이 더워졌네요. ${p.job} 출퇴근하는데 진짜 힘드네요.\n다들 건강 챙기세요!`,
    p=>`${p.age} ${p.sexLabel}으로 사는 게 요즘 팍팍하게 느껴져요. ${p.job} 수입으로 ${p.housing} 유지하면서 생활비 맞추려니 빠듯하네요. 같은 처지 분들 계신가요?`,
    p=>`오늘 ${p.job} 일이 바빠서 정신없이 하루 보냈어요. 저녁에 가족들이랑 밥 먹으면서 지원금 얘기 나왔는데, 생각보다 모르는 게 많더라고요.`,
  ],
  '고민': [
    p=>`${p.age} ${p.sexLabel}인데 요즘 ${p.job} 관련 고민이 생겨서요. 수입이 불안정해서 지원을 받을 수 있을지 찾아보는 중이에요. 비슷한 경험 있으신 분 조언 부탁드려요.`,
    p=>`${p.housing}에 살고 있는데 생활비 부담이 커요. ${p.age}에 이런 고민 하는 게 맞는 건지... 주변에 물어보기도 애매하고 여기서 솔직하게 얘기해봐요.`,
    p=>`솔직히 요즘 경제적으로 좀 어렵습니다. ${p.job} 하는데 수입이 들쭉날쭉해서 지원받을 수 있는 게 있는지 알아보고 있어요. ${p.region}에서 받을 수 있는 지원금 아시는 분?`,
  ],
  '질문': [
    p=>`${p.age} ${p.sexLabel}인데요, 혹시 ${p.job} 종사자들이 신청할 수 있는 지원금이 따로 있나요? ${p.region} 거주자인데 지역별로 다른 게 있는 것 같아서요.`,
    p=>`국민내일배움카드 신청하려고 하는데요, ${p.age} ${p.job}도 대상이 되는지 모르겠어요. 신청해본 분 계시면 절차 좀 알려주세요.`,
    p=>`${p.region}에서 ${p.age}에 신청 가능한 복지 혜택 총 정리된 거 어디서 볼 수 있나요? 복지로 들어가면 너무 많아서 헷갈려요.`,
  ],
  '후기': [
    p=>`지난달에 ${p.region}에서 청년지원금 받았어요. ${p.age}라 아슬아슬하게 대상이었는데 통과됐네요. 서류 준비가 좀 까다로웠지만 담당자분이 친절해서 잘 됐어요.`,
    p=>`${p.job} 하면서 직업훈련 신청했는데 생각보다 빨리 승인됐어요. ${p.region} 고용센터 빠르더라고요. ${p.age}도 충분히 받을 수 있으니 고민하지 말고 신청해보세요!`,
  ],
};

const BT = {
  '신청후기': [
    (p,b)=>`${b.name} 신청해봤어요. ${p.region} 사는 ${p.age} ${p.sexLabel}인데요. 서류 준비는 ${b.org}에서 안내를 잘 해줘서 어렵지 않았어요. 신청 방법: ${cleanField(b.method)}. 도움 되셨으면 좋겠어요!`,
    (p,b)=>`${b.name} 드디어 승인됐어요! ${p.age}인데 처음 신청해봤는데 생각보다 빠르게 처리됐네요. ${p.region} 사시는 분들 마감 전에 꼭 신청하세요. 마감: ${b.deadline}`,
  ],
  '질문': [
    (p,b)=>`${b.name} 신청 자격 문의드려요. ${p.age} ${p.job} 하고 있는데 대상이 되는지 궁금합니다. 신청해보신 분 경험 알려주시면 감사하겠어요!`,
    (p,b)=>`${b.name} 관련해서 여쭤볼게요. ${p.region}에서 신청하려면 어디로 가야 하나요? 홈페이지 들어가봤는데 너무 복잡하더라고요. 경험자분 알려주세요!`,
    (p,b)=>`${b.name} 마감이 "${b.deadline}"이라고 되어 있는데, 상시 신청이면 언제든 되는 건가요? 아니면 예산 소진되면 끝나는 건지 궁금해요.`,
  ],
  '정보공유': [
    (p,b)=>`${b.name} 정보 공유합니다! 대상: ${cleanField(b.target)}... 신청방법: ${cleanField(b.method)}. ${p.region} 거주 ${p.age} ${p.sexLabel}으로서 도움 될 것 같아 올려봐요.`,
    (p,b)=>`${b.name} 혜택 알고 계세요? ${p.age} ${p.job}이면 대부분 해당돼요. 지원 내용: ${cleanField(b.content)}... 자세한 건 ${b.org} 홈페이지 참고하세요!`,
  ],
  '탈락경험': [
    (p,b)=>`${b.name} 탈락했어요. ${p.age} ${p.job}인데 소득 기준 초과로 안 됐네요. ${p.region}이라 지역 제한도 있고... 비슷하게 탈락하신 분 있나요? 다른 지원금 추천해주세요.`,
    (p,b)=>`${b.name} 서류 다 냈는데 결국 탈락 통보 받았어요. ${p.age} ${p.sexLabel}입니다. 기준 미충족이었는데, 비슷한 경험 있으신 분 어떻게 하셨어요?`,
  ],
};

const COMMENT_T = [
  ()=>`저도 비슷한 경험 있어요! 도움이 됐으면 좋겠네요.`,
  ()=>`정보 감사합니다! 저도 알아봐야겠어요.`,
  ()=>`응원합니다! 잘 되시길 바랍니다.`,
  ()=>`저도 공감돼요. 힘내세요!`,
  ()=>`이런 정보 공유해주셔서 감사해요. 신청해봐야겠네요!`,
  ()=>`저는 작년에 비슷한 거 신청했는데 생각보다 빨리 처리됐어요.`,
  ()=>`문의는 고용센터나 복지로로 해보세요!`,
  ()=>`저도 궁금했던 부분인데 감사해요.`,
  ()=>`맞아요, 처음엔 복잡한데 익숙해지면 괜찮더라고요.`,
  ()=>`구체적으로 올려주셔서 도움이 많이 됐습니다!`,
];

// 글 생성
const nPersona = Math.floor(COUNT*0.6);
const nBenefit = COUNT - nPersona;
const posts = [];

for (let i=0; i<nPersona; i++) {
  const key=pickKey(), p=getInfo(key), cat=pickCat(P_CATS);
  const tmpl=rand(PT[cat]);
  const titleOpts = {
    '자기소개':[`안녕하세요, ${p.region} ${p.age} ${p.sexLabel}입니다`,`${p.region} 사는 ${p.age} ${p.sexLabel} 인사드려요`],
    '일상':[`${p.region} ${p.age} 일상 공유해요`,`오늘 하루 일상 기록`],
    '고민':[`${p.age} ${p.sexLabel}의 솔직한 고민`,`요즘 고민이 많아요...`],
    '질문':[`${p.job} 관련 지원금 있나요?`,`지원금 신청 자격 문의드려요`],
    '후기':[`지원금 신청 후기 공유합니다`,`신청 통과했어요! 후기 남겨요`],
  };
  posts.push({ nick:makeNick(), slug:key.replace(/_/g,'-').toLowerCase(), type:cat, region:p.region, sex:p.sex, age:p.age, title:rand(titleOpts[cat]), content:tmpl(p), board:'persona', date:randomDate30() });
}
for (let i=0; i<nBenefit; i++) {
  const key=pickKey(), p=getInfo(key), cat=pickCat(B_CATS), b=pickBenefit(p.region,p.age);
  const tmpl=rand(BT[cat]);
  const titleOpts = {
    '신청후기':[`${b.name} 신청 후기 공유해요`,`${b.name} 승인됐어요!`],
    '질문':[`${b.name} 신청 자격 문의`,`${b.name} 대상 되나요?`],
    '정보공유':[`${b.name} 정보 공유드립니다`,`${b.name} 꼭 확인해보세요`],
    '탈락경험':[`${b.name} 탈락 경험담`,`${b.name} 탈락했어요...`],
  };
  posts.push({ nick:makeNick(), slug:key.replace(/_/g,'-').toLowerCase(), type:cat, region:p.region, sex:p.sex, age:p.age, title:rand(titleOpts[cat]), content:tmpl(p,b), board:'benefit', date:randomDate30() });
}
posts.sort((a,b)=>b.date.localeCompare(a.date));

// 댓글 생성
const targetComments = Math.round(COUNT*(900/700));
const comments = [];
for (let i=0; i<posts.length && comments.length<targetComments; i++) {
  const n = Math.random()<0.45?0:(Math.random()<0.6?1:(Math.random()<0.7?2:3));
  for (let j=0; j<n && comments.length<targetComments; j++) {
    const base = new Date(posts[i].date).getTime();
    const cd = new Date(base+(j+1)*Math.random()*6*3600000).toISOString().replace('T',' ').slice(0,19);
    comments.push({ post_idx:i, nick:makeNick(), content:rand(COMMENT_T)(), date:cd });
  }
}

// SQL 출력
const lines = [
`-- Step E 시드 글 SQL (${COUNT}개)`,
`-- 생성: ${new Date().toISOString()}`,
`-- AI 페르소나 시드 전용 (user_id=0)`,
`PRAGMA foreign_keys=OFF;`,
`BEGIN TRANSACTION;`,
`INSERT OR IGNORE INTO users (id, kakao_id, name, provider, created_at) VALUES (0, 'seed-0', 'AI페르소나', 'seed', datetime('now'));`,
];

posts.forEach(p => {
  lines.push(`INSERT INTO persona_posts (user_id,persona_slug,persona_type,region,sex,age,title,content,board_type,created_at) VALUES (0,'${escape(p.slug)}','${escape(p.type)}','${escape(p.region)}','${p.sex}','${escape(p.age)}','${escape(p.title)}','${escape(p.content)}','${p.board}','${p.date}');`);
});


fs.writeFileSync(OUT_SQL, lines.join('\n'));

// 미리보기 JSON
const preview = {
  summary:{ total:posts.length, persona:posts.filter(p=>p.board==='persona').length, benefit:posts.filter(p=>p.board==='benefit').length, comments:comments.length },
  samples: posts.slice(0,5).map(p=>({board:p.board,nick:p.nick,title:p.title,content:p.content,date:p.date})),
  sample_comments: comments.slice(0,5),
};
const pvPath = OUT_SQL.replace('.sql','_preview.json');
fs.writeFileSync(pvPath, JSON.stringify(preview,null,2));

console.log(`\n완료!`);
console.log(`SQL: ${OUT_SQL} (${lines.length}줄)`);
console.log(`미리보기: ${pvPath}`);
console.log(`글: ${posts.length}개 / 댓글: ${comments.length}개`);
