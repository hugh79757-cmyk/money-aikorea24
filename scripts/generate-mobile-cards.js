import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const CARDS_DIR  = path.join(__dirname, '../public/cards');
const MOBILE_DIR = path.join(__dirname, '../public/cards-mobile');
const STATS_JSON = path.join(__dirname, '../public/persona-stats.json');

const W = 400, H = 800;

const stats = JSON.parse(fs.readFileSync(STATS_JSON, 'utf-8'));
if (!fs.existsSync(MOBILE_DIR)) fs.mkdirSync(MOBILE_DIR, { recursive: true });

function pct(obj, keys) {
  const t = Object.values(obj).reduce((s,v)=>s+v, 0);
  return t ? Math.round(keys.reduce((s,k)=>s+(obj[k]||0),0)/t*100) : 0;
}
function regionLabel(key) {
  const map = {서울:'서울',부산:'부산',대구:'대구',인천:'인천',광주:'광주',대전:'대전',울산:'울산',세종:'세종',경기:'경기',강원:'강원',충북:'충북',충남:'충남',전북:'전북',전남:'전남',경북:'경북',경남:'경남',제주:'제주'};
  return map[key.split('_')[0]] || key.split('_')[0];
}
function sexLabel(key) { return key.includes('여자') ? '여자' : '남자'; }
function ageLabel(key) { const m = key.match(/(\d+대이상|\d+대|\d+)/); return m ? m[0] : ''; }

