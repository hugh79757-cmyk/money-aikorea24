import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const CARDS_DIR  = path.join(__dirname, '../public/cards');
const MOBILE_DIR = path.join(__dirname, '../public/cards-mobile');
const STATS_JSON = path.join(__dirname, '../public/persona-stats.json');

const CARD_W = 800, CARD_H = 400, THUMB_W = 400, THUMB_H = 400, INFO_W = 400, INFO_H = 400;

const stats = JSON.parse(fs.readFileSync(STATS_JSON, 'utf-8'));

if (!fs.existsSync(MOBILE_DIR)) fs.mkdirSync(MOBILE_DIR, { recursive: true });

function pct(count, total) {
  return total > 0 ? Math.round((count / total) * 100) : 0;
}

function regionLabel(key) {
  const map = {서울:'서울',부산:'부산',대구:'대구',인천:'인천',광주:'광주',대전:'대전',울산:'울산',세종:'세종',경기:'경기',강원:'강원',충북:'충북',충남:'충남',전북:'전북',전남:'전남',경북:'경북',경남:'경남',제주:'제주'};
  return map[key.split('_')[0]] || key.split('_')[0];
}
function sexLabel(key)  { return key.includes('여자') ? '여' : '남'; }
function ageLabel(key)  { const m = key.match(/(\d+대이상|\d+대|\d+)/); return m ? m[0] : ''; }

function makeSvg(key, data) {
  const total   = data.total || 1;
  const housing = data.housing || {};
  const edu     = data.education || {};
  const jobs    = data.jobs || {};
  const marital = data.marital || {};

  // 아파트 비율
  const aptP = pct(housing['아파트'] || 0, total);

  // 대졸 비율 (4년제 + 대학원)
  const uniCnt = (edu['4년제 대학교'] || 0) + (edu['대학원'] || 0);
  const eduP   = pct(uniCnt, total);

  // 배우자 있음 비율 (marital 또는 family에서)
  const family = data.family || {};
  const marCnt = (family['배우자와 거주'] || 0) + (family['배우자·자녀와 거주'] || 0)
               + (family['배우자·손자녀와 거주'] || 0) + (family['배우자·자녀·부모와 거주'] || 0)
               + (family['배우자·편부모와 거주'] || 0) + (family['배우자·친인척과 거주'] || 0)
               + (family['배우자·자녀·아버지와 거주'] || 0) + (family['배우자·미혼 형제자매와 거주'] || 0);
  const marP   = pct(marCnt, total);

  // 무직 비율
  const uneP = pct(jobs['무직'] || 0, total);

  const barColor = '#4f8ef7', barBg = '#1e2a4a', textColor = '#ffffff', subColor = '#a0b4d6';

  function bar(label, value, y) {
    const bw = Math.round((value / 100) * 300);
    return `
      <text x="20" y="${y}" fill="${subColor}" font-size="13" font-family="sans-serif">${label}</text>
      <rect x="20" y="${y+6}" width="300" height="14" rx="7" fill="${barBg}"/>
      <rect x="20" y="${y+6}" width="${bw}"  height="14" rx="7" fill="${barColor}"/>
      <text x="326" y="${y+18}" fill="${textColor}" font-size="13" font-weight="bold" font-family="sans-serif">${value}%</text>`;
  }

  return `<svg width="${INFO_W}" height="${INFO_H}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#0f172a"/>
        <stop offset="100%" stop-color="#1e3a5f"/>
      </linearGradient>
    </defs>
    <rect width="${INFO_W}" height="${INFO_H}" fill="url(#bg)"/>
    <rect x="12" y="12" width="376" height="28" rx="14" fill="#2563eb" opacity="0.85"/>
    <text x="200" y="31" text-anchor="middle" fill="#fff" font-size="12" font-weight="bold" font-family="sans-serif">엔비디아 700만 한국인 데이터</text>
    <text x="200" y="78" text-anchor="middle" fill="#fff" font-size="22" font-weight="900" font-family="sans-serif">${regionLabel(key)} ${ageLabel(key)} ${sexLabel(key)}자</text>
    <text x="200" y="104" text-anchor="middle" fill="${subColor}" font-size="13" font-family="sans-serif">총 ${total.toLocaleString()}명 분석</text>
    <line x1="20" y1="118" x2="380" y2="118" stroke="#2563eb" stroke-width="1" opacity="0.5"/>
    ${bar('🏠 아파트 거주',    aptP, 140)}
    ${bar('🎓 대학 졸업 이상', eduP, 200)}
    ${bar('💍 배우자와 거주',  marP, 260)}
    ${bar('📋 무직',           uneP, 320)}
    <text x="200" y="388" text-anchor="middle" fill="${subColor}" font-size="11" opacity="0.7" font-family="sans-serif">persona.aikorea24.kr</text>
  </svg>`;
}

async function generateOne(key, data) {
  const srcPath = path.join(CARDS_DIR,  `${key}.jpg`);
  const outPath = path.join(MOBILE_DIR, `${key}.jpg`);
  if (!fs.existsSync(srcPath)) return false;

  const thumbBuf = await sharp(srcPath).resize(THUMB_W, THUMB_H, { fit: 'cover' }).toBuffer();
  const infoBuf  = await sharp(Buffer.from(makeSvg(key, data))).resize(INFO_W, INFO_H).png().toBuffer();

  await sharp({ create: { width: CARD_W, height: CARD_H, channels: 3, background: { r:15, g:23, b:42 } } })
    .composite([{ input: thumbBuf, left: 0, top: 0 }, { input: infoBuf, left: THUMB_W, top: 0 }])
    .jpeg({ quality: 88 })
    .toFile(outPath);

  return true;
}

async function main() {
  const keys = Object.keys(stats);
  console.log(`🚀 총 ${keys.length}개 모바일 카드 생성 시작…`);
  let done = 0, skip = 0;

  for (let i = 0; i < keys.length; i += 50) {
    const results = await Promise.all(keys.slice(i, i+50).map(k => generateOne(k, stats[k]).catch(e => { console.error(`❌ [${k}]`, e.message); return false; })));
    done += results.filter(Boolean).length;
    skip += results.filter(r => !r).length;
    process.stdout.write(`\r  진행: ${Math.min(i+50, keys.length)}/${keys.length}`);
  }

  console.log(`\n✅ 완료! 생성: ${done}개 / 스킵: ${skip}개`);
}

main().catch(console.error);
