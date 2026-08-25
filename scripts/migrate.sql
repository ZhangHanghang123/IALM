-- IALM Schema migration: 新增 5 张表
-- 4.9 产品-资产关联
CREATE TABLE IF NOT EXISTS ialm_product_asset_link (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    company_id      BIGINT        NOT NULL,
    product_type_id BIGINT        NOT NULL,
    asset_category_id BIGINT      NOT NULL,
    allocation_pct  DECIMAL(6,4)  NOT NULL DEFAULT 0,
    duration_match  DECIMAL(8,4)  NOT NULL DEFAULT 0,
    remark          VARCHAR(256)  NOT NULL DEFAULT '',
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_link (company_id, product_type_id, asset_category_id),
    INDEX idx_product (product_type_id),
    INDEX idx_asset_cat (asset_category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='产品-资产配置关联';

-- 4.10 死亡率表
CREATE TABLE IF NOT EXISTS ialm_mortality_table (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    table_code      VARCHAR(64)   NOT NULL,
    table_name      VARCHAR(128)  NOT NULL,
    gender          VARCHAR(8)    NOT NULL,
    age_min         INT           NOT NULL DEFAULT 0,
    age_max         INT           NOT NULL DEFAULT 120,
    source          VARCHAR(128)  DEFAULT '',
    description     VARCHAR(512)  DEFAULT '',
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_table_code (table_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='死亡率表';

-- 4.11 死亡率表点
CREATE TABLE IF NOT EXISTS ialm_mortality_table_point (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    table_id        BIGINT        NOT NULL,
    age             INT           NOT NULL,
    qx              DECIMAL(10,8) NOT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_table_age (table_id, age)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='死亡率表点';

-- 4.12 退保率
CREATE TABLE IF NOT EXISTS ialm_lapse_rate (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    rate_code       VARCHAR(64)   NOT NULL,
    rate_name       VARCHAR(128)  NOT NULL,
    product_type_id BIGINT        DEFAULT NULL,
    policy_year_min INT           NOT NULL DEFAULT 1,
    policy_year_max INT           NOT NULL DEFAULT 50,
    rate_value      DECIMAL(8,6)  NOT NULL DEFAULT 0,
    extra_json      JSON          DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_rate_code (rate_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='退保率';

-- 4.13 精算假设集
CREATE TABLE IF NOT EXISTS ialm_actuarial_assumption (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    company_id      BIGINT        NOT NULL,
    product_type_id BIGINT        DEFAULT NULL,
    assumption_set_code VARCHAR(64) NOT NULL,
    effective_date  DATE          NOT NULL,
    expiry_date     DATE          DEFAULT NULL,
    mortality_table_code VARCHAR(64) DEFAULT '',
    lapse_rate_code VARCHAR(64)   DEFAULT '',
    expense_rate_code VARCHAR(64) DEFAULT '',
    discount_rate   DECIMAL(6,4)  NOT NULL DEFAULT 0,
    extra_json      JSON          DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_company_effective (company_id, effective_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='精算假设集';

-- ============================================================
-- 兼容修复：给缺 is_deleted 列的表补上（用动态 SQL）
-- ============================================================
DROP PROCEDURE IF EXISTS _migrate_add_columns;
DELIMITER //
CREATE PROCEDURE _migrate_add_columns()
BEGIN
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='ialm_db' AND TABLE_NAME='ialm_asset_cashflow' AND COLUMN_NAME='is_deleted') THEN
        ALTER TABLE ialm_asset_cashflow ADD COLUMN is_deleted TINYINT NOT NULL DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='ialm_db' AND TABLE_NAME='ialm_liability_cashflow' AND COLUMN_NAME='is_deleted') THEN
        ALTER TABLE ialm_liability_cashflow ADD COLUMN is_deleted TINYINT NOT NULL DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='ialm_db' AND TABLE_NAME='ialm_reserve' AND COLUMN_NAME='is_deleted') THEN
        ALTER TABLE ialm_reserve ADD COLUMN is_deleted TINYINT NOT NULL DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='ialm_db' AND TABLE_NAME='ialm_mortality_table_point' AND COLUMN_NAME='is_deleted') THEN
        ALTER TABLE ialm_mortality_table_point ADD COLUMN is_deleted TINYINT NOT NULL DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='ialm_db' AND TABLE_NAME='ialm_reserve' AND COLUMN_NAME='updated_at') THEN
        ALTER TABLE ialm_reserve ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
    END IF;
END //
DELIMITER ;
CALL _migrate_add_columns();
DROP PROCEDURE _migrate_add_columns;

