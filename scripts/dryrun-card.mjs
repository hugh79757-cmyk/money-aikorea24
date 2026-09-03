// Dry-run: generate 1 card for visual inspection
import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = '/Users/twinssn/Projects/money-aikorea24';
const BG_DIR = path.join(ROOT, 'public/bg_img');
const STATS = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/persona-stats.json'), 'utf-8'));

const W = 600, H = 600;

function pct(obj, keys) {
  if (!obj) return 0;
  const t = Object.values(obj).reduce((s,v)=>s+v, 0);
  return t ? Math.round(keys.reduce((s,k)=>s+(obj[k]||0),0)/t*100) : 0;
}

function determineType(s, age) {
  const safe = {
    housing:   (s && s.housing)   || {},
    education: (s && s.education) || {},
    family:    (s && s.family)    || {},
    jobs:      (s && s.jobs)      || {},
  };
  const h = safe.housing, e = safe.education, f = safe.family, j = safe.jobs;
  if (age>=30 && age<=50 && pct(h,['아파트'])>=30) return {name:'대출이 월급보다 먼저 나가는 사람', emoji:'😮‍💨'};
  if (age<27) return {name:'아직 엄마밥이 제일 맛있는 사람', emoji:'🍚'};
  if (age>=50 && age<60 && pct(j,['자영업자'])>=15) return {name:'퇴직금으로 치킨집 고민하는 사람', emoji:'🍗'};
  if (age>=28 && age<=40 && pct(h,['전세'])>=20) return {name:'전세 계약서 들고 한숨 쉬는 사람', emoji:'📄'};
  if (age>=35 && age<=55 && pct(j,['임금근로자'])>=50) return {name:'월급은 그대로인데 물가만 오른 사람', emoji:'📈'};
  if (age>=30 && age<=45 && pct(h,['아파트'])>=25) return {name:'주말엔 쿠팡 박스 뜯는 게 낙인 사람', emoji:'📦'};
  if (age>=25 && age<=40) return {name:'적금 깨고 또 적금 드는 사람', emoji:'🏦'};
  if (age>=28 && age<=45 && pct(j,['임금근로자'])>=40) return {name:'카드값 걱정에 잠 못 자는 사람', emoji:'💳'};
  if (age>=45 && age<=58 && pct(j,['임금근로자'])>=45) return {name:'명퇴 걱정에 투잡 알아보는 사람', emoji:'💼'};
  if (age>=28 && age<=42 && pct(h,['월세'])>=20) return {name:'내 집 마련이 꿈인 사람', emoji:'🏠'};
  if (age>=45 && age<=65) return {name:'건강검진 결과지 보기 무서운 사람', emoji:'🏥'};
  if (age>=65) return {name:'손자 보며 노후를 즐기는 사람', emoji:'👴'};
  if (age>=52 && age<65) return {name:'자녀 결혼 비용이 두려운 사람', emoji:'💒'};
  if (age>=60) return {name:'은퇴 후 뭘 할지 모르는 사람', emoji:'🌅'};
  if (age>=62) return {name:'연금만으로는 부족한 사람', emoji:'📉'};
  if (age>=30 && pct(h,['아파트'])>=35) return {name:'지방에서 서울 부동산 구경하는 사람', emoji:'🏙️'};
  if (age>=50 && pct(j,['임금근로자'])>=55) return {name:'평생 월급쟁이로 살아온 사람', emoji:'👔'};
  if (age>=28 && age<=33 && pct(e,['4년제 대학교','대학원'])>=50) return {name:'스펙 쌓다 서른 된 사람', emoji:'🎓'};
  if (age>=24 && age<=30 && pct(j,['실업자'])>=15) return {name:'취업 준비 3년차인 사람', emoji:'📝'};
  if (age>=22 && age<=27) return {name:'첫 월급 받고 부모님께 용돈 드린 사람', emoji:'🧧'};
  if (age>=25 && age<=45) return {name:'내 월급이 평균인지 모르는 사람', emoji:'❓'};
  if (age>=22 && age<=32) return {name:'집도 차도 없는 자유로운 사람', emoji:'🎒'};
  return {name:'그냥 평범하게 살아가는 한국인', emoji:'🇰🇷'};
}

function shortRegion(r) {
  const map = {
    '경상북':'경북','경상남':'경남','충청북':'충북','충청남':'충남',
    '전라북':'전북','전라남':'전남'
  };
  return map[r] || r;
}

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

// Test key
const KEY = '서울_남자_35';
const d = STATS[KEY];

const region = KEY.split('_')[0];
const sex = KEY.split('_')[1];
const age = KEY.split('_')[2];
const total = d.total || 0;
const aptP = pct(d.housing, ['아파트']);
const eduP = pct(d.education, ['4년제 대학교','대학원']);
const fam = d.family || {};
const marCnt = Object.entries(fam).filter(([k])=>k.includes('배우자')).reduce((s,[,v])=>s+v,0);
const marP = Math.round(marCnt/(total||1)*100);
const uneP = pct(d.jobs, ["무직"]);
const typeObj = determineType(d, age);
const typeLabel = typeObj.emoji + " " + typeObj.name;

