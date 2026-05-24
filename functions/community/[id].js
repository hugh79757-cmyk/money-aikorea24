export async function onRequestGet({ params, env, request }) {
  const url = new URL(request.url);
  const html = await env.ASSETS.fetch(
    new Request(url.origin + '/community/_/index.html')
  );
  return new Response(await html.text(), {
    headers: { 'Content-Type': 'text/html; charset=utf-8' }
  });
}
