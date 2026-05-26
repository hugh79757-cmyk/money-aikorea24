import { readFileSync, writeFileSync } from 'fs';
const PATH = '/Users/twinssn/Projects/money-aikorea24/public/persona-stats.json';

const BASE = {
  '남': { '20대':310, '30대':460, '40대':510, '50대':490, '60대이상':255 },
  '여': { '20대':245, '30대':315, '40대':320, '50대':280, '60대이상':185 },
};
const REGION_MULT = {
  '서울':1.15,'경기':1.05,'인천':1.02,'부산':1.00,'대구':0.97,
  '광주':0.95,'대전':0.98,'울산':1.08,'세종':1.02,'강원':0.92,
  '충북':0.93,'충청북':0.93,'충남':0.95,'충청남':0.95,
  '전북':0.90,'전라북':0.90,'전남':0.88,'전라남':0.88,
  '경북':0.92,'경상북':0.92,'경남':0.95,'경상남':0.95,'제주':0.88,
};

function getRegionMult(key) {
  for (const [r, m] of Object.entries(REGION_MULT)) {
    if (key.startsWith(r)) return m;
  }
  return 1.0;
}
function getAgeKey(bracket) {
  if (!bracket) return null;
  if (bracket.includes('20')) return '20대';
  if (bracket.includes('30')) return '30대';
  if (bracket.includes('40')) return '40대';
  if (bracket.includes('50')) return '50대';
  return '60대이상';
}

const data = JSON.parse(readFileSync(PATH, 'utf8'));
let fixed = 0;

for (const [key, val] of Object.entries(data)) {
  if (!val?.income) continue;
  const sex = val.income.income_sex;
  const ageBracket = val.income.income_age_bracket;
  const ageKey = getAgeKey(ageBracket);
  if (!sex || !ageKey || !BASE[sex]?.[ageKey]) continue;

  const base = BASE[sex][ageKey];
  const mult = getRegionMult(key);
  const regionAvg = Math.round(base * mult);

  val.income.income_region_avg = regionAvg;
  val.income.income_national_avg = base;
  val.income.income_source = 'KOSIS 고용형태별근로실태조사 2024 성별×연령×지역 보정';
  val.income.income_year = 2024;
  fixed++;
}

writeFileSync(PATH, JSON.stringify(data), 'utf8');
console.log(`보정 완료: ${fixed}개`);
