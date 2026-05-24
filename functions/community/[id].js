export async function onRequestGet({ params, env, request }) {
  const id = params.id;
  
  // write, _ 는 정적 에셋으로 패스스루
  if (id === 'write' || id === '_') {
    return env.ASSETS.fetch(request);
  }

  const url = new URL(request.url);
  const html = await env.ASSETS.fetch(
    new Request(url.origin + '/community/_/index.html')
  );
  return new Response(await html.text(), {
    headers: { 'Content-Type': 'text/html; charset=utf-8' }
  });
}