function makeSvg(key, data) {
  const total = data.total || 1;
  const aptP  = pct(data.housing,   ['아파트']);
  const eduP  = pct(data.education, ['4년제 대학교','대학원']);
  const fam   = data.family || {};
  const marCnt = Object.entries(fam).filter(([k])=>k.includes('배우자')).reduce((s,[,v])=>s+v,0);
  const marP  = Math.round(marCnt/total*100);
  const uneP  = pct(data.jobs, ['무직']);

  // 바차트: x=24 시작, 너비=W-48=352, 퍼센트는 바 위에 표시
  const bars = [
    { label:'🏠 아파트 거주', value:aptP, color:'#4f8ef7' },
    { label:'🎓 대졸 이상',   value:eduP, color:'#10b981' },
    { label:'💍 배우자 거주', value:marP, color:'#f59e0b' },
    { label:'📋 무직',        value:uneP, color:'#ef4444' },
  ];

  const bX     = 24;
  const bW     = W - 48;
  const bH     = 20;
  const startY = 500;
  const gap    = 68;

  const barsSvg = bars.map((b, i) => {
    const y  = startY + i * gap;
    const fw = Math.round((b.value / 100) * bW);
    return `
      <text x="${bX}" y="${y}" fill="#fff" font-size="19" font-weight="700" font-family="sans-serif">${b.label}</text>
      <text x="${W - bX}" y="${y}" text-anchor="end" fill="${b.color}" font-size="19" font-weight="900" font-family="sans-serif">${b.value}%</text>
      <rect x="${bX}" y="${y+6}" width="${bW}" height="${bH}" rx="10" fill="rgba(255,255,255,0.15)"/>
      <rect x="${bX}" y="${y+6}" width="${fw}" height="${bH}" rx="10" fill="${b.color}"/>`;
  }).join('');

  return `<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="tg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#000" stop-opacity="0.72"/>
        <stop offset="38%" stop-color="#000" stop-opacity="0"/>
      </linearGradient>
      <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="28%" stop-color="#000" stop-opacity="0"/>
        <stop offset="100%" stop-color="#000" stop-opacity="0.90"/>
      </linearGradient>
    </defs>
    <rect width="${W}" height="${H}" fill="url(#tg)"/>
    <rect width="${W}" height="${H}" fill="url(#bg)"/>

    <!-- 배지 -->
    <rect x="20" y="20" width="${W-40}" height="36" rx="18" fill="#2563eb" opacity="0.92"/>
    <text x="${W/2}" y="44" text-anchor="middle" fill="#fff"
      font-size="15" font-weight="700" font-family="sans-serif">🇰🇷 엔비디아 700만 한국인 데이터</text>

    <!-- 제목 -->
    <text x="${W/2}" y="126" text-anchor="middle" fill="#fff"
      font-size="52" font-weight="900" font-family="sans-serif">${regionLabel(key)}</text>
    <text x="${W/2}" y="182" text-anchor="middle" fill="#fff"
      font-size="36" font-weight="800" font-family="sans-serif">${ageLabel(key)} ${sexLabel(key)}</text>
    <text x="${W/2}" y="220" text-anchor="middle" fill="rgba(255,255,255,0.78)"
      font-size="18" font-family="sans-serif">총 ${total.toLocaleString()}명 분석</text>

    <!-- 구분선 -->
    <line x1="24" y1="244" x2="${W-24}" y2="244" stroke="rgba(255,255,255,0.25)" stroke-width="1"/>

    <!-- 핵심 수치 2×2 -->
    <rect x="16"        y="256" width="178" height="100" rx="14" fill="rgba(255,255,255,0.10)"/>
    <rect x="${W/2+6}"  y="256" width="178" height="100" rx="14" fill="rgba(255,255,255,0.10)"/>
    <rect x="16"        y="364" width="178" height="100" rx="14" fill="rgba(255,255,255,0.10)"/>
    <rect x="${W/2+6}"  y="364" width="178" height="100" rx="14" fill="rgba(255,255,255,0.10)"/>

    <text x="105"       y="296" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="14" font-family="sans-serif">🏠 아파트</text>
    <text x="105"       y="338" text-anchor="middle" fill="#fff" font-size="34" font-weight="900" font-family="sans-serif">${aptP}%</text>
    <text x="${W/2+95}" y="296" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="14" font-family="sans-serif">🎓 대졸이상</text>
    <text x="${W/2+95}" y="338" text-anchor="middle" fill="#fff" font-size="34" font-weight="900" font-family="sans-serif">${eduP}%</text>
    <text x="105"       y="404" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="14" font-family="sans-serif">💍 배우자</text>
    <text x="105"       y="446" text-anchor="middle" fill="#fff" font-size="34" font-weight="900" font-family="sans-serif">${marP}%</text>
    <text x="${W/2+95}" y="404" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="14" font-family="sans-serif">📋 무직</text>
    <text x="${W/2+95}" y="446" text-anchor="middle" fill="#fff" font-size="34" font-weight="900" font-family="sans-serif">${uneP}%</text>

    <!-- 바차트 -->
    ${barsSvg}

    <!-- 워터마크 -->
    <text x="${W/2}" y="${H-14}" text-anchor="middle" fill="rgba(255,255,255,0.45)"
      font-size="13" font-family="sans-serif">persona.aikorea24.kr</text>
  </svg>`;
}

async function generateCard(key, data) {
  const src = path.join(CARDS_DIR, `${key}.jpg`);
  const out = path.join(MOBILE_DIR, `${key}.jpg`);
  if (!fs.existsSync(src)) return false;

  const svgBuf = Buffer.from(makeSvg(key, data));

  await sharp(src)
    .resize(W, H, { fit:'cover', position:'centre' })
    .composite([{ input: svgBuf, top:0, left:0 }])
    .jpeg({ quality:90 })
    .toFile(out);
  return true;
}

const keys   = Object.keys(stats);
const total  = keys.length;
let done = 0, skip = 0;
const BATCH  = 50;

console.log(`🚀 총 ${total}개 모바일 카드 생성 (400×800 세로형)…`);

for (let i = 0; i < total; i += BATCH) {
  const batch = keys.slice(i, i + BATCH);
  const results = await Promise.all(batch.map(k => generateCard(k, stats[k])));
  results.forEach(ok => ok ? done++ : skip++);
  console.log(`  진행: ${Math.min(i+BATCH, total)}/${total}`);
}

console.log(`✅ 완료! 생성: ${done}개 / 스킵: ${skip}개`);
console.log(`📁 ${MOBILE_DIR}`);
