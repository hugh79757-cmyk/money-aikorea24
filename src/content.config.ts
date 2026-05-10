import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const sharedSchema = z.object({
        title: z.string(),
        description: z.string(),
        draft: z.boolean().default(true),
        tags: z.array(z.string()).optional().default([]),
        pubDate: z.coerce.date().optional(),
        updatedDate: z.coerce.date().optional(),
        heroImage: z.string().optional(),
        category: z.enum(["insurance", "invest", "loan", "tax", "general"]).optional(),
        needs_review: z.boolean().optional().default(false),
});

const makeCollection = (path: string) =>
        defineCollection({
                loader: glob({ base: path, pattern: '**/*.{md,mdx}' }),
                schema: sharedSchema,
        });

export const collections = {
        blog:  makeCollection('./src/content/blog'),
        nomad: makeCollection('./src/content/nomad'),
};
