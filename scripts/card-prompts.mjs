import fs from 'fs';
const benefits = JSON.parse(fs.readFileSync('public/benefits-clean.json','utf8'));
const N = parseInt(process.argv[2] || '5');

const today = new Date();
function daysLeft(deadline) {
  if (!deadline) return null;
  const m = String(deadline).match(/(\d{4})[-.](\d{1,2})[-.](\d{1,2})/);
  if (!m) return null;
  const d = new Date(+m[1], +m[2]-1, +m[3]);
  return Math.ceil((d - today) / 86400000);
}

const ranked = benefits
  .map(b => ({...b, _d: daysLeft(b.deadline)}))
  .filter(b => b._d !== null && b._d > 0 && b._d <= 30)
  .sort((a,b) => a._d - b._d)
  .slice(0, N);

const STYLE = `1080x1080 square Instagram card. Minimalist Korean design. Background: warm cream (#FFF8EE). Accent: deep brown (#6B4226) and soft orange (#FFA552). Korean Pretendard-style sans-serif font, heavy weight for titles. No people, no realistic photos. Flat vector style. Generous whitespace.`;

ranked.forEach((b, i) => {
  const name = b.name || '지원금';
  const amount = b.amount || b.support || '지원금';
  const target = (b.target || '').replace(/\s+/g,' ').slice(0,150);
  const method = (b.method || b.how || '').replace(/\s+/g,' ').slice(0,150);
  const org = b.org || '관할기관';

  console.log(`\n========== [${i+1}/${N}] ${name} (D-${b._d}) ==========\n`);

  console.log(`### 슬라이드 1 (후킹)\n${STYLE} Top-left badge: "⏰ D-${b._d}". Center: huge bold Korean text "${name}". Bottom subtitle: "지금 신청 안 하면 끝". Bottom-right tiny logo "@persona.aikorea24".\n`);

  console.log(`### 슬라이드 2 (혜택)\n${STYLE} Top label: "지원 내용". Center: large Korean text "${amount}". Bottom: "${org}". Flat coin icon in corner.\n`);

  console.log(`### 슬라이드 3 (대상자)\n${STYLE} Top heading: "이런 분이 받아요". Center: Korean text block with check-mark bullets:\n"${target}"\nThree separate bullet points with flat check-mark icons.\n`);

  console.log(`### 슬라이드 4 (신청방법)\n${STYLE} Top heading: "신청 방법". Center: numbered timeline with circles (1,2,3):\n"${method}"\nVertical step layout, deep brown numbered circles.\n`);

  console.log(`### 슬라이드 5 (CTA)\n${STYLE} Top: "👉 자세한 내용은". Center: rounded rectangle button (deep brown #6B4226) with white Korean text "프로필 링크 클릭". Bottom tiny text: "persona.aikorea24.kr | D-${b._d} 마감". Gift-box flat icon at top.\n`);
});

console.log(`\n--- 완료: ${ranked.length}개 지원금 × 5장 = ${ranked.length*5}장 프롬프트 ---`);
