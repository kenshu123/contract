import argparse
import json
import re
import sys

from dotenv import load_dotenv

from app.bedrock import generate
from app.config import BEDROCK_MODEL_ID, BEDROCK_REGION, SYSTEM_PROMPT

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

SEVERITY_LABELS = {"high": "高", "medium": "中", "low": "低"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path")
    args = parser.parse_args()

    with open(args.file_path, encoding="utf-8") as f:
        contract_text = f.read()

    user_message = f"以下の契約書を確認してください。\n\n{contract_text}"

    response_text = generate(
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
        print("JSONの解析に失敗しました。モデルの生出力:")
        print(response_text)
        return

    if not risks:
        print("リスク条項は見つかりませんでした。")
        return

    for risk in risks:
        severity = risk.get("severity", "unknown")
        label = SEVERITY_LABELS.get(severity, severity)
        print(f"[{label}] {risk.get('clause', '')}")
        print(f"  理由: {risk.get('reason', '')}")
        print()


if __name__ == "__main__":
    main()
