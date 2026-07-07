CREATE TABLE IF NOT EXISTS contract_risk_checks (
    id            BIGSERIAL     PRIMARY KEY,
    contract_text TEXT          NOT NULL,
    risk_result   JSONB         NOT NULL,
    checked_at    TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_contract_risk_checks_checked_at ON contract_risk_checks (checked_at);
CREATE INDEX IF NOT EXISTS idx_contract_risk_checks_risk_result ON contract_risk_checks USING gin (risk_result);
