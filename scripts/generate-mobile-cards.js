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
function sexLabel(key)  { return key.includes('여자') ? '여자' : '남자'; }
function ageLabel(key)  { const m = key.match(/(\d+대이상|\d+대|\d+)/); return m ? m[0] : ''; }

function makeSvg(key, data) {
  const total  = data.total || 1;
  const region = regionLabel(key);
  const sex    = sexLabel(key);
  const age    = ageLabel(key);

  const aptP = pct(data.housing,   ['아파트']);
  const eduP = pct(data.education, ['4년제 대학교','대학원']);

  // 배우자와 거주 관련 family 합산
  const fam  = data.family || {};
  const marCnt = Object.entries(fam)
    .filter(([k]) => k.includes('배우자'))
    .reduce((s,[,v])=>s+v, 0);
  const marP = total ? Math.round(marCnt/total*100) : 0;

  const uneP = pct(data.jobs, ['무직']);

  // 바 차트 항목
  const bars = [
    { label:'🏠 아파트 거주', value: aptP, color:'#4f8ef7' },
    { label:'🎓 대졸 이상',   value: eduP, color:'#10b981' },
    { label:'💍 배우자 거주', value: marP, color:'#f59e0b' },
    { label:'📋 무직',        value: uneP, color:'#ef4444' },
  ];

  // 바차트 SVG 생성 (y 시작점 480부터)
  const barH    = 22;   // 바 두께
  const barGap  = 68;   // 항목 간격
  const barMaxW = 320;  // 바 최대 너비
  const barX    = 40;   // 바 시작 x
  const labelY0 = 500;  // 첫 라벨 y

  const barsSvg = bars.map((b, i) => {
    const y     = labelY0 + i * barGap;
    const fillW = Math.round((b.value / 100) * barMaxW);
    return `
      <text x="${barX}" y="${y}" fill="#ffffff" font-size="20" font-weight="700" font-family="sans-serif">${b.label}</text>
      <rect x="${barX}" y="${y+8}" width="${barMaxW}" height="${barH}" rx="11" fill="rgba(255,255,255,0.15)"/>
      <rect x="${barX}" y="${y+8}" width="${fillW}"   height="${barH}" rx="11" fill="${b.color}"/>
      <text x="${barX + barMaxW + 12}" y="${y+24}" fill="#ffffff" font-size="20" font-weight="900" font-family="sans-serif">${b.value}%</text>
    `;
  }).join('');

  return `<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg">

    <!-- 상단 어두운 그라디언트 (배지+제목 가독성) -->
    <defs>
      <linearGradient id="topGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"   stop-color="#000000" stop-opacity="0.72"/>
        <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
      </linearGradient>
      <linearGradient id="botGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"   stop-color="#000000" stop-opacity="0"/>
        <stop offset="100%" stop-color="#000000" stop-opacity="0.85"/>
      </linearGradient>
    </defs>
    <rect width="${W}" height="220" fill="url(#topGrad)"/>
    <rect y="420" width="${W}" height="380" fill="url(#botGrad)"/>

    <!-- 배지 -->
    <rect x="20" y="24" width="260" height="36" rx="18" fill="#2563eb" opacity="0.92"/>
    <text x="150" y="47" text-anchor="middle" fill="#ffffff"
      font-size="17" font-weight="700" font-family="sans-serif">🇰🇷 엔비디아 700만 한국인 데이터</text>

    <!-- 제목 -->
    <text x="200" y="120" text-anchor="middle" fill="#ffffff"
      font-size="42" font-weight="900" font-family="sans-serif">${region} ${age}</text>
    <text x="200" y="168" text-anchor="middle" fill="#ffffff"
      font-size="32" font-weight="800" font-family="sans-serif">${sex}</text>
    <text x="200" y="208" text-anchor="middle" fill="rgba(255,255,255,0.80)"
      font-size="20" font-family="sans-serif">총 ${total.toLocaleString()}명 분석</text>

    <!-- 바차트 -->
    ${barsSvg}

    <!-- 워터마크 -->
    <text x="200" y="782" text-anchor="middle" fill="rgba(255,255,255,0.55)"
      font-size="16" font-family="sans-serif">persona.aikorea24.kr</text>
  </svg>`;
}

async function generateOne(key, data) {
  const srcPath = path.join(CARDS_DIR,  `${key}.jpg`);
  const outPath = path.join(MOBILE_DIR, `${key}.jpg`);
  if (!fs.existsSync(srcPath)) return false;

  try {
    // 600×600 → 400×800 중앙 크롭
    const bgBuf = await sharp(srcPath)
      .resize(W, H, { fit: 'cover', position: 'centre' })
      .toBuffer();

    // SVG 오버레이
    const svgBuf = await sharp(Buffer.from(makeSvg(key, data)))
      .resize(W, H)
      .png()
      .toBuffer();

    await sharp(bgBuf)
      .composite([{ input: svgBuf, left: 0, top: 0 }])
      .jpeg({ quality: 90 })
      .toFile(outPath);

    return true;
  } catch(e) {
    console.error(`❌ [${key}]`, e.message);
    return false;
  }
}

async function main() {
  const keys = Object.keys(stats);
  console.log(`🚀 총 ${keys.length}개 모바일 카드 생성 시작…`);
  let done = 0, skip = 0;

  for (let i = 0; i < keys.length; i += 50) {
    const results = await Promise.all(
      keys.slice(i, i+50).map(k => generateOne(k, stats[k]).catch(e => {
        console.error(`❌ [${k}]`, e.message); return false;
      }))
    );
    done += results.filter(Boolean).length;
    skip += results.filter(r => !r).length;
    process.stdout.write(`\r  진행: ${Math.min(i+50, keys.length)}/${keys.length}`);
  }

  console.log(`\n✅ 완료! 생성: ${done}개 / 스킵: ${skip}개`);
  console.log(`📂 출력: ${MOBILE_DIR}`);
}

main().catch(console.error);
