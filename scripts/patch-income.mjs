/**
 * patch-income.mjs  (v3 — 중위값 기반 + 로그정규 백분위)
 *
 * income_employed = medianBase[성별][연령] × regionFactor
 *   medianBase: 성별×연령별 전국 취업자 중위월소득(만원)
 *               (통계청·국세청 근로소득 분포 2022-2024 추정)
 *
 * top_percentile: 로그정규분포로 "동일 성별·연령 취업자 중 상위 몇 %" 추정
 *   - 소득 분포는 로그정규에 가까움 (우편향 분포)
 *   - MU  = ln(medianBase)   ← 해당 그룹 중위값이 분포 중심
 *   - SIG = 0.72              ← 한국 임금 로그정규 표준편차 실증 추정
 *   - top% = (1 - Φ((ln(income) - MU) / SIG)) × 100
 */
import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const STATS_PATH = resolve(__dirname, '../public/persona-stats.json');
const WAGE_PATH  = resolve(__dirname, '../src/data/wage-table.json');

const wageTable = JSON.parse(readFileSync(WAGE_PATH, 'utf8'));

// ── 로그정규 누적분포함수(CDF) 근사 ──────────────────────────────
// Abramowitz & Stegun erf 근사 (JS에 Math.erf 없으므로 직접 구현)
function erf(x) {
  const t = 1 / (1 + 0.3275911 * Math.abs(x));
  const poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))));
  const result = 1 - poly * Math.exp(-x * x);
  return x >= 0 ? result : -result;
}
function normCDF(z) { return 0.5 * (1 + erf(z / Math.SQRT2)); }

const SIG         = 0.72;  // 한국 임금 로그정규 표준편차 추정
const GLOBAL_MED  = 288;   // 전체 임금근로자 중위월소득 (2024 국세청, 만원)

/**
 * 전체 취업자 소득 분포에서 상위 몇 % 인지 반환.
 * 기준: 전국 취업자 중위 GLOBAL_MED, 로그정규 SIG
 * → 지역·성별·연령이 달라도 소득에 따라 각기 다른 값이 나옴
 */
function calcTopPct(income) {
  if (!income || income <= 0) return null;
  const z      = (Math.log(income) - Math.log(GLOBAL_MED)) / SIG;
  const topPct = (1 - normCDF(z)) * 100;
  return Math.round(topPct * 10) / 10;
}

// ── 지역 보정계수 ────────────────────────────────────────────────
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

/** ageNum 또는 ageBracket → wage-table ageKey */
function resolveAgeKey(ageNum, ageBracket) {
  if (ageNum !== null && !isNaN(ageNum)) {
    if (ageNum < 20) return '10대';
    if (ageNum < 25) return '20대초';
    if (ageNum < 30) return '20대후';
    if (ageNum < 35) return '30대초';
    if (ageNum < 40) return '30대후';
    if (ageNum < 45) return '40대초';
    if (ageNum < 50) return '40대후';
    if (ageNum < 55) return '50대초';
    if (ageNum < 60) return '50대후';
    return '60대이상';
  }
  if (!ageBracket) return null;
  if (ageBracket.includes('10')) return '10대';
  if (ageBracket.includes('20')) return '20대후';
  if (ageBracket.includes('30')) return '30대초';
  if (ageBracket.includes('40')) return '40대초';
  if (ageBracket.includes('50')) return '50대초';
  return '60대이상';
}

// ── 메인 ────────────────────────────────────────────────────────
const data = JSON.parse(readFileSync(STATS_PATH, 'utf8'));
let fixed = 0, skipped = 0;

for (const [key, val] of Object.entries(data)) {
  if (!val?.income) continue;

  const sex        = val.income.income_sex;
  const ageBracket = val.income.income_age_bracket;
  if (!sex) { skipped++; continue; }

  const parts    = key.split('_');
  const lastPart = parts[parts.length - 1];
  const isDecade = lastPart.includes('대') || lastPart.includes('이상');
  const ageNum   = isDecade ? null : parseInt(lastPart, 10);

  const ageKey = resolveAgeKey(ageNum, ageBracket);
  if (!ageKey) { skipped++; continue; }

  const sexKey     = sex === '여' ? '여' : '남';
  const medianBase = (wageTable.medianBase[sexKey] || {})[ageKey];
  if (!medianBase) { skipped++; continue; }

  const regionMult = getRegionMult(key);
  const employed   = Math.round(medianBase * regionMult);
  const nationalMed = medianBase; // 전국 동일그룹 중위 (지역 보정 전)

  val.income.income_employed     = employed;
  val.income.income_national_avg = nationalMed; // 실제론 중위값이지만 필드명 유지
  val.income.income_region_avg   = employed;
  val.income.top_percentile      = calcTopPct(employed);
  val.income.income_estimate     = employed;
  val.income.income_source       = '통계청·국세청 근로소득 분포 2024 성별×연령 중위값 × 지역보정';
  val.income.income_year         = 2024;
  fixed++;
}

writeFileSync(STATS_PATH, JSON.stringify(data), 'utf8');
console.log(`완료: ${fixed}개 보정, ${skipped}개 건너뜀`);

// ── 검증 출력 ────────────────────────────────────────────────────
const samples = [
  '서울_남자_32', '서울_남자_37', '서울_남자_30대',
  '서울_남자_40대', '서울_남자_50대',
  '경기_남자_30대', '강원_남자_30대', '서울_여자_30대',
];
console.log('\n--- 검증 샘플 ---');
console.log('페르소나               | 소득   | 전국중위 | 상위%');
console.log('-----------------------|--------|---------|-----');
for (const k of samples) {
  const inc = data[k]?.income;
  if (inc) {
    const {income_employed: e, income_national_avg: n, top_percentile: t} = inc;
    console.log(k.padEnd(23)+'| '+String(e).padStart(4)+'만원 | '+String(n).padStart(5)+'만원 | '+t+'%');
  }
}
