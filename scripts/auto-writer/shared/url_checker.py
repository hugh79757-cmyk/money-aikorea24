"""
URL Alive 검증 모듈 — 서비스 URL이 실제 존재하는지 확인
"""
import requests
from shared.db_utils import mark_error


def check_url_alive(url: str, timeout: int = 10) -> dict:
    """
    HTTP HEAD로 URL alive 확인.
    Returns: {"alive": True/False/None, "reason": str}
    """
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return {"alive": True, "reason": "ok"}
        elif resp.status_code in (404, 410):
            return {"alive": False, "reason": "not_found"}
        else:
            return {"alive": False, "reason": f"http_{resp.status_code}"}
    except requests.exceptions.Timeout:
        return {"alive": None, "reason": "timeout"}
    except requests.exceptions.SSLError:
        return {"alive": None, "reason": "ssl_error"}
    except requests.exceptions.ConnectionError:
        return {"alive": None, "reason": "connection_error"}
    except Exception as e:
        return {"alive": None, "reason": str(e)[:100]}


def check_gov24_alive(service_id: str, detail_url: str) -> bool:
    """
    Gov24 URL 검증 + mark_error 처리.
    Returns: True (alive), False (dead/unstable → skip)
    """
    if not detail_url:
        return True

    result = check_url_alive(detail_url)

    if result["alive"] is True:
        return True

    if result["alive"] is False:
        mark_error(service_id, f"url_dead:{result['reason']}")
        print(f"  [url-check] ✗ 서비스 종료: {service_id} ({result['reason']})")
        return False

    # alive=None (timeout, ssl, connection)
    mark_error(service_id, f"url_unstable:{result['reason']}")
    print(f"  [url-check] ⚠ 불안정: {service_id} ({result['reason']})")
    return False
