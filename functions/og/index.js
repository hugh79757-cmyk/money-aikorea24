// 동적 SVG OG는 카카오톡/페이스북이 인식하지 못하므로
// public/cards/{region}_{sex}_{age}.jpg 정적 파일로 리다이렉트
export async function onRequest(context) {
  const url = new URL(context.request.url);
  const params = url.searchParams;

  const region = params.get('region') || '서울';
  const sex    = params.get('sex')    || '남자';
  const age    = params.get('age')    || '35';

  const key = `${region}_${sex}_${age}`;
  const cardUrl = `https://persona.aikorea24.kr/cards/${encodeURIComponent(key)}.jpg`;

  return Response.redirect(cardUrl, 302);
}
