"""
R2 Uploader — 블로그 썸네일을 Cloudflare R2에 업로드
 boto3 (S3-compatible API) 사용
"""
import os
import sys
from pathlib import Path

# load_env: .env → .env.common 폴백
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from load_env import env

import boto3
from botocore.config import Config

R2_ACCOUNT_ID = env("R2_ACCOUNT_ID", "fac9808c757df31d797190c529aaa71a")
R2_ACCESS_KEY_ID = env("R2_ACCESS_KEY_ID", "f283c44d6346fe3577067aeda789fd56")
R2_SECRET_ACCESS_KEY = env("R2_SECRET_ACCESS_KEY", "03b9bc340fee3b087cdf9fb2fd9c69782d515ad1a22073cbbc5cc5550da42a8e")
R2_BUCKET = env("R2_BUCKET_NAME", "hotissue-images")
R2_PUBLIC_URL = env("R2_PUBLIC_URL", "https://pub-2f5c7af1c303419a933069212bc25874.r2.dev")
R2_ENDPOINT = env("R2_ENDPOINT", f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com")

R2_PREFIX = "blog-thumbnails"


def get_client():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )


def upload_file(local_path: str, slug: str) -> str | None:
    """
    로컬 썸네일 파일을 R2에 업로드.
    반환: R2 퍼블릭 URL 또는 None (실패 시)
    """
    r2_key = f"{R2_PREFIX}/{slug}.jpg"
    try:
        client = get_client()
        with open(local_path, "rb") as f:
            client.put_object(
                Bucket=R2_BUCKET,
                Key=r2_key,
                Body=f,
                ContentType="image/jpeg",
                CacheControl="public, max-age=31536000, immutable",
            )
        url = f"{R2_PUBLIC_URL}/{r2_key}"
        print(f"  [r2] 업로드 완료: {r2_key}")
        return url
    except Exception as e:
        print(f"  [r2] 업로드 실패 {r2_key}: {e}")
        return None


def file_exists(slug: str) -> bool:
    """R2에 해당 썸네일이 이미 있는지 확인"""
    r2_key = f"{R2_PREFIX}/{slug}.jpg"
    try:
        client = get_client()
        client.head_object(Bucket=R2_BUCKET, Key=r2_key)
        return True
    except Exception:
        return False


def get_public_url(slug: str) -> str:
    """R2 퍼블릭 URL 반환"""
    return f"{R2_PUBLIC_URL}/{R2_PREFIX}/{slug}.jpg"
