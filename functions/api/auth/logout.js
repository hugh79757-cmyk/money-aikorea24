export async function onRequestGet({ request }) {
  const headers = new Headers({ Location: '/' });
  // host-only 쿠키 만료
  headers.append('Set-Cookie', 'session=; Path=/; HttpOnly; Max-Age=0; Secure; SameSite=Lax');
  headers.append('Set-Cookie', 'session_ui=; Path=/; Max-Age=0; Secure; SameSite=Lax');
  // 구식 Domain=.aikorea24.kr 쿠키 무력화 (마이그레이션)
  headers.append('Set-Cookie', 'session=; Path=/; Domain=.aikorea24.kr; HttpOnly; Max-Age=0; Secure; SameSite=Lax');
  headers.append('Set-Cookie', 'session_ui=; Path=/; Domain=.aikorea24.kr; Max-Age=0; Secure; SameSite=Lax');
  return new Response(null, { status: 302, headers });
}
