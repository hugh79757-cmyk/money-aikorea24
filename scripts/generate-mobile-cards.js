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
  const total  = data.total || 1;
  const aptP   = pct(data.housing,   ['아파트']);
  const eduP   = pct(data.education, ['4년제 대학교','대학원']);
  const fam    = data.family || {};
  const marCnt = Object.entries(fam).filter(([k])=>k.includes('배우자')).reduce((s,[,v])=>s+v,0);
  const marP   = Math.round(marCnt/total*100);
  const uneP   = pct(data.jobs, ['무직']);

  const bars = [
    { label:'🏠 아파트 거주', value:aptP, color:'#4f8ef7' },
    { label:'🎓 대졸 이상',   value:eduP, color:'#10b981' },
    { label:'💍 배우자 거주', value:marP, color:'#f59e0b' },
    { label:'📋 무직',        value:uneP, color:'#ef4444' },
  ];

  const barX    = 32;
  const barMaxW = W - barX - 70;
  const barH    = 24;
  const labelY0 = 490;
  const barGap  = 72;

  const barsSvg = bars.map((b, i) => {
    const y  = labelY0 + i * barGap;
    const bw = Math.round((b.value / 100) * barMaxW);
    return `
      <text x="${barX}" y="${y}" fill="#ffffff" font-size="22" font-weight="700" font-family="sans-serif">${b.label}</text>
      <rect x="${barX}" y="${y+8}" width="${barMaxW}" height="${barH}" rx="12" fill="rgba(255,255,255,0.15)"/>
      <rect x="${barX}" y="${y+8}" width="${bw}" height="${barH}" rx="12" fill="${b.color}"/>
      <text x="${barX+barMaxW+10}" y="${y+26}" fill="#fff" font-size="22" font-weight="900" font-family="sans-serif">${b.value}%</text>`;
  }).join('');

  return `<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="tg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#000" stop-opacity="0.75"/>
        <stop offset="40%" stop-color="#000" stop-opacity="0"/>
      </linearGradient>
      <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="30%" stop-color="#000" stop-opacity="0"/>
        <stop offset="100%" stop-color="#000" stop-opacity="0.88"/>
      </linearGradient>
    </defs>
    <rect width="${W}" height="${H}" fill="url(#tg)"/>
    <rect width="${W}" height="${H}" fill="url(#bg)"/>

    <!-- 상단 배지 -->
    <rect x="20" y="22" width="${W-40}" height="38" rx="19" fill="#2563eb" opacity="0.92"/>
    <text x="${W/2}" y="47" text-anchor="middle" fill="#fff"
      font-size="16" font-weight="700" font-family="sans-serif">🇰🇷 엔비디아 700만 한국인 데이터</text>

    <!-- 제목 -->
    <text x="${W/2}" y="130" text-anchor="middle" fill="#fff"
      font-size="48" font-weight="900" font-family="sans-serif">${regionLabel(key)}</text>
    <text x="${W/2}" y="188" text-anchor="middle" fill="#fff"
      font-size="38" font-weight="800" font-family="sans-serif">${ageLabel(key)} ${sexLabel(key)}</text>
    <text x="${W/2}" y="228" text-anchor="middle" fill="rgba(255,255,255,0.80)"
      font-size="20" font-family="sans-serif">총 ${total.toLocaleString()}명 분석</text>

    <!-- 구분선 -->
    <line x1="32" y1="254" x2="${W-32}" y2="254" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>

    <!-- 핵심 수치 2×2 -->
    <rect x="20"       y="268" width="168" height="90" rx="12" fill="rgba(255,255,255,0.10)"/>
    <rect x="${W/2+4}" y="268" width="168" height="90" rx="12" fill="rgba(255,255,255,0.10)"/>
    <rect x="20"       y="368" width="168" height="90" rx="12" fill="rgba(255,255,255,0.10)"/>
    <rect x="${W/2+4}" y="368" width="168" height="90" rx="12" fill="rgba(255,255,255,0.10)"/>

    <text x="104"      y="306" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="13" font-family="sans-serif">🏠 아파트</text>
    <text x="104"      y="340" text-anchor="middle" fill="#fff" font-size="30" font-weight="900" font-family="sans-serif">${aptP}%</text>
    <text x="${W/2+88}" y="306" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="13" font-family="sans-serif">🎓 대졸이상</text>
    <text x="${W/2+88}" y="340" text-anchor="middle" fill="#fff" font-size="30" font-weight="900" font-family="sans-serif">${eduP}%</text>
    <text x="104"      y="406" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="13" font-family="sans-serif">💍 배우자</text>
    <text x="104"      y="440" text-anchor="middle" fill="#fff" font-size="30" font-weight="900" font-family="sans-serif">${marP}%</text>
    <text x="${W/2+88}" y="406" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="13" font-family="sans-serif">📋 무직</text>
    <text x="${W/2+88}" y="440" text-anchor="middle" fill="#fff" font-size="30" font-weight="900" font-family="sans-serif">${uneP}%</text>

    <!-- 바 차트 -->
    ${barsSvg}

    <!-- 워터마크 -->
    <text x="${W/2}" y="${H-16}" text-anchor="middle" fill="rgba(255,255,255,0.5)"
      font-size="14" font-family="sans-serif">persona.aikorea24.kr</text>
  </svg>`;
}

async function generateOne(key, data) {
  const srcPath = path.join(CARDS_DIR,  `${key}.jpg`);
  const outPath = path.join(MOBILE_DIR, `${key}.jpg`);
  if (!fs.existsSync(srcPath)) return false;

  try {
    const bgBuf  = await sharp(srcPath).resize(W, H, { fit:'cover', position:'centre' }).toBuffer();
    const svgBuf = await sharp(Buffer.from(makeSvg(key, data))).resize(W, H).png().toBuffer();

    await sharp(bgBuf)
      .composite([{ input: svgBuf, left:0, top:0 }])
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
  console.log(`🚀 총 ${keys.length}개 모바일 카드 생성 (400×800 세로형)…`);
  let done = 0, skip = 0;

  for (let i = 0; i < keys.length; i += 50) {
    const results = await Promise.all(
      keys.slice(i,i+50).map(k => generateOne(k, stats[k]).catch(e => { console.error(`❌[${k}]`,e.message); return false; }))
    );
    done += results.filter(Boolean).length;
    skip += results.filter(r=>!r).length;
    process.stdout.write(`\r  진행: ${Math.min(i+50,keys.length)}/${keys.length}`);
  }
  console.log(`\n✅ 완료! 생성: ${done}개 / 스킵: ${skip}개`);
}

main().catch(console.error);
