export const CATEGORY_PERSONA_MAP: Record<string, {
  ctaText: string;
  ctaSubtext?: string;
  targetUrl: string;
  focusSection: string | null;
}> = {
  insurance: {
    ctaText: '나와 같은 조건 사람들의 보험 가입 현황은?',
    ctaSubtext: '내 페르소나로 확인하기',
    targetUrl: '/my-persona?focus=insurance',
    focusSection: 'insurance',
  },
  invest: {
    ctaText: '내 소득 수준에서 가능한 투자 한도는?',
    ctaSubtext: '내 페르소나로 확인하기',
    targetUrl: '/my-persona?focus=investment',
    focusSection: 'investment',
  },
  loan: {
    ctaText: '나와 같은 조건 한국인 평균 대출 한도는?',
    ctaSubtext: '내 페르소나로 확인하기',
    targetUrl: '/my-persona?focus=loan',
    focusSection: 'loan',
  },
  tax: {
    ctaText: '비슷한 소득의 한국인들은 세금을 얼마나 낼까?',
    ctaSubtext: '내 페르소나로 확인하기',
    targetUrl: '/my-persona?focus=tax',
    focusSection: 'tax',
  },
  nomad: {
    ctaText: '나와 비슷한 사람들의 부업 수익은?',
    ctaSubtext: '디지털 노마드 페르소나 확인하기',
    targetUrl: '/my-persona?focus=side_income',
    focusSection: 'side_income',
  },
  general: {
    ctaText: '나와 비슷한 한국인은 어떻게 살까?',
    ctaSubtext: '내 페르소나로 확인하기',
    targetUrl: '/my-persona',
    focusSection: null,
  },
};

export const CATEGORY_LABEL_KO: Record<string, string> = {
  insurance: '보험',
  invest: '투자·절세',
  loan: '대출·부동산',
  tax: '세금·절약',
  general: '금융 가이드',
};

export interface PersonaInput {
  age: number;
  gender: string;
  region: string;
  maritalStatus?: string;
}

export interface BlogPostMeta {
  title: string;
  description?: string;
  slug: string;
  category: string;
  ageRange?: [number, number];
  gender?: string[];
  maritalStatus?: string[];
  regions?: string[];
  priority?: number;
  pubDate?: string;
}

export function matchBlogPosts(
  persona: PersonaInput,
  allPosts: BlogPostMeta[],
): (BlogPostMeta & { matchScore: number })[] {
  return allPosts
    .map((post) => {
      let score = post.priority || 0;

      if (post.ageRange) {
        const [min, max] = post.ageRange;
        if (persona.age >= min && persona.age <= max) score += 10;
        else score -= 5;
      }

      if (post.maritalStatus && post.maritalStatus.length > 0) {
        if (post.maritalStatus.includes(persona.maritalStatus || '')) score += 8;
        else score -= 3;
      }

      if (post.regions && post.regions.length > 0) {
        if (post.regions.includes(persona.region)) score += 12;
        else score -= 2;
      }

      if (post.gender && post.gender.length > 0) {
        if (post.gender.includes(persona.gender)) score += 5;
      }

      return { ...post, matchScore: score };
    })
    .filter((post) => post.matchScore > 0)
    .sort((a, b) => b.matchScore - a.matchScore);
}

export function selectBlogCards(
  matched: (BlogPostMeta & { matchScore: number })[],
  count: number = 4,
  seed?: number,
): (BlogPostMeta & { matchScore: number })[] {
  if (matched.length <= count) return matched;

  const topCount = Math.ceil(count * 0.6);
  const top = matched.slice(0, topCount);
  const pool = matched.slice(topCount);
  const random = shuffle(pool, seed).slice(0, count - topCount);

  return [...top, ...random];
}

function shuffle<T>(arr: T[], seed?: number): T[] {
  const a = [...arr];
  let m = a.length;
  let t: T;
  let i: number;
  const rng = seed ? mulberry32(seed) : Math.random;
  while (m) {
    i = Math.floor(rng() * m--);
    t = a[m];
    a[m] = a[i];
    a[i] = t;
  }
  return a;
}

function mulberry32(seed: number) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export type PersonaCardTarget = {
  ctaText: string;
  ctaSubtext?: string;
  targetUrl: string;
  focusSection?: string;
};
