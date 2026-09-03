/**
 * patch-income.mjs  (v4 — 중위소득 기반 통일 체계)
 *
 * 모든 소득 추정을 하나의 중위소득 기반 체계로 통일:
 *   estimatedIncome = categoryBase × ageSexFactor(median) × regionFactor
 *
 * income_employed = nationalMedianIncome × ageSexFactor × regionFactor
 *   - 히어로 카드 "추정 월소득"에 사용
 *   - 중위소득(350) × 성별·연령 보정계수 × 지역 보정계수
 *   - 통계청 2023 전체 임금근로자 중위월소득 350만원 기준
 *
 * income_region_avg = medianBase × regionFactor
 *   - "지역 중위 소득" 참고값으로 유지
 *   - 성별·연령별 전국 취업자 중위월소득 × 지역 보정
 *
 * income_estimate = income_employed (동일 체계, 추후 직업 반영 시 분리)
 *
 * top_percentile: 로그정규분포로 "전체 취업자 중 상위 몇 %" 추정
 *   - 소득 분포는 로그정규에 가까움 (우편향 분포)
 *   - MU  = ln(medianBase)   ← 해당 그룹 중위값이 분포 중심
 *   - SIG = 0.72              ← 한국 임금 로그정규 표준편차 실증 추정
 *   - top% = (1 - Φ((ln(income) - MU) / SIG)) × 100
 */
import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { calcTopPct } from '../src/lib/income-percentile.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const STATS_PATH = resolve(__dirname, '../data/persona-stats.json');
const WAGE_PATH  = resolve(__dirname, '../src/data/wage-table.json');

const wageTable = JSON.parse(readFileSync(WAGE_PATH, 'utf8'));

// ── wage-table.json에서 regionFactor 읽기 ────────────────────────
const REGION_MULT = wageTable.regionFactor;

function getRegionMult(key) {
  for (const [r, m] of Object.entries(REGION_MULT)) {
    if (key.startsWith(r)) return m;
  }
  return 1.0;
}

/** ageNum → wage-table ageKey (5세 단위) */
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
const ageSexFactor = wageTable.ageSexFactor;
const nationalMedianIncome = wageTable.nationalMedianIncome ?? 350;

let fixed = 0, skipped = 0;

for (const [key, val] of Object.entries(data)) {
  if (!val?.income) continue;

  const sex        = val.income.income_sex;
  const ageBracket = val.income.income_age_bracket;
  if (!sex) { skipped++; continue; }

  const parts    = key.split('_');
  const lastPart = parts[parts.length - 1];
  const ageNum   = parseInt(lastPart, 10);

  const ageKey = resolveAgeKey(ageNum, ageBracket);
  if (!ageKey) { skipped++; continue; }

  const sexKey     = sex === '여' ? '여' : '남';
  const medianBase = (wageTable.medianBase[sexKey] || {})[ageKey];
  if (!medianBase) { skipped++; continue; }

  const regionMult = getRegionMult(key);

  // 통일 공식: nationalMedianIncome × ageSexFactor(median) × regionFactor
  const asfKey = `${sexKey}_${ageKey}`;
  const asfVal = ageSexFactor[asfKey] ?? (medianBase / nationalMedianIncome);
  const employed = Math.round(nationalMedianIncome * asfVal * regionMult);

  // income_region_avg: 기존 medianBase × regionFactor 유지 (지역 중위 참고값)
  const regionAvg = Math.round(medianBase * regionMult);

  val.income.income_employed     = employed;
  val.income.income_national_avg = medianBase;
  val.income.income_region_avg   = regionAvg;
  val.income.top_percentile      = calcTopPct(employed);
  val.income.income_estimate     = employed;
  val.income.income_source       = '통계청·국세청 근로소득 분포 2024 중위값 기반 통일 추정 (nationalMedianIncome × ageSexFactor × regionFactor)';
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
  '광주_여자_33', '광주_여자_30대',
];
console.log('\n--- 검증 샘플 ---');
console.log('페르소나               | 소득   | 지중위 | 전국중위 | 상위% | asfKey');
console.log('-----------------------|--------|-------|---------|-----|-------');
for (const k of samples) {
  const inc = data[k]?.income;
  if (inc) {
    const {income_employed: e, income_region_avg: r, income_national_avg: n, top_percentile: t} = inc;
    const p = k.split('_');
    const last = p[p.length-1];
    const ageNum = parseInt(last);
    const aKey = resolveAgeKey(ageNum, '');
    const sKey = inc.income_sex === '여' ? '여' : '남';
    const asfKey = `${sKey}_${aKey}`;
    console.log(k.padEnd(23)+'| '+String(e).padStart(4)+'만원 | '+String(r).padStart(4)+'만원 | '+String(n).padStart(5)+'만원 | '+String(t).padStart(4)+'% | '+asfKey);
  }
}
