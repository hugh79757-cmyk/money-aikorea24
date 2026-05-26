import { getCollection } from 'astro:content';

export async function GET() {
  const posts = await getCollection('blog', ({ data }) => !data.draft);
  const searchData = posts.map(post => ({
    title: post.data.title || '',
    description: post.data.description || '',
    slug: post.id,
    category: post.data.category || 'general',
    pubDate: post.data.pubDate ? String(post.data.pubDate) : '',
  }));
  return new Response(JSON.stringify(searchData), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}
