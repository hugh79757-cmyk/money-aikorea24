export type PersonaInput = {
  age: number;
  sex?: string;       // 'male' | 'female'
  region?: string;
  category?: string;
};

export type Benefit = {
  id: string;
  name: string;
  purpose: string;
  target: string;
  content: string;
  type: string;
  method: string;
  deadline: string;
  url: string;
  org: string;
  updated: string;
  category: string;
  age_range: number[];
  regions: string[];
  sex?: string;       // 'male' | 'female' | 'any'
  _curated?: boolean;
  _score?: number;
};

export type BenefitMatch = Benefit & {
  matchStatus: 'eligible_likely' | 'needs_check' | 'not_eligible';
  score: number;
  reasons: string[];
  warnings: string[];
};

const REGION_MAP: Record<string, string[]> = {
  '서울': ['서울'], '경기': ['경기'], '인천': ['인천'],
  '부산': ['부산'], '대구': ['대구'], '광주': ['광주'],
  '대전': ['대전'], '울산': ['울산'], '세종': ['세종'],
  '강원': ['강원'],
  '충북': ['충북','충청'], '충남': ['충남','충청'],
  '충청남': ['충남','충청'], '충청북': ['충북','충청'],
  '전북': ['전북'], '전남': ['전남'],
  '전라남': ['전남'], '전라북': ['전북'],
  '경북': ['경북'], '경남': ['경남'],
  '경상남': ['경남'], '경상북': ['경북'],
  '제주': ['제주'],
};

function regionMatch(personaRegion: string, benefitRegions: string[]): boolean {
  if (!benefitRegions || benefitRegions.includes('전국')) return true;
  const aliases = REGION_MAP[personaRegion] || [personaRegion];
  return aliases.some(a => benefitRegions.some(r => r.includes(a) || a.includes(r)));
}

export function matchBenefit(persona: PersonaInput, benefit: Benefit): BenefitMatch {
  let score = 50;
  const reasons: string[] = [];
  const warnings: string[] = [];

  // ── 1. 나이 하드 필터 ──────────────────────────────
  if (benefit.age_range && benefit.age_range.length === 2) {
    const [min, max] = benefit.age_range;
    if (persona.age < min || persona.age > max) {
      return { ...benefit, matchStatus: 'not_eligible', score: 0,
        reasons: [`연령 조건 불일치 (만 ${min}~${max}세)`], warnings: [] };
    }
    score += 20;
    reasons.push(`연령 조건 해당 (만 ${min}~${max}세)`);
  }

  // ── 2. 성별 하드 필터 ──────────────────────────────
  const bSex = benefit.sex || 'any';
  if (bSex !== 'any' && persona.sex && persona.sex !== 'any') {
    if (bSex !== persona.sex) {
      return { ...benefit, matchStatus: 'not_eligible', score: 0,
        reasons: ['성별 조건 불일치'], warnings: [] };
    }
    score += 10;
    reasons.push('성별 조건 해당');
  }

  // ── 3. 지역 필터 ──────────────────────────────────
  if (persona.region) {
    if (regionMatch(persona.region, benefit.regions)) {
      if (!benefit.regions.includes('전국')) {
        score += 15;
        reasons.push(`${persona.region} 지역 대상`);
      }
    } else {
      return { ...benefit, matchStatus: 'not_eligible', score: 0,
        reasons: ['지역 조건 불일치'], warnings: [] };
    }
  }

  // ── 4. 큐레이션 우선 가점 ─────────────────────────
  if (benefit._curated) {
    score += 25;
    reasons.push('검증된 주요 혜택');
  }

  // ── 5. 카테고리 보너스 ────────────────────────────
  const catBonus: Record<string, string[]> = {
    youth:    ['20대','30대','청년','대학','취업','창업'],
    senior:   ['60대','70대','시니어','노인','은퇴','어르신'],
    child:    ['아이','육아','출산','자녀','어린이','영아'],
    welfare:  ['저소득','수급','복지','장애','긴급'],
    business: ['자영업','창업','소상공인','프리랜서'],
  };
  const personaText = (persona.category || '');
  const bonusKws = catBonus[benefit.category] || [];
  if (bonusKws.some(k => personaText.includes(k) || benefit.name.includes(k))) {
    score += 10;
  }

  // ── 6. 소득/재산 경고 ─────────────────────────────
  const checkText = (benefit.target || '') + (benefit.content || '');
  if (checkText.includes('소득') || checkText.includes('중위')) {
    warnings.push('소득 기준 확인 필요');
    score -= 3;
  }
  if (checkText.includes('재산') || checkText.includes('자산')) {
    warnings.push('재산 기준 확인 필요');
    score -= 3;
  }

  // ── 7. url 없으면 경고 ────────────────────────────
  if (!benefit.url) {
    warnings.push('신청처 직접 확인 필요');
    score -= 5;
  }

  const matchStatus = warnings.length > 0 ? 'needs_check' : 'eligible_likely';
  return { ...benefit, matchStatus, score, reasons, warnings };
}

export function getBenefitMatches(
  persona: PersonaInput,
  benefits: Benefit[],
  limit = 8
): BenefitMatch[] {
  return benefits
    .map(b => matchBenefit(persona, b))
    .filter(b => b.matchStatus !== 'not_eligible' && b.score > 35)
    .sort((a, b) => {
      // 큐레이션 먼저
      if (a._curated && !b._curated) return -1;
      if (!a._curated && b._curated) return 1;
      return b.score - a.score;
    })
    .slice(0, limit);
}
