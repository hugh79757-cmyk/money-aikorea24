// generate-decade-stats.mjs
// persona-stats.json에서 decade 수준 데이터만 추출 (204 keys, ~4MB)
import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');

const raw = readFileSync(join(root, 'public', 'persona-stats.json'), 'utf-8');
const fullData = JSON.parse(raw);
const decadeData = {};

for (const [k, v] of Object.entries(fullData)) {
  const last = k.split('_')[2];
  if (last.includes('대') || last.includes('이상')) {
    const inc = v.income ? {
      income_employed: v.income.income_employed,
      income_estimate: v.income.income_estimate,
      top_percentile: v.income.top_percentile,
    } : null;
    decadeData[k] = { ...v, income: inc };
  }
}

const out = JSON.stringify(decadeData);
writeFileSync(join(root, 'public', 'persona-stats-decade.json'), out, 'utf-8');
console.log(`Generated persona-stats-decade.json (${(Buffer.byteLength(out, 'utf-8') / 1024 / 1024).toFixed(1)} MiB, ${Object.keys(decadeData).length} keys)`);
