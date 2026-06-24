// 복지로 API 수집: 지자체(LcgvWelfarelist) + 중앙부처(NationalWelfarelistV001)
// 결과: public/welfare-local.json, public/welfare-central.json
import fs from 'node:fs';
import path from 'node:path';
import { XMLParser } from 'fast-xml-parser';

// .env → .env.common 폴백 로드
import '../lib/env-loader.ts';

const ROOT = path.resolve(import.meta.dirname, '..');
const KEY = process.env.DATA_GO_KR_API_KEY || '';
if (!KEY) { console.error('DATA_GO_KR_API_KEY not found'); process.exit(1); }

const parser = new XMLParser({ ignoreAttributes: true, parseTagValue: false });
const PAGE_SIZE = 500;
const SLEEP_MS = 150;
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function fetchPage(baseUrl, pageNo, extraParams = '') {
  const url = `${baseUrl}?serviceKey=${KEY}&pageNo=${pageNo}&numOfRows=${PAGE_SIZE}${extraParams}`;
  const res = await fetch(url);
  const text = await res.text();
  const json = parser.parse(text);
  const root = json.wantedList || {};
  const list = root.servList ? (Array.isArray(root.servList) ? root.servList : [root.servList]) : [];
  return { total: Number(root.totalCount || 0), list, raw: text.slice(0, 200) };
}

async function fetchAll(label, baseUrl, extraParams = '') {
  console.log(`\n=== ${label} 수집 시작 ===`);
  const first = await fetchPage(baseUrl, 1, extraParams);
  console.log(`총 ${first.total}건, 페이지당 ${PAGE_SIZE}`);
  if (first.total === 0) { console.error('응답 이상:', first.raw); return []; }
  const pages = Math.ceil(first.total / PAGE_SIZE);
  const all = [...first.list];
  for (let p = 2; p <= pages; p++) {
    process.stdout.write(`  page ${p}/${pages}... `);
    const { list } = await fetchPage(baseUrl, p, extraParams);
    all.push(...list);
    console.log(`누적 ${all.length}`);
    await sleep(SLEEP_MS);
  }
  console.log(`✅ ${label}: ${all.length}건 수집`);
  return all;
}

(async () => {
  // 1. 지자체
  const local = await fetchAll(
    '지자체 복지',
    'http://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist'
  );
  fs.writeFileSync(path.join(ROOT, 'public/welfare-local.json'), JSON.stringify(local, null, 2));
  console.log(`saved: public/welfare-local.json (${(fs.statSync(path.join(ROOT,'public/welfare-local.json')).size/1024).toFixed(0)} KB)`);

  // 2. 중앙부처 (srchKeyCode 필수)
  const central = await fetchAll(
    '중앙부처 복지',
    'http://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfarelistV001',
    '&srchKeyCode=003&callTp=L'
  );
  fs.writeFileSync(path.join(ROOT, 'public/welfare-central.json'), JSON.stringify(central, null, 2));
  console.log(`saved: public/welfare-central.json (${(fs.statSync(path.join(ROOT,'public/welfare-central.json')).size/1024).toFixed(0)} KB)`);

  console.log('\n=== 완료 ===');
})();
