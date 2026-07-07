ALTER TABLE contract_risk_checks
    ADD COLUMN IF NOT EXISTS content_hash CHAR(64);

UPDATE contract_risk_checks
    SET content_hash = encode(sha256(contract_text::bytea), 'hex')
    WHERE content_hash IS NULL;

-- 重複ハッシュのうち最古の行だけ残して残りを削除
DELETE FROM contract_risk_checks
    WHERE id IN (
        SELECT id
        FROM (
            SELECT id,
                   ROW_NUMBER() OVER (PARTITION BY content_hash ORDER BY id) AS rn
            FROM contract_risk_checks
        ) ranked
        WHERE rn > 1
    );

ALTER TABLE contract_risk_checks
    ALTER COLUMN content_hash SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_contract_risk_checks_content_hash
    ON contract_risk_checks (content_hash);
