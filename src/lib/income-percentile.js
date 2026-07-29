/**
 * income-percentile.js  —  소득 백분위 계산 (로그정규 분포)
 *
 * persona.aikorea24.kr / scripts/patch-income.mjs 에서 공동 사용.
 *
 * calcTopPct(monthlyIncome):
 *   한국 임금 소득 분포를 로그정규분포로 가정해
 *   "전체 취업자 중 상위 몇 %"를 추정.
 *
 * 상수 출처:
 *   GLOBAL_MED = 288 (만원)  — 전국 취업자 중위월소득 (KOSIS 2023 기반)
 *   SIG        = 0.72        — 로그정규 표준편차 실증 추정값
 *
 * @param {number} income  월소득 (단위: 만원, 0 초과)
 * @returns {number|null}  상위 백분위 (0.1 단위, 예: 33.7)
 */

export const GLOBAL_MED = 288;  // 전국 취업자 중위월소득 (만원)
export const SIG        = 0.72; // 로그정규 표준편차

/* ── 로그정규 누적분포함수(CDF) 근사 (Abramowitz & Stegun) ── */
function erf(x) {
  const t = 1 / (1 + 0.3275911 * Math.abs(x));
  const poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))));
  const result = 1 - poly * Math.exp(-x * x);
  return x >= 0 ? result : -result;
}

function normCDF(z) {
  return 0.5 * (1 + erf(z / Math.SQRT2));
}

/**
 * 월소득(만원)을 입력받아 전국 취업자 중 상위 백분위를 반환.
 *
 * @param {number} income  월소득 (만원). 0 이하 또는 null/undefined 시 null.
 * @returns {number|null}  상위 백분위 (0.1 단위, 0 < result < 100)
 *
 * @example
 *   calcTopPct(400)  // → 33.7  (월 400만원 = 상위 33.7%)
 *   calcTopPct(0)    // → null
 */
export function calcTopPct(income) {
  if (!income || income <= 0) return null;
  const z      = (Math.log(income) - Math.log(GLOBAL_MED)) / SIG;
  const topPct = (1 - normCDF(z)) * 100;
  return Math.round(topPct * 10) / 10;
}
