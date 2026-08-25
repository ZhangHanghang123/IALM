-- ═══ 期限单位字典表 ═══
CREATE TABLE IF NOT EXISTS ialm_period_unit_dict (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    unit_code       VARCHAR(16)   NOT NULL COMMENT 'DAY/WEEK/MONTH/QUARTER/HALF_YEAR/YEAR',
    unit_name       VARCHAR(32)   NOT NULL COMMENT '日/周/月/季/半年/年',
    days_per_unit   DECIMAL(8,2)  NOT NULL DEFAULT 1 COMMENT '每个单位的天数（用于折算年）',
    sort_order      INT           NOT NULL DEFAULT 0,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_unit_code (unit_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='期限单位字典';

-- 预填字典
INSERT IGNORE INTO ialm_period_unit_dict (unit_code, unit_name, days_per_unit, sort_order) VALUES
('DAY',       '日',    1.00,   1),
('WEEK',      '周',    7.00,   2),
('MONTH',     '月',   30.00,   3),
('QUARTER',   '季',   90.00,   4),
('HALF_YEAR', '半年', 180.00,   5),
('YEAR',      '年',  365.00,   6);

-- ═══ 资产现金流：新增 period_count + period_unit ═══
ALTER TABLE ialm_asset_cashflow ADD COLUMN period_count DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER period_number;
ALTER TABLE ialm_asset_cashflow ADD COLUMN period_unit  VARCHAR(16)   NOT NULL DEFAULT 'YEAR' AFTER period_count;

-- ═══ 负债现金流：新增 period_count + period_unit ═══
ALTER TABLE ialm_liability_cashflow ADD COLUMN period_count DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER period_number;
ALTER TABLE ialm_liability_cashflow ADD COLUMN period_unit  VARCHAR(16)   NOT NULL DEFAULT 'YEAR' AFTER period_count;

-- 索引：便于按期限筛选
CREATE INDEX idx_asset_cf_unit ON ialm_asset_cashflow (period_unit, period_count);
CREATE INDEX idx_liab_cf_unit ON ialm_liability_cashflow (period_unit, period_count);