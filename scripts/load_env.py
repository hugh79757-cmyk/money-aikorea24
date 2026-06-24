"""
환경변수 로더 — .env → .env.common 순서로 폴백
모든 Python 스크립트에서 from load_env import env; env("KEY") 형태로 사용

사용법:
    from load_env import env
    API_KEY = env("DATA_GO_KR_API_KEY")
"""
import os
from pathlib import Path


def _parse_env_file(path: str) -> dict:
    """KEY=VALUE 형태의 .env 파일 파싱 (주석, 빈 줄 무시)"""
    result = {}
    p = Path(path)
    if not p.exists():
        return result
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # 따로 감싼 문자열 처리
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


# 프로젝트 루트
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
_COMMON_ENV = str(Path.home() / ".env.common")

# 1차: .env.common 로드 (전역 백업)
_common = _parse_env_file(_COMMON_ENV)
for _k, _v in _common.items():
    if _k not in os.environ:
        os.environ[_k] = _v

# 2차: 프로젝트 .env 로드 (우선)
_project_env = os.path.join(_PROJECT_ROOT, ".env")
_project = _parse_env_file(_project_env)
for _k, _v in _project.items():
    # .env의 값이 .env.common보다 우선 (이미 os.environ에 있으면 덮어씀)
    os.environ[_k] = _v


def env(key: str, default: str = "") -> str:
    """환경변수 조회 — .env → .env.common → 기본값"""
    return os.environ.get(key, default)