const incomeData = d.income || null;
const incomeVal = incomeData && incomeData.income_employed > 0 ? incomeData.income_employed : null;
const topPct = incomeData && incomeData.top_percentile > 0 ? incomeData.top_percentile : null;

const bars = [
  { label:'아파트 거주', value:aptP, color:'#4f8ef7' },
  { label:'대졸 이상',   value:eduP, color:'#10b981' },
  { label:'기혼',        value:marP, color:'#f59e0b' },
  { label:'무직',        value:uneP, color:'#ef4444' },
];

console.log('\n=== DRY-RUN: 서울_남자_35 ===');
console.log(`total: ${total.toLocaleString()}명`);
console.log(`아파트: ${aptP}% | 대졸: ${eduP}% | 기혼: ${marP}% | 무직: ${uneP}%`);
console.log(`income_employed: ${incomeVal}만원 | top_percentile: ${topPct}%`);
console.log(`type: ${typeLabel}`);
console.log(`\n=== SVG Bar Layout ===`);
console.log(`startY=380, gap=44`);

if (incomeVal && topPct) {
  bars.push({ label:'월 소득', value:topPct, color:'#D97706', suffix:incomeVal.toLocaleString() + '만원' });
}

const bX = 28, bW = W - 56, bH = 16;
const startY = 380, gap = 44;

bars.forEach((b, i) => {
  const y = startY + i * gap;
  const fw = Math.round((b.value / 100) * bW);
  const bottomY = y + 6 + bH;
  console.log(`  Bar #${i+1} [${b.label}]: y=${y}, bottom=${bottomY}, value=${b.value}%, fw=${fw}px, suffix="${b.suffix || b.value + '%'}"`);
});

// Last bar bottom edge
const lastY = startY + (bars.length - 1) * gap;
const lastBottom = lastY + 6 + bH;
console.log(`\n  Last bar bottom edge: ${lastBottom}px`);
console.log(`  Space to card bottom (600): ${600 - lastBottom}px`);
console.log(`  Footer text at y=588`);
const footerSpace = 588 - lastBottom;
console.log(`  Footer위젯 공간: ${footerSpace}px (${footerSpace >= 20 ? '✅ 충분' : '⚠️ 부족'})`);

// Generate actual JPG for visual inspection
const bX2 = bX, bW2 = bW, bH2 = bH, startY2 = startY, gap2 = gap;

const barsSvg = bars.map((b, i) => {
  const y = startY2 + i * gap2;
  const fw = Math.round((b.value / 100) * bW2);
  return `
    <text x="${bX2}" y="${y}" fill="#fff" font-size="18" font-weight="700" font-family="sans-serif">${b.label}</text>
    <text x="${W-bX2}" y="${y}" text-anchor="end" fill="${b.color}" font-size="18" font-weight="900" font-family="sans-serif">${b.suffix || b.value + '%'}</text>
    <rect x="${bX2}" y="${y+6}" width="${bW2}" height="${bH2}" rx="8" fill="rgba(255,255,255,0.18)"/>
    <rect x="${bX2}" y="${y+6}" width="${fw}" height="${bH2}" rx="8" fill="${b.color}"/>`;
}).join('');

const svg = `<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="tg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#000" stop-opacity="0.55"/>
      <stop offset="35%" stop-color="#000" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="30%" stop-color="#000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0.88"/>
    </linearGradient>
  </defs>
  <rect width="${W}" height="${H}" fill="url(#tg)"/>
  <rect width="${W}" height="${H}" fill="url(#bg)"/>
  <rect x="16" y="16" width="${W-32}" height="34" rx="17" fill="#2563eb" opacity="0.92"/>
  <text x="${W/2}" y="39" text-anchor="middle" fill="#fff" font-size="14" font-weight="700" font-family="sans-serif">엔비디아 700만 한국인 데이터</text>
  <text x="${bX2}" y="290" fill="#fff" font-size="28" font-weight="900" font-family="sans-serif">${shortRegion(region)} ${age} ${sex} ${total.toLocaleString()}명 분석</text>
  <text x="${bX2}" y="318" fill="rgba(255,255,255,0.75)" font-size="16" font-family="sans-serif">나와 같은 조건의 한국인 현실</text>
  <rect x="${bX2-4}" y="328" width="${typeLabel.length * 18 + 24}" height="32" rx="16" fill="rgba(255,255,255,0.18)"/>
  <text x="${bX2 + 8}" y="350" fill="#fff" font-size="17" font-weight="700" font-family="sans-serif">${typeLabel}</text>
  ${barsSvg}
  <text x="${W/2}" y="${H-12}" text-anchor="middle" fill="rgba(255,255,255,0.45)" font-size="12" font-family="sans-serif">persona.aikorea24.kr/my-persona</text>
</svg>`;

const bgFile = getBg(region, age);
const bgPath = path.join(BG_DIR, bgFile);
const outPath = '/tmp/dryrun-card-seoul_man_35.jpg';

await sharp(bgPath)
  .resize(W, H, { fit:'cover', position:'centre' })
  .composite([{ input: Buffer.from(svg), top:0, left:0 }])
  .jpeg({ quality: 88 })
  .toFile(outPath);

console.log(`\n✅ JPG saved to: ${outPath}`);
