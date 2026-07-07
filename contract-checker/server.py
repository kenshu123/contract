import logging
import sys
import json
import os
import re
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import Response
from dotenv import load_dotenv, dotenv_values
from storage import save_check, find_by_hash, _sha256
from service import call_bedrock, run_db
from app.auth import verify_api_key
from app.config import BEDROCK_MODEL_ID, BEDROCK_REGION, SYSTEM_PROMPT
from app.schemas import CheckRequest, CheckResponse, RiskItem

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

load_dotenv(override=False)

app = FastAPI()

SEVERITY_LABELS = {"high": "高", "medium": "中", "low": "低"}


def mask(key: str, value: str) -> str:
    sensitive = ("KEY", "SECRET", "TOKEN", "PASSWORD")
    if any(word in key.upper() for word in sensitive):
        return value[:8] + "..." if len(value) > 8 else "***"
    return value


@app.on_event("startup")
def startup():
    config = {**dotenv_values(".env"), **os.environ}
    print("=== env ===")
    for key, value in config.items():
        print(f"  {key}={mask(key, value)}")
    print("===========")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/check", response_model=CheckResponse)
async def check(body: CheckRequest, _: None = Depends(verify_api_key)):
    cached_row = run_db(find_by_hash, _sha256(body.text))
    if cached_row is not None:
        return CheckResponse(
            id=cached_row["id"],
            cached=True,
            risks=[
                RiskItem(
                    clause=r.get("clause", ""),
                    severity=r.get("severity", "unknown"),
                    severity_label=SEVERITY_LABELS.get(r.get("severity", ""), r.get("severity", "")),
                    reason=r.get("reason", ""),
                )
                for r in cached_row["risk_result"]
            ],
        )

    user_message = f"以下の契約書を確認してください。\n\n{body.text}"

    response_text = call_bedrock(
        user_message,
        model_id=BEDROCK_MODEL_ID,
        region=BEDROCK_REGION,
        system=SYSTEM_PROMPT,
    )
    response_text = response_text.strip()
    response_text = re.sub(r"^```(?:json)?|```$", "", response_text, flags=re.MULTILINE).strip()

    try:
        risks = json.loads(response_text)
    except json.JSONDecodeError:
        print("=== JSON解析失敗: モデルの生出力 ===")
        print(response_text)
        print("===================================")
        raise HTTPException(status_code=500, detail="モデルの出力をJSONとして解析できませんでした。")

    result = [
        RiskItem(
            clause=r.get("clause", ""),
            severity=r.get("severity", "unknown"),
            severity_label=SEVERITY_LABELS.get(r.get("severity", ""), r.get("severity", "")),
            reason=r.get("reason", ""),
        )
        for r in risks
    ]

    save_result = run_db(save_check, body.text, [item.model_dump() for item in result])

    return CheckResponse(id=save_result.id, cached=save_result.cached, risks=result)
