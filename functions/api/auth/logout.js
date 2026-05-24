export async function onRequestGet({ request }) {
  const headers = new Headers({ Location: '/' });
  headers.append('Set-Cookie', 'session=; Path=/; HttpOnly; Max-Age=0');
  return new Response(null, { status: 302, headers });
}
