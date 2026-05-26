// 복지로 API (지자체 + 중앙부처) 페르소나 매칭
// 입력: persona-stats.json 키 (지역, 성별, 나이)
// 출력: 매칭된 복지서비스 카드 N개

export type WelfarePersona = {
  age: number;
  sex?: string;
  region: string;  // 예: '서울', '경기', '광주'
};

export type WelfareRaw = {
  servId: string;
  servNm: string;
  servDgst?: string;
  servDtlLink?: string;
  ctpvNm?: string;
  sggNm?: string;
  bizChrDeptNm?: string;
  lifeNmArray?: string;     // "청년, 중장년"
  lifeArray?: string;       // 중앙 API
  trgterIndvdlArray?: string;
  intrsThemaArray?: string;
  jurMnofNm?: string;
  aplyMtdNm?: string;
  sprtCycNm?: string;
  srvPvsnNm?: string;
  lastModYmd?: string;
  inqNum?: string;
  _source?: 'local' | 'central';
};

export type WelfareMatch = WelfareRaw & {
  score: number;
  reasons: string[];
  lifeStage: string;
};

// 페르소나 지역 키 → 복지로 ctpvNm 풀네임
const REGION_TO_CTPV: Record<string, string[]> = {
  '서울': ['서울특별시'],
  '부산': ['부산광역시'],
  '대구': ['대구광역시'],
  '인천': ['인천광역시'],
  '광주': ['광주광역시'],
  '대전': ['대전광역시'],
  '울산': ['울산광역시'],
  '세종': ['세종특별자치시'],
  '경기': ['경기도'],
  '강원': ['강원특별자치도', '강원도'],
  '충북': ['충청북도'],
  '충남': ['충청남도'],
  '전북': ['전북특별자치도', '전라북도'],
  '전남': ['전라남도'],
  '경북': ['경상북도'],
  '경남': ['경상남도'],
  '제주': ['제주특별자치도'],
};

// 나이 → 생애주기 태그
export function ageToLifeStage(age: number): string {
  if (age < 35) return "청년";
  if (age < 65) return "중장년";
  return "노년";
}

function regionMatch(personaRegion: string, welfare: WelfareRaw): 'exact' | 'national' | 'none' {
  const ctpv = welfare.ctpvNm || '';
  // 중앙부처는 ctpvNm 없음 → 전국 대상
  if (!ctpv || ctpv === '-') return 'national';
  const targets = REGION_TO_CTPV[personaRegion] || [personaRegion];
  for (const t of targets) {
    if (ctpv.includes(t) || t.includes(ctpv)) return 'exact';
  }
  return 'none';
}

function lifeStageMatch(personaStage: string, welfare: WelfareRaw): boolean {
  const tags = (welfare.lifeNmArray || welfare.lifeArray || '').trim();
  if (!tags) return true;  // 태그 없으면 전 연령 대상으로 간주
  return tags.split(',').map(s => s.trim()).includes(personaStage);
}

export function matchWelfare(
  persona: WelfarePersona,
  pool: WelfareRaw[],
  limit = 8
): WelfareMatch[] {
  const stage = ageToLifeStage(persona.age);
  const results: WelfareMatch[] = [];

  for (const w of pool) {
    const regionKind = regionMatch(persona.region, w);
    if (regionKind === 'none') continue;

    const lifeOk = lifeStageMatch(stage, w);
    if (!lifeOk) continue;

    let score = 50;
    const reasons: string[] = [];

    if (regionKind === 'exact') {
      score += 30;
      reasons.push(`${w.ctpvNm}${w.sggNm ? ' ' + w.sggNm : ''} 특화`);
    } else {
      score += 10;
      reasons.push('전국 대상');
    }

    const tags = (w.lifeNmArray || w.lifeArray || '').trim();
    if (tags && tags.split(',').map(s => s.trim()).includes(stage)) {
      score += 20;
      reasons.push(`${stage} 맞춤`);
    }

    // 신선도 가점 (6개월 이내 갱신)
    if (w.lastModYmd && /^\d{8}$/.test(w.lastModYmd)) {
      const y = +w.lastModYmd.slice(0, 4), m = +w.lastModYmd.slice(4, 6), d = +w.lastModYmd.slice(6, 8);
      const days = (Date.now() - new Date(y, m - 1, d).getTime()) / 86400000;
      if (days < 180) score += 5;
    }

    // 조회수 보정 (인기도)
    const inq = +(w.inqNum || 0);
    if (inq > 10000) score += 5;
    else if (inq > 1000) score += 2;

    results.push({ ...w, score, reasons, lifeStage: stage });
  }

  results.sort((a, b) => b.score - a.score);
  return results.slice(0, limit);
}
