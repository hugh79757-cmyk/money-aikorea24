// @ts-check
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'astro/config';
import remarkGfm from 'remark-gfm';

export default defineConfig({
  vite: {
    plugins: [tailwindcss()],
  },
  site: 'https://persona.aikorea24.kr',
  output: 'static',
  integrations: [
    mdx({ remarkPlugins: [[remarkGfm, { singleTilde: false }]] }),
    sitemap({
      changefreq: 'weekly',
      priority: 0.7,
      filter: (page) => {
        // 1년 단위 페르소나 페이지(noindex)는 사이트맵에서 제외
        // 예: /persona/서울-남자-35/  → 제외
        //     /persona/서울-남자-30대/ → 포함 (10년 단위만)
        const match = page.match(/\/persona\/[^/]+-(\d+|\d+대|\d+대이상|이상)\/?$/);
        if (!match) return true; // persona 아닌 페이지는 모두 포함
        const age = match[1];
        // 숫자만 있는 경우(1년 페이지)는 제외, '대' 또는 '이상' 포함 시 통과
        return age.includes('대') || age.includes('이상');
      },
    }),
  ],
  markdown: {
    remarkPlugins: [[remarkGfm, { singleTilde: false }]],
  },
});
