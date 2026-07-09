import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const personaCardTargetSchema = z.object({
  ctaText: z.string(),
  ctaSubtext: z.string().optional(),
  targetUrl: z.string(),
  focusSection: z.string().optional(),
}).optional();

const targetPersonaSchema = z.object({
  ageRange: z.tuple([z.number(), z.number()]).optional(),
  gender: z.array(z.string()).optional(),
  maritalStatus: z.array(z.string()).optional(),
  regions: z.array(z.string()).optional(),
  hasChildren: z.boolean().optional(),
  priority: z.number().optional(),
}).optional();

const sharedSchema = z.object({
        title: z.string(),
        description: z.string(),
        draft: z.boolean().default(true),
        tags: z.array(z.string()).optional().default([]),
        pubDate: z.coerce.date().optional(),
        updatedDate: z.coerce.date().optional(),
        heroImage: z.string().optional(),
        category: z.enum(["insurance", "invest", "loan", "general"]).optional(),
        needs_review: z.boolean().optional().default(false),
        canonical: z.string().optional(),
        noindex: z.boolean().optional().default(false),
        personaCardTarget: personaCardTargetSchema,
        targetPersona: targetPersonaSchema,
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
