import fs from 'fs';

const data = JSON.parse(fs.readFileSync('public/persona-stats.json', 'utf-8'));

// 여기만 수정해서 다양한 비교 실행
const KEY_A = '서울_남자_30대';
const KEY_B = '서울_여자_30대';

const A = data[KEY_A];
const B = data[KEY_B];

if (!A || !B) {
  console.log('키 없음. 사용 가능한 키 샘플:');
  console.log(Object.keys(data).filter(k => k.includes('서울')).slice(0, 20));
  process.exit(1);
}

const pct = (n, total) => total ? ((n / total) * 100).toFixed(1) : '0.0';
const top = (obj, n = 5) => Object.entries(obj).sort((a, b) => b[1] - a[1]).slice(0, n);

console.log(`\n=== ${KEY_A} (n=${A.total}) vs ${KEY_B} (n=${B.total}) ===\n`);

const fields = ['housing', 'education', 'family', 'jobs'];
for (const f of fields) {
  if (!A[f] || !B[f]) continue;
  console.log(`\n[${f.toUpperCase()}]`);
  const allKeys = new Set([...Object.keys(A[f]), ...Object.keys(B[f])]);
  const rows = [...allKeys].map(k => ({
    key: k,
    a: A[f][k] || 0,
    b: B[f][k] || 0,
    aPct: pct(A[f][k] || 0, A.total),
    bPct: pct(B[f][k] || 0, B.total),
  })).sort((x, y) => (y.a + y.b) - (x.a + x.b)).slice(0, 8);

  console.log(`${'항목'.padEnd(30)} ${KEY_A.padEnd(20)} ${KEY_B}`);
  for (const r of rows) {
    console.log(`${r.key.padEnd(30)} ${(r.aPct + '%').padEnd(8)}(${r.a})`.padEnd(50) + ` ${(r.bPct + '%').padEnd(8)}(${r.b})`);
  }
}

// 차이 큰 항목 자동 추출
console.log('\n\n=== 격차 TOP 10 (절대 % 차이) ===');
const diffs = [];
for (const f of fields) {
  if (!A[f] || !B[f]) continue;
  const allKeys = new Set([...Object.keys(A[f]), ...Object.keys(B[f])]);
  for (const k of allKeys) {
    const aPct = parseFloat(pct(A[f][k] || 0, A.total));
    const bPct = parseFloat(pct(B[f][k] || 0, B.total));
    diffs.push({ field: f, key: k, aPct, bPct, diff: Math.abs(aPct - bPct) });
  }
}
diffs.sort((x, y) => y.diff - x.diff).slice(0, 10).forEach(d => {
  console.log(`[${d.field}] ${d.key}: ${KEY_A.split('_')[1]} ${d.aPct}% vs ${KEY_B.split('_')[1]} ${d.bPct}% (차이 ${d.diff.toFixed(1)}p)`);
});
