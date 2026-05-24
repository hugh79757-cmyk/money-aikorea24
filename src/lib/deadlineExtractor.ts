// deadlineExtractor.ts
// 지원금 본문에서 마감일 추출 → 없으면 회계연도 말일(12/31) 반환

/**
 * 본문에서 구체 날짜 추출 (패턴 A)
 * 우선순위: YYYY년 M월 D일 > YYYY.MM.DD > 'YY.M.D > M월 D일까지
 */
export function extractDeadlineFromContent(text: string): Date | null {
  if (!text) return null;

  const now = new Date();
  const currentYear = now.getFullYear();

  // 패턴 1: 2026년 5월 29일 / 2026년5월29일
  const p1 = text.match(/(20\d{2})년\s*(\d{1,2})월\s*(\d{1,2})일/);
  if (p1) {
    const d = new Date(+p1[1], +p1[2] - 1, +p1[3]);
    if (d > now) return d;
  }

  // 패턴 2: 2026.05.29 / 2026-05-29
  const p2 = text.match(/(20\d{2})[.\-](\d{1,2})[.\-](\d{1,2})/);
  if (p2) {
    const d = new Date(+p2[1], +p2[2] - 1, +p2[3]);
    if (d > now) return d;
  }

  // 패턴 3: '26.5.29
  const p3 = text.match(/'(\d{2})[.\-](\d{1,2})[.\-](\d{1,2})/);
  if (p3) {
    const d = new Date(2000 + +p3[1], +p3[2] - 1, +p3[3]);
    if (d > now) return d;
  }

  // 패턴 4: 5월 29일까지
  const p4 = text.match(/(\d{1,2})월\s*(\d{1,2})일까지/);
  if (p4) {
    const month = +p4[1];
    const day = +p4[2];
    let year = currentYear;
    const candidate = new Date(year, month - 1, day);
    if (candidate <= now) year += 1; // 이미 지난 월/일이면 내년
    return new Date(year, month - 1, day);
  }

  return null;
}

/**
 * 마감일 계산 메인 함수
 * - 본문에서 구체 날짜 추출 시도 (패턴 A)
 * - 실패 시 회계연도 말일 12/31 (패턴 B, 롤오버 포함)
 */
export function calcDeadline(content: string, deadlineField: string): {
  date: Date;
  daysLeft: number;
  source: 'content' | 'fiscal';
  label: string;
} {
  const now = new Date();
  now.setHours(0, 0, 0, 0);

  // 패턴 A 시도
  const extracted = extractDeadlineFromContent(content || '');
  if (extracted) {
    const diff = Math.ceil((extracted.getTime() - now.getTime()) / 86400000);
    return {
      date: extracted,
      daysLeft: diff,
      source: 'content',
      label: formatDeadlineLabel(diff),
    };
  }

  // 패턴 B: 회계연도 말일 (12/31), 지난 경우 익년으로 롤오버
  let fiscalEnd = new Date(now.getFullYear(), 11, 31);
  if (fiscalEnd <= now) fiscalEnd = new Date(now.getFullYear() + 1, 11, 31);
  const diff = Math.ceil((fiscalEnd.getTime() - now.getTime()) / 86400000);
  return {
    date: fiscalEnd,
    daysLeft: diff,
    source: 'fiscal',
    label: formatDeadlineLabel(diff),
  };
}

function formatDeadlineLabel(days: number): string {
  if (days <= 0) return '마감';
  if (days === 1) return '오늘 마감 🔥';
  if (days <= 7) return `D-${days} 🔥`;
  if (days <= 30) return `D-${days} ⏰`;
  return `D-${days}`;
}

/**
 * 카운트다운 배지 색상 클래스
 */
export function deadlineBadgeClass(daysLeft: number): string {
  if (daysLeft <= 7) return 'deadline-urgent';
  if (daysLeft <= 30) return 'deadline-soon';
  return 'deadline-normal';
}
