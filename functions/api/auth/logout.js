export async function onRequestGet({ request }) {
  const headers = new Headers({ Location: '/' });
  headers.append('Set-Cookie', 'session=; Path=/; HttpOnly; Max-Age=0; Secure; SameSite=Lax');
  headers.append('Set-Cookie', 'session_ui=; Path=/; Max-Age=0; Secure; SameSite=Lax');
  return new Response(null, { status: 302, headers });
}
