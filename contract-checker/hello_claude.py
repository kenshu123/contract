import os
import sys

from dotenv import load_dotenv
from anthropic import Anthropic

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

MODEL = "claude-haiku-4-5-20251001"
USER_MESSAGE = "この契約書全体の要約を3行でまとめてください"


def main():
    with client.messages.stream(
        model=MODEL,
        max_tokens=50,
        messages=[{"role": "user", "content": USER_MESSAGE}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
