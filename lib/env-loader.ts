/**
 * 환경변수 로더 — .env → .env.common 순서로 폴백
 *
 * dotenv와 동일하게 process.env에 주입하되,
 * .env에 없는 변수는 ~/.env.common에서 자동으로 가져온다.
 *
 * 사용법 (빌드 스크립트 등):
 *   import './lib/env-loader.js';  // process.env에 주입
 *
 * 사용법 (Functions):
 *   import { getEnv } from './lib/env-loader.js';
 *   const token = getEnv('TELEGRAM_BOT_TOKEN');
 */
import { readFileSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';

function parseEnvFile(filePath: string): Record<string, string> {
  const result: Record<string, string> = {};
  if (!existsSync(filePath)) return result;

  const content = readFileSync(filePath, 'utf-8');
  for (const line of content.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    const eqIdx = trimmed.indexOf('=');
    if (eqIdx === -1) continue;

    let key = trimmed.slice(0, eqIdx).trim();
    let value = trimmed.slice(eqIdx + 1).trim();

    // 따로 감싼 문자열 처리
    if (value.length >= 2 && value[0] === value[value.length - 1] && (value[0] === '"' || value[0] === "'")) {
      value = value.slice(1, -1);
    }

    result[key] = value;
  }
  return result;
}

// 프로젝트 루트 탐색 (lib/ 안에서 1단계 상위)
function findProjectRoot(): string {
  // Vite/Astro 환경
  if (typeof process !== 'undefined' && process.cwd) {
    return process.cwd();
  }
  // Node.js 환경
  return resolve(import.meta.dirname ?? '.', '..');
}

// 1차: ~/.env.common 로드 (전역 백업)
const homeEnvPath = join(process.env.HOME || '~', '.env.common');
const commonVars = parseEnvFile(homeEnvPath);
for (const [key, value] of Object.entries(commonVars)) {
  if (!process.env[key]) {
    process.env[key] = value;
  }
}

// 2차: 프로젝트 .env 로드 (우선)
const projectRoot = findProjectRoot();
const projectEnvPath = join(projectRoot, '.env');
const projectVars = parseEnvFile(projectEnvPath);
for (const [key, value] of Object.entries(projectVars)) {
  process.env[key] = value;
}

/**
 * 환경변수 조회 — .env → .env.common → 기본값
 */
export function getEnv(key: string, defaultValue = ''): string {
  return process.env[key] ?? defaultValue;
}

export default getEnv;
