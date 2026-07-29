import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const MOBILE_DIR = path.join(__dirname, '../public/cards-mobile');
const BG_DIR     = path.join(__dirname, '../public/bg_img');
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
function getBg(region, age) {
  if (region === '서울' || region === '경기' || region === '인천') {
    if (age < 30) return 'bg_seoul_20.jpeg';
    if (age < 40) return 'bg_seoul_30.jpeg';
    if (age < 50) return 'bg_gyeonggi_40.jpeg';
    if (age < 70) return 'bg_seoul_60.jpeg';
    return 'bg_seoul_60.jpeg';
  }
  if (region === '부산' || region === '대구' || region === '울산' ||
      region === '경상남' || region === '경상북') return 'bg_busan_all.jpeg';
  if (region === '강원') return 'bg_gangwon_all.jpeg';
  if (region === '제주') return 'bg_jeju_all.jpeg';
  if (age >= 50) return 'bg_rural_50.jpeg';
  return 'bg_rural_50.jpeg';
}

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
    { label:'아파트 거주', value:aptP, color:'#4f8ef7' },
    { label:'대졸 이상',   value:eduP, color:'#10b981' },
    { label:'배우자 거주', value:marP, color:'#f59e0b' },
    { label:'무직',        value:uneP, color:'#ef4444' },
  ];

  const incomeData = data.income || null;
  const incomeVal = incomeData && incomeData.income_employed > 0 ? incomeData.income_employed : null;
  const topPct = incomeData && incomeData.top_percentile > 0 ? incomeData.top_percentile : null;

  const bX     = 24;
  const bW     = W - 48;
  const bH     = 20;
  const startY = 465;
  const gap    = 58;

  const barsSvg = bars.map((b, i) => {
    const y  = startY + i * gap;
    const fw = Math.round((b.value / 100) * bW);
    return `
      <text x="${bX}" y="${y}" fill="#fff" font-size="19" font-weight="700" font-family="sans-serif">${b.label}</text>
      <text x="${W - bX}" y="${y}" text-anchor="end" fill="${b.color}" font-size="19" font-weight="900" font-family="sans-serif">${b.value + '%'}</text>
      <rect x="${bX}" y="${y+6}" width="${bW}" height="${bH}" rx="10" fill="rgba(255,255,255,0.15)"/>
      <rect x="${bX}" y="${y+6}" width="${fw}" height="${bH}" rx="10" fill="${b.color}"/>`;
  }).join('');

  // Income highlight — standalone, visually distinct from ratio bars
  let incomeSvg = '';
  if (incomeVal && topPct) {
    const secY = startY + bars.length * gap + 8; // = 465 + 232 + 8 = 705
    incomeSvg = `
    <line x1="${bX}" y1="${secY - 25}" x2="${W-bX}" y2="${secY - 25}" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>
    <text x="${W/2}" y="${secY + 8}" text-anchor="middle" fill="#D97706" font-size="24" font-weight="900" font-family="sans-serif">상위 ${topPct}%</text>
    <text x="${W/2}" y="${secY + 36}" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="13" font-family="sans-serif">월소득 약 ${incomeVal.toLocaleString()}만원 · 전체 취업자 기준</text>`;
  }

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
      font-size="15" font-weight="700" font-family="sans-serif">엔비디아 700만 한국인 데이터</text>

    <!-- 제목 -->
    <text x="${W/2}" y="126" text-anchor="middle" fill="#fff"
      font-size="52" font-weight="900" font-family="sans-serif">${regionLabel(key)}</text>
    <text x="${W/2}" y="182" text-anchor="middle" fill="#fff"
      font-size="36" font-weight="800" font-family="sans-serif">${ageLabel(key)} ${sexLabel(key)}</text>
    <text x="${W/2}" y="220" text-anchor="middle" fill="rgba(255,255,255,0.78)"
      font-size="18" font-family="sans-serif">총 ${total.toLocaleString()}명 분석</text>

    <!-- 구분선 -->
    <line x1="24" y1="244" x2="${W-24}" y2="244" stroke="rgba(255,255,255,0.25)" stroke-width="1"/>

    <!-- 가로 바차트 (4개 비율 지표) -->
    ${barsSvg}
    ${incomeSvg}

    <!-- 워터마크 -->
    <text x="${W/2}" y="${H-14}" text-anchor="middle" fill="rgba(255,255,255,0.45)"
      font-size="13" font-family="sans-serif">persona.aikorea24.kr</text>
  </svg>`;
}

async function generateCard(key, data) {
  const out = path.join(MOBILE_DIR, `${key}.jpg`);
  const parts = key.split('_');
  const region = parts[0];
  const age = parseInt(parts[2]) || 30;
  const bgFile = getBg(region, age);
  const bgPath = path.join(BG_DIR, bgFile);

  const svgBuf = Buffer.from(makeSvg(key, data));

  await sharp(bgPath)
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
