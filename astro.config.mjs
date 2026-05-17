// @ts-check

import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig } from 'astro/config';
import remarkGfm from 'remark-gfm';

export default defineConfig({
  site: 'https://persona.aikorea24.kr',
  integrations: [
    mdx({
      remarkPlugins: [[remarkGfm, { singleTilde: false }]],
    }),
    sitemap({
      changefreq: 'weekly',
      priority: 0.7,
    }),
  ],
  markdown: {
    remarkPlugins: [[remarkGfm, { singleTilde: false }]],
  },
});
