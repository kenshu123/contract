# ── ベースイメージ ──────────────────────────────────────────────
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ── Linux パッケージの更新（セキュリティパッチ適用） ───────────
# && rm -rf /var/lib/apt/lists/* でキャッシュを削除しイメージを軽量に保つ
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── venv を作成してその中にインストール ────────────────────────
# --prefix より確実。/venv ごと次ステージへ渡す
RUN python -m venv /venv

COPY requirements.txt .

# venv の pip を使ってインストール
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt


# ── 本番ステージ ───────────────────────────────────────────────
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ── Linux パッケージの更新（セキュリティパッチ適用） ───────────
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ── 非 root ユーザーの作成 ─────────────────────────────────────
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# ── ビルド済み venv を builder からコピー ──────────────────────
COPY --from=builder /venv /venv

# ── venv のバイナリを PATH に追加 ──────────────────────────────
ENV PATH="/venv/bin:$PATH"

# ── 実行時に外部から注入する設定値（値はここに書かない） ──────
ENV DATABASE_URL=""

# ── アプリケーションコードをコピー ────────────────────────────
COPY --chown=appuser:appgroup . .
RUN chmod +x /app/migrate.sh

# ── 実行ユーザーを非 root に切り替え ──────────────────────────
USER appuser

EXPOSE 8000

CMD ["uvicorn", "server:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4"]
