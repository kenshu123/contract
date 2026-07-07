import hashlib
import json
import os
from typing import NamedTuple
from urllib.parse import quote_plus

import boto3
import psycopg2
import psycopg2.extras


def _connect():
    secret_arn = os.environ.get("DB_SECRET_ARN")
    if secret_arn:
        client = boto3.client("secretsmanager")
        secret = json.loads(client.get_secret_value(SecretId=secret_arn)["SecretString"])
        dsn = (
            f"postgresql://{quote_plus(secret['username'])}:{quote_plus(secret['password'])}"
            f"@{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', '5432')}/{os.environ['DB_NAME']}"
        )
        return psycopg2.connect(dsn)
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class SaveResult(NamedTuple):
    id: int
    cached: bool


def save_check(text: str, result: dict) -> SaveResult:
    content_hash = _sha256(text)
    sql_insert = """
        INSERT INTO contract_risk_checks (contract_text, content_hash, risk_result)
        VALUES (%s, %s, %s)
        ON CONFLICT (content_hash) DO NOTHING
        RETURNING id
    """
    sql_select = """
        SELECT id FROM contract_risk_checks WHERE content_hash = %s
    """
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql_insert, (text, content_hash, json.dumps(result, ensure_ascii=False)))
        row = cur.fetchone()
        if row is not None:
            return SaveResult(id=row[0], cached=False)
        cur.execute(sql_select, (content_hash,))
        return SaveResult(id=cur.fetchone()[0], cached=True)


def find_by_hash(content_hash: str) -> dict | None:
    sql = """
        SELECT id, risk_result
        FROM contract_risk_checks
        WHERE content_hash = %s
    """
    with _connect() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (content_hash,))
        row = cur.fetchone()
    if row is None:
        return None
    return {"id": row["id"], "risk_result": row["risk_result"]}


def get_check(check_id: int) -> dict | None:
    sql = """
        SELECT id, contract_text, risk_result, checked_at
        FROM contract_risk_checks
        WHERE id = %s
    """
    with _connect() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (check_id,))
        row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "contract_text": row["contract_text"],
        "risk_result": row["risk_result"],
        "checked_at": row["checked_at"].isoformat(),
    }


def list_checks() -> list[dict]:
    sql = """
        SELECT id, contract_text, risk_result, checked_at
        FROM contract_risk_checks
        ORDER BY checked_at DESC
    """
    with _connect() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return [
        {
            "id": row["id"],
            "contract_text": row["contract_text"],
            "risk_result": row["risk_result"],
            "checked_at": row["checked_at"].isoformat(),
        }
        for row in rows
    ]
