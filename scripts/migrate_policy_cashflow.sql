-- 给 ialm_liability_cashflow 加 policy_id 字段（实现按保单筛选现金流）
ALTER TABLE ialm_liability_cashflow ADD COLUMN policy_id BIGINT DEFAULT NULL AFTER product_type_id;
CREATE INDEX idx_liab_cf_policy ON ialm_liability_cashflow (policy_id);