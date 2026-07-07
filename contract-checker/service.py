import logging
import time
import traceback

import psycopg2
from botocore.exceptions import ClientError

from fastapi import HTTPException

from app.bedrock import generate

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_INITIAL_WAIT = 1.0
_MAX_WAIT = 8.0

# Bedrock error codes that are not worth retrying
_NON_RETRYABLE_CODES = {
    "AccessDeniedException",
    "ValidationException",
    "ResourceNotFoundException",
    "ModelNotReadyException",
}


def call_bedrock(prompt: str, model_id: str, region: str, system: str = "") -> str:
    """
    Bedrock generate() を呼び出す。
    - ThrottlingException: 指数バックオフでリトライ（最大 3 回、初期 1 秒、上限 8 秒）
    - 認証・バリデーション系エラー: 即座に 500
    - その他の ClientError: 即座に 500
    """
    wait = _INITIAL_WAIT
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return generate(prompt, model_id=model_id, region=region, system=system)
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            location = traceback.extract_tb(exc.__traceback__)[-1]
            if code == "ThrottlingException":
                logger.error(
                    "[ThrottlingException] at %s:%d — attempt %d/%d",
                    location.filename,
                    location.lineno,
                    attempt + 1,
                    _MAX_RETRIES + 1,
                )
                if attempt == _MAX_RETRIES:
                    raise HTTPException(status_code=429, detail="Bedrock のレート制限に達しました。しばらくしてから再試行してください。")
                logger.info("%.1f 秒後にリトライします…", wait)
                time.sleep(wait)
                wait = min(wait * 2, _MAX_WAIT)
            elif code in _NON_RETRYABLE_CODES:
                logger.error(
                    "[%s] 回復不能エラー at %s:%d — %s",
                    code,
                    location.filename,
                    location.lineno,
                    exc,
                )
                raise HTTPException(status_code=500, detail=f"Bedrock エラー: {code}")
            else:
                logger.error(
                    "[ClientError:%s] at %s:%d — %s",
                    code,
                    location.filename,
                    location.lineno,
                    exc,
                )
                raise HTTPException(status_code=500, detail=f"Bedrock エラー: {code}")


def run_db(fn, *args, **kwargs):
    """
    DB 操作をラップする。psycopg2.OperationalError は 503 を返す。
    """
    try:
        return fn(*args, **kwargs)
    except psycopg2.OperationalError as exc:
        location = traceback.extract_tb(exc.__traceback__)[-1]
        logger.error(
            "[%s] DB接続エラー at %s:%d — %s",
            type(exc).__name__,
            location.filename,
            location.lineno,
            exc,
        )
        raise HTTPException(status_code=503, detail="データベースに接続できません。しばらくしてから再試行してください。")
