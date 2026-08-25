-- ═══ 资产持仓：增加还息/还本频率 + 频率单位字段 ═══

-- 1. 加 4 个新字段
ALTER TABLE ialm_asset_holding
    ADD COLUMN interest_payment_freq INT NOT NULL DEFAULT 1 AFTER payment_freq,
    ADD COLUMN interest_payment_unit VARCHAR(16) NOT NULL DEFAULT 'YEAR' AFTER interest_payment_freq,
    ADD COLUMN principal_payment_freq INT NOT NULL DEFAULT 0 AFTER interest_payment_unit,
    ADD COLUMN principal_payment_unit VARCHAR(16) NOT NULL DEFAULT 'YEAR' AFTER principal_payment_freq;

-- 2. 加 COMMENT（MySQL 不支持 ADD COLUMN 中带 COMMENT，必须 ALTER）
ALTER TABLE ialm_asset_holding
    MODIFY COLUMN interest_payment_freq INT NOT NULL DEFAULT 1 COMMENT '还息频率（数值）',
    MODIFY COLUMN interest_payment_unit VARCHAR(16) NOT NULL DEFAULT 'YEAR' COMMENT '还息频率单位（DAY/WEEK/MONTH/QUARTER/HALF_YEAR/YEAR）',
    MODIFY COLUMN principal_payment_freq INT NOT NULL DEFAULT 0 COMMENT '还本频率（0 = 到期一次性）',
    MODIFY COLUMN principal_payment_unit VARCHAR(16) NOT NULL DEFAULT 'YEAR' COMMENT '还本频率单位';

-- 3. 兼容老数据：把 payment_freq 拷贝到 interest_payment_freq
UPDATE ialm_asset_holding SET interest_payment_freq = payment_freq WHERE interest_payment_freq = 1 AND payment_freq != 1;

-- 4. 删除旧的 payment_freq
ALTER TABLE ialm_asset_holding DROP COLUMN payment_freq;

-- 5. 索引
CREATE INDEX idx_holding_int_unit ON ialm_asset_holding (interest_payment_unit, interest_payment_freq);
CREATE INDEX idx_holding_prn_unit ON ialm_asset_holding (principal_payment_unit, principal_payment_freq);