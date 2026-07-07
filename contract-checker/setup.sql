-- 1. データベース作成（postgresなど管理者権限で実行）
CREATE DATABASE riskcheck;

-- 2. ユーザー作成
CREATE USER appuser WITH PASSWORD 'apppassword';

-- 3. riskcheck データベースに接続してから実行
\c riskcheck

-- 4. スキーマへの接続・利用権限
GRANT CONNECT ON DATABASE riskcheck TO appuser;
GRANT USAGE ON SCHEMA public TO appuser;

-- 5. 既存テーブルに対するDML権限のみ付与（CREATE/DROP/ALTERは付与しない）
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO appuser;

-- 6. 既存シーケンスへのUSAGE権限（SERIAL/IDENTITY列を使う場合、INSERT時に必要）
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO appuser;

-- 7. 今後 postgres ユーザーが作成するテーブル・シーケンスにも
--    自動的に同じDML権限が付与されるようにする（appuser自身のCREATE権限は不要）
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO appuser;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO appuser;