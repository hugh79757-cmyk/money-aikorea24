// 실행: node scripts/vs-card-prompts.mjs --vs=월세전세
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_PATH = join(__dirname, '../public/benefits-clean.json');

const STYLE = `1080x1350 portrait (4:5 ratio) Instagram carousel card.
Pixel art illustration style (Stardew Valley / Korean retro game).
Deep navy gradient background (#0F1E3D to #1E3A5F).
Pixel-art Korean cityscape, hanok, modern apartments, cozy lit windows.
Korean Pretendard-style bold sans-serif overlay text in white and orange (#FFA552).
Atmospheric lighting. No real photos.
Bottom-right tiny watermark "persona.aikorea24.kr".
Top-right pill "@aikorea24" navy outline style.`;

const VS_MAP = {
  '월세전세': {
    title: '월세 지원 vs 전세 지원, 어느 게 유리?',
    left:  { label: '월세 지원', keywords: /월세/ },
    right: { label: '전세 지원', keywords: /전세|버팀목/ },
    conclusion: '소득 낮고 단기 거주 → 월세 / 목돈 있고 장기 거주 → 전세',
  },
  '청년도약': {
    title: '청년도약계좌 vs 청년내일채움공제',
    left:  { label: '청년도약계좌', keywords: /청년도약/ },
    right: { label: '청년내일채움공제', keywords: /내일채움/ },
    conclusion: '자유저축 선호 → 도약계좌 / 중소기업 재직 → 내일채움공제',
  },
  '창업취업': {
    title: '창업 지원 vs 취업 지원, 나에게 맞는 건?',
    left:  { label: '창업 지원', keywords: /창업/ },
    right: { label: '취업 지원', keywords: /취업|구직/ },
    conclusion: '아이디어·사업계획 있으면 → 창업 / 빠른 소득 필요 → 취업지원',
  },
};

const args = Object.fromEntries(process.argv.slice(2).filter(a=>a.startsWith('--')).map(a=>a.slice(2).split('=')));
const vsKey = args.vs ?? '월세전세';
const vs = VS_MAP[vsKey];
if (!vs) { console.error(`VS 키 오류. 가능: ${Object.keys(VS_MAP).join(', ')}`); process.exit(1); }

const data = JSON.parse(readFileSync(DATA_PATH, 'utf8'));
const cut = (s,n=55) => s ? s.replace(/\s+/g,' ').trim().slice(0,n)+(s.length>n?'…':'') : '';

const leftItems  = data.filter(d=>vs.left.keywords.test(d.name+d.purpose)).slice(0,3);
const rightItems = data.filter(d=>vs.right.keywords.test(d.name+d.purpose)).slice(0,3);

console.log('='.repeat(60));

// 슬라이드 1: 표지
console.log('[슬라이드 1 / 표지]');
console.log(`PROMPT:\n${STYLE}
Split screen pixel art: left side warm orange glow, right side cool blue glow.
Center text: "VS" (large white bold).
Left label (orange): "${vs.left.label}"
Right label (white): "${vs.right.label}"
Bottom text (white,medium): "${vs.title}"
`);

// 슬라이드 2: 왼쪽 옵션
console.log('[슬라이드 2 / ' + vs.left.label + ' 소개]');
const lDesc = leftItems.map((d,i)=>`${i+1}. ${d.name}: ${cut(d.content,40)}`).join(' / ');
console.log(`PROMPT:\n${STYLE}
Left-focused layout. Large orange header: "${vs.left.label}".
Bullet list (white text):\n${leftItems.map((d,i)=>`  ${i+1}. ${d.name} — ${cut(d.content,45)}`).join('\n')}
Bottom tag (orange pill): "이런 분께 추천"
`);

// 슬라이드 3: 오른쪽 옵션
console.log('[슬라이드 3 / ' + vs.right.label + ' 소개]');
console.log(`PROMPT:\n${STYLE}
Right-focused layout. Large white header: "${vs.right.label}".
Bullet list (white text):\n${rightItems.map((d,i)=>`  ${i+1}. ${d.name} — ${cut(d.content,45)}`).join('\n')}
Bottom tag (white pill): "이런 분께 추천"
`);

// 슬라이드 4: 비교표
console.log('[슬라이드 4 / 비교표]');
console.log(`PROMPT:\n${STYLE}
Pixel-art style comparison table (2 columns).
Column headers: "${vs.left.label}" (orange) | "${vs.right.label}" (white).
Rows: 지원금액 / 신청조건 / 지원기간 / 추천대상
Table has glowing grid lines. Background stays navy.
`);

// 슬라이드 5: 결론·CTA
console.log('[슬라이드 5 / 결론·CTA]');
console.log(`PROMPT:\n${STYLE}
Center text (three lines):
  Line1 (orange, large): "나에게 맞는 선택은?"
  Line2 (white, medium): "${vs.conclusion}"
  Line3 (white, small): "자세한 조건 → persona.aikorea24.kr/benefits"
Pixel-art character holding a signpost with two directions.
`);

// 쓰레드 훅
const hook = `${vs.left.label} vs ${vs.right.label}, 뭐가 유리할까? 🤔\n\n` +
  `✅ ${vs.left.label}: ${leftItems[0]?.name ?? '-'}\n` +
  `✅ ${vs.right.label}: ${rightItems[0]?.name ?? '-'}\n\n` +
  `${vs.conclusion}\n\n전체 비교 → persona.aikorea24.kr/benefits\n#정부지원금 #주거지원 #복지혜택`;
console.log('='.repeat(60));
console.log('[쓰레드 훅]');
console.log(hook);
console.log(`(${hook.length}자)`);
