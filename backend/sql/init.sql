-- ============================================================
-- 保险资产负债管理平台 (IALM) — 数据库初始化脚本
-- 设计版本: V1.0  | 设计日期: 2026-08-25
-- 关联文档:
--   - IALM_保险资产负债管理产品需求文档.md
--   - IALM_保险资产负债管理算法详细设计.md
--   - IALM_保险资产负债管理算法案例模板.xlsx
--
-- 标准化规范:
--   系统表: sys_ 前缀   业务表: ialm_ 前缀
--   公共字段: id/status/is_deleted/created_by/updated_by/created_at/updated_at
--   状态码值: TINYINT status(0=停用, 1=启用/正常)
--             VARCHAR exec_status(PENDING/RUNNING/COMPLETED/FAILED)
--             VARCHAR verify_status(PENDING/APPROVED/REJECTED)
--   JSON 字段: <name>_json
--   数据库: ialm_db (与 almd/IALMD/ALMT/CURV 共用 almd 用户)
-- ============================================================

USE ialm_db;

SET FOREIGN_KEY_CHECKS=0;

-- ============================================================
-- Part 1: 系统管理模块 (sys_) — 与 ALMD/IALMD 复用约定
-- ============================================================

-- 1.1 用户表
CREATE TABLE IF NOT EXISTS sys_user (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    username        VARCHAR(64)   NOT NULL COMMENT '登录名',
    password_hash   VARCHAR(256)  NOT NULL COMMENT '密码哈希(BCrypt)',
    real_name       VARCHAR(64)   NOT NULL DEFAULT '' COMMENT '真实姓名',
    email           VARCHAR(128)  NOT NULL DEFAULT '' COMMENT '邮箱',
    phone           VARCHAR(20)   NOT NULL DEFAULT '' COMMENT '手机号',
    company_id      BIGINT        DEFAULT NULL COMMENT '所属保险公司ID',
    avatar_url      VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '头像URL',
    last_login_at   DATETIME      DEFAULT NULL COMMENT '最后登录时间',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=正常',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_username (username),
    INDEX idx_company (company_id),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='IALM 用户表';

-- 1.2 角色表
CREATE TABLE IF NOT EXISTS sys_role (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    role_name       VARCHAR(64)   NOT NULL COMMENT '角色名称',
    role_code       VARCHAR(64)   NOT NULL COMMENT '角色编码: ALCO_CHAIR/RISK_MANAGER/ACTUARY/ASSET_MANAGER/ADMIN',
    description     VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '角色描述',
    sort_order      INT           NOT NULL DEFAULT 0 COMMENT '排序号',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=停用, 1=启用',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_role_code (role_code),
    INDEX idx_status (status, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='IALM 角色表';

-- 1.3 用户角色关联表
CREATE TABLE IF NOT EXISTS sys_user_role (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id         BIGINT        NOT NULL COMMENT '用户ID',
    role_id         BIGINT        NOT NULL COMMENT '角色ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_user_role (user_id, role_id),
    INDEX idx_role (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='用户角色关联表';

-- 1.4 权限表
CREATE TABLE IF NOT EXISTS sys_permission (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    permission_code VARCHAR(128)  NOT NULL COMMENT '权限编码: alm:report:view, stress:run',
    permission_name VARCHAR(128)  NOT NULL COMMENT '权限名称',
    parent_id       BIGINT        NOT NULL DEFAULT 0 COMMENT '父权限ID, 0=顶级',
    permission_type VARCHAR(16)   NOT NULL DEFAULT 'MENU' COMMENT '权限类型: MENU/BUTTON/API',
    sort_order      INT           NOT NULL DEFAULT 0 COMMENT '排序号',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=停用, 1=启用',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL COMMENT '创建人ID',
    updated_by      BIGINT        DEFAULT NULL COMMENT '更新人ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_permission_code (permission_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='权限表';

-- 1.5 角色权限关联表
CREATE TABLE IF NOT EXISTS sys_role_permission (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    role_id         BIGINT        NOT NULL COMMENT '角色ID',
    permission_id   BIGINT        NOT NULL COMMENT '权限ID',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_role_permission (role_id, permission_id),
    INDEX idx_permission (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='角色权限关联表';

-- 1.6 字典类型表
CREATE TABLE IF NOT EXISTS sys_dict_type (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    dict_type       VARCHAR(64)   NOT NULL COMMENT '字典类型编码',
    dict_name        VARCHAR(128)  NOT NULL COMMENT '字典名称',
    description     VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '字典描述',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=停用, 1=启用',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除, 1=已删除',
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_dict_type (dict_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='字典类型表';

-- 1.7 字典数据表
CREATE TABLE IF NOT EXISTS sys_dict_data (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    dict_type       VARCHAR(64)   NOT NULL COMMENT '字典类型编码',
    dict_label      VARCHAR(128)  NOT NULL COMMENT '字典标签',
    dict_value      VARCHAR(128)  NOT NULL COMMENT '字典值',
    sort_order      INT           NOT NULL DEFAULT 0 COMMENT '排序号',
    is_default      TINYINT       NOT NULL DEFAULT 0 COMMENT '是否默认: 0=否, 1=是',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=停用, 1=启用',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dict_type (dict_type, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='字典数据表';

-- 1.8 LLM 配置表
CREATE TABLE IF NOT EXISTS sys_llm_config (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    provider        VARCHAR(64)   NOT NULL COMMENT '供应商: deepseek/openai/qwen/mock',
    model_name       VARCHAR(128)  NOT NULL COMMENT '模型名称',
    api_key         VARCHAR(512)  NOT NULL DEFAULT '' COMMENT 'API Key',
    api_base        VARCHAR(256)  NOT NULL DEFAULT '' COMMENT 'API Base URL',
    temperature     DECIMAL(3,2)  NOT NULL DEFAULT 0.70 COMMENT '温度参数',
    max_tokens      INT           NOT NULL DEFAULT 2048 COMMENT '最大输出 tokens',
    is_default      TINYINT       NOT NULL DEFAULT 0 COMMENT '是否默认启用',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态',
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_provider (provider, is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='LLM 配置表';

-- 1.9 审计日志表
CREATE TABLE IF NOT EXISTS sys_audit_log (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id         BIGINT        DEFAULT NULL COMMENT '操作用户ID',
    username        VARCHAR(64)   NOT NULL DEFAULT '' COMMENT '登录名',
    action          VARCHAR(64)   NOT NULL COMMENT '操作动作: CREATE/UPDATE/DELETE/QUERY/LOGIN',
    entity_type     VARCHAR(64)   NOT NULL COMMENT '对象类型',
    entity_id       BIGINT        DEFAULT NULL COMMENT '对象ID',
    remark          VARCHAR(512)  NOT NULL DEFAULT '' COMMENT '操作说明',
    ip_address      VARCHAR(64)   NOT NULL DEFAULT '' COMMENT 'IP 地址',
    user_agent      VARCHAR(512)  NOT NULL DEFAULT '' COMMENT 'UA',
    request_data    JSON          DEFAULT NULL COMMENT '请求数据快照',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user (user_id, created_at),
    INDEX idx_entity (entity_type, entity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='审计日志表';

-- 1.10 通知消息表
CREATE TABLE IF NOT EXISTS sys_notification (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id         BIGINT        NOT NULL COMMENT '接收用户ID',
    title           VARCHAR(128)  NOT NULL COMMENT '消息标题',
    content         TEXT          NOT NULL COMMENT '消息内容',
    level           VARCHAR(16)   NOT NULL DEFAULT 'INFO' COMMENT '级别: INFO/WARN/ERROR',
    category        VARCHAR(32)   NOT NULL DEFAULT '' COMMENT '分类: KRI/STRESS/REPORT',
    is_read         TINYINT       NOT NULL DEFAULT 0 COMMENT '是否已读: 0=否, 1=是',
    read_at         DATETIME      DEFAULT NULL COMMENT '阅读时间',
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_unread (user_id, is_read, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='通知消息表';


-- ============================================================
-- Part 2: 基础数据域 — 保险公司主档
-- ============================================================

-- 2.1 保险公司主档
CREATE TABLE IF NOT EXISTS ialm_insurance_company (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_code    VARCHAR(32)   NOT NULL COMMENT '公司编码: 金融监管局 6位 ORG_CODE',
    company_name    VARCHAR(128)  NOT NULL COMMENT '公司中文名',
    company_short   VARCHAR(64)   NOT NULL DEFAULT '' COMMENT '公司简称',
    company_type    VARCHAR(16)   NOT NULL COMMENT '公司类型: LIFE(寿险)/PROPERTY(财险)/HEALTH(健康险)/REINSURANCE(再保)/GROUP(集团)',
    legal_rep       VARCHAR(64)   NOT NULL DEFAULT '' COMMENT '法定代表人',
    registered_capital DECIMAL(18,2) DEFAULT 0 COMMENT '注册资本(万元)',
    established_at  DATE          DEFAULT NULL COMMENT '成立日期',
    business_scope  VARCHAR(512)  NOT NULL DEFAULT '' COMMENT '经营范围',
    address         VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '注册地址',
    contact_phone   VARCHAR(20)   NOT NULL DEFAULT '' COMMENT '联系电话',
    website         VARCHAR(128)  NOT NULL DEFAULT '' COMMENT '官网',
    regulatory_rating VARCHAR(16) DEFAULT '' COMMENT '监管评级: A/B/C/D',
    risk_preference_id BIGINT     DEFAULT NULL COMMENT '风险偏好ID',
    status          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态: 0=停用, 1=启用',
    is_deleted      TINYINT       NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_company_code (company_code),
    INDEX idx_company_type (company_type, is_deleted),
    INDEX idx_name (company_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='保险公司主档';


-- ============================================================
-- Part 3: 资产端数据域
-- ============================================================

-- 3.1 资产分类树 (多层级)
CREATE TABLE IF NOT EXISTS ialm_asset_category (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    category_code   VARCHAR(64)   NOT NULL COMMENT '资产分类编码',
    category_name   VARCHAR(128)  NOT NULL COMMENT '资产分类名称',
    parent_id       BIGINT        NOT NULL DEFAULT 0 COMMENT '父分类ID, 0=顶级',
    category_level  INT           NOT NULL DEFAULT 1 COMMENT '层级(1/2/3)',
    category_type   VARCHAR(32)   NOT NULL COMMENT '大类: CASH/BOND/EQUITY/FUND/ALTERNATIVE/OTHER',
    risk_weight     DECIMAL(5,4)  NOT NULL DEFAULT 0.0000 COMMENT '监管风险权重',
    duration_default DECIMAL(8,4) NOT NULL DEFAULT 0.0000 COMMENT '默认修正久期',
    sort_order      INT           NOT NULL DEFAULT 0 COMMENT '排序',
    description     VARCHAR(512)  NOT NULL DEFAULT '' COMMENT '描述',
    status          TINYINT       NOT NULL DEFAULT 1,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_category_code (category_code),
    INDEX idx_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='资产分类树';

-- 3.2 持仓明细
CREATE TABLE IF NOT EXISTS ialm_asset_holding (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL COMMENT '所属保险公司',
    asset_code      VARCHAR(64)   NOT NULL COMMENT '资产编号',
    asset_name      VARCHAR(256)  NOT NULL COMMENT '资产名称',
    category_id     BIGINT        NOT NULL COMMENT '资产分类ID',
    asset_subtype   VARCHAR(32)   DEFAULT '' COMMENT '子类型: 国债/政策性金融债/企业债/股票/...',
    issuer          VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '发行人',
    credit_rating   VARCHAR(16)   DEFAULT '' COMMENT '信用评级: AAA/AA+/A/...',
    face_value      DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '面值(万元)',
    cost_value      DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '成本(万元)',
    market_value    DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '市值(万元)',
    coupon_rate     DECIMAL(8,4)  NOT NULL DEFAULT 0 COMMENT '票面利率',
    ytm             DECIMAL(8,4)  NOT NULL DEFAULT 0 COMMENT '到期收益率(%)',
    issue_date      DATE          DEFAULT NULL COMMENT '发行日',
    maturity_date   DATE          DEFAULT NULL COMMENT '到期日',
    duration_year   DECIMAL(8,4)  NOT NULL DEFAULT 0 COMMENT '修正久期(年)',
    effective_duration DECIMAL(8,4) NOT NULL DEFAULT 0 COMMENT '有效久期',
    convexity       DECIMAL(10,4) NOT NULL DEFAULT 0 COMMENT '凸性',
    payment_freq    INT           NOT NULL DEFAULT 1 COMMENT '年付息次数',
    currency        VARCHAR(8)    NOT NULL DEFAULT 'CNY' COMMENT '币种',
    report_date     DATE          NOT NULL COMMENT '持仓日期',
    source          VARCHAR(32)   NOT NULL DEFAULT 'MANUAL' COMMENT '数据来源: MANUAL/ETL/API',
    extra_json      JSON          DEFAULT NULL COMMENT '扩展字段',
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_company_report (company_id, report_date),
    INDEX idx_category (category_id),
    INDEX idx_maturity (maturity_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='资产持仓明细';

-- 3.3 资产现金流（按期）
CREATE TABLE IF NOT EXISTS ialm_asset_cashflow (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    holding_id      BIGINT        NOT NULL COMMENT '持仓ID',
    company_id      BIGINT        NOT NULL COMMENT '保险公司ID',
    asset_code      VARCHAR(64)   NOT NULL COMMENT '资产编号',
    period_number   INT           NOT NULL COMMENT '期数(从1开始)',
    period_date     DATE          NOT NULL COMMENT '现金流日期',
    period_year     DECIMAL(6,2)  NOT NULL COMMENT '距离报告日期的年数',
    cashflow_type   VARCHAR(16)   NOT NULL COMMENT '现金流类型: COUPON(息票)/PRINCIPAL(本金)/REINVEST(再投资)/TOTAL',
    amount          DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '现金流金额(万元,正为流入)',
    discount_factor DECIMAL(10,6) NOT NULL DEFAULT 1.0 COMMENT '折现因子',
    present_value   DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '现值',
    scenario_code   VARCHAR(32)   DEFAULT 'BASE' COMMENT '对应情景: BASE/UP200/DOWN200/STRESS',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_holding_period (holding_id, period_number),
    INDEX idx_company_scenario (company_id, scenario_code, period_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='资产现金流';

-- 3.4 资产风险指标（VaR/信用/集中度）
CREATE TABLE IF NOT EXISTS ialm_asset_risk_metric (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    report_date     DATE          NOT NULL,
    asset_code      VARCHAR(64)   DEFAULT NULL COMMENT '单资产 (为空时为组合)',
    metric_type     VARCHAR(32)   NOT NULL COMMENT '指标类型: VAR/CVAR/CREDIT_EXPOSURE/CONCENTRATION',
    confidence_level DECIMAL(4,3) NOT NULL DEFAULT 0.950 COMMENT '置信度(95%/99%)',
    horizon_days    INT           NOT NULL DEFAULT 1 COMMENT '持有期(天)',
    value           DECIMAL(18,6) NOT NULL DEFAULT 0 COMMENT '指标值',
    unit            VARCHAR(16)   NOT NULL DEFAULT 'PCT' COMMENT '单位: PCT/万元/PCT_OF_TOTAL',
    extra_json      JSON          DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_date (company_id, report_date, metric_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='资产风险指标';


-- ============================================================
-- Part 4: 负债端数据域
-- ============================================================

-- 4.1 产品分类树
CREATE TABLE IF NOT EXISTS ialm_product_category (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    product_type_code VARCHAR(64) NOT NULL COMMENT '产品类型编码',
    product_type_name VARCHAR(128) NOT NULL COMMENT '产品类型名称',
    parent_id       BIGINT        NOT NULL DEFAULT 0 COMMENT '父分类ID, 0=顶级',
    category_level  INT           NOT NULL DEFAULT 1 COMMENT '层级',
    insurance_type  VARCHAR(16)   NOT NULL COMMENT '险种类别: LIFE/HEALTH/ACCIDENT/ANNUNITY/UNIVERSAL/INVESTMENT_LINK',
    duration_type   VARCHAR(16)   DEFAULT '' COMMENT '期限类型: SHORT_TERM/LONG_TERM/WHOLE_LIFE',
    payment_type    VARCHAR(16)   DEFAULT '' COMMENT '缴费方式: SINGLE(趸交)/REGULAR(期交)',
    is_risk_account  TINYINT       NOT NULL DEFAULT 0 COMMENT '是否风险账户(回正期≤5年要求): 0=否, 1=是',
    sort_order      INT           NOT NULL DEFAULT 0,
    description     VARCHAR(512)  NOT NULL DEFAULT '',
    status          TINYINT       NOT NULL DEFAULT 1,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_product_type_code (product_type_code),
    INDEX idx_parent (parent_id),
    INDEX idx_insurance_type (insurance_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='保险产品分类树';

-- 4.2 保单主档
CREATE TABLE IF NOT EXISTS ialm_policy_master (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL COMMENT '所属保险公司',
    policy_no       VARCHAR(64)   NOT NULL COMMENT '保单号',
    product_type_id BIGINT        NOT NULL COMMENT '产品类型ID',
    product_name    VARCHAR(128)  NOT NULL DEFAULT '' COMMENT '产品名称',
    policyholder_id VARCHAR(64)   DEFAULT '' COMMENT '投保人证件号',
    insured_id      VARCHAR(64)   DEFAULT '' COMMENT '被保人身份证号',
    insured_age     INT           DEFAULT NULL COMMENT '投保年龄',
    insured_gender  VARCHAR(8)    DEFAULT '' COMMENT '性别: M/F',
    sum_insured     DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '保额(万元)',
    annual_premium  DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '年保费(万元)',
    single_premium  DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '趸交保费(万元)',
    payment_freq    INT           NOT NULL DEFAULT 1 COMMENT '缴费频率(年)',
    payment_period  INT           NOT NULL DEFAULT 0 COMMENT '缴费期(年)',
    insurance_period INT          NOT NULL DEFAULT 0 COMMENT '保险期间(年)',
    issue_date      DATE          DEFAULT NULL COMMENT '销售日期',
    effective_date  DATE          DEFAULT NULL COMMENT '生效日期',
    maturity_date   DATE          DEFAULT NULL COMMENT '满期日期',
    status          VARCHAR(16)   NOT NULL DEFAULT 'IN_FORCE' COMMENT '状态: IN_FORCE/LAPSED/MATURED/SURRENDERED',
    currency        VARCHAR(8)    NOT NULL DEFAULT 'CNY' COMMENT '币种',
    reserve_balance DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '准备金余额',
    extra_json      JSON          DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_company_policy (company_id, policy_no),
    INDEX idx_product (product_type_id),
    INDEX idx_effective (effective_date),
    INDEX idx_maturity (maturity_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='保单主档';

-- 4.3 准备金
CREATE TABLE IF NOT EXISTS ialm_reserve (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    report_date     DATE          NOT NULL COMMENT '报告日期',
    reserve_type    VARCHAR(32)   NOT NULL COMMENT '准备金类型: UNEARNED_PREMIUM/OUTSTANDING_CLAIMS/IBNR/LIFE/LIABILITY/CSM/EV',
    product_type_id BIGINT        DEFAULT NULL COMMENT '产品类型ID(可空=全公司)',
    amount          DECIMAL(20,4) NOT NULL DEFAULT 0 COMMENT '准备金金额(万元)',
    currency        VARCHAR(8)    NOT NULL DEFAULT 'CNY',
    accounting_basis VARCHAR(16)  NOT NULL DEFAULT 'CHINA_GAAP' COMMENT '会计准则: CHINA_GAAP/IFRS17',
    extra_json      JSON          DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_date (company_id, report_date, reserve_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='准备金';

-- 4.4 精算假设集
CREATE TABLE IF NOT EXISTS ialm_actuarial_assumption (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    product_type_id BIGINT        DEFAULT NULL COMMENT '产品类型ID(空=全公司)',
    assumption_set_code VARCHAR(64) NOT NULL COMMENT '假设集编码',
    effective_date  DATE          NOT NULL COMMENT '生效日期',
    expiry_date     DATE          DEFAULT NULL COMMENT '失效日期',
    mortality_table_code VARCHAR(64) DEFAULT '' COMMENT '使用的死亡率表编码',
    lapse_rate_code VARCHAR(64)   DEFAULT '' COMMENT '退保率假设编码',
    expense_rate_code VARCHAR(64) DEFAULT '' COMMENT '费用率假设编码',
    discount_rate   DECIMAL(6,4)  NOT NULL DEFAULT 0 COMMENT '折现率',
    extra_json      JSON          DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_company_effective (company_id, effective_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='精算假设集';

-- 4.5 死亡率表
CREATE TABLE IF NOT EXISTS ialm_mortality_table (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    table_code      VARCHAR(64)   NOT NULL COMMENT '表编码: CL1-CL6/经验表',
    table_name      VARCHAR(128)  NOT NULL COMMENT '表名称',
    gender          VARCHAR(8)    NOT NULL COMMENT 'M/F/MIXED',
    age_min         INT           NOT NULL DEFAULT 0,
    age_max         INT           NOT NULL DEFAULT 120,
    source          VARCHAR(128)  DEFAULT '' COMMENT '数据来源',
    description     VARCHAR(512)  DEFAULT '',
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_table_code (table_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='死亡率表';

-- 4.6 死亡率表点
CREATE TABLE IF NOT EXISTS ialm_mortality_table_point (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    table_id        BIGINT        NOT NULL,
    age             INT           NOT NULL,
    qx              DECIMAL(10,8) NOT NULL COMMENT '死亡率',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_table_age (table_id, age)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='死亡率表点';

-- 4.7 退保率假设
CREATE TABLE IF NOT EXISTS ialm_lapse_rate (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    rate_code       VARCHAR(64)   NOT NULL COMMENT '退保率编码',
    rate_name       VARCHAR(128)  NOT NULL,
    product_type_id BIGINT        DEFAULT NULL,
    policy_year_min INT           NOT NULL DEFAULT 1,
    policy_year_max INT           NOT NULL DEFAULT 50,
    rate_value      DECIMAL(8,6)  NOT NULL DEFAULT 0 COMMENT '退保率(小数)',
    extra_json      JSON          DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_rate_code (rate_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='退保率假设';

-- 4.8 负债现金流
CREATE TABLE IF NOT EXISTS ialm_liability_cashflow (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    product_type_id BIGINT        DEFAULT NULL,
    period_number   INT           NOT NULL,
    period_date     DATE          NOT NULL,
    period_year     DECIMAL(6,2)  NOT NULL,
    cashflow_type   VARCHAR(16)   NOT NULL COMMENT 'PREMIUM_IN(保费流入)/CLAIM_OUT(赔付支出)/SURRENDER_OUT(退保支出)/EXPENSE_OUT(费用支出)/BENEFIT_OUT(给付)/TOTAL',
    amount          DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '现金流金额(万元,正为流入)',
    discount_factor DECIMAL(10,6) NOT NULL DEFAULT 1.0,
    present_value   DECIMAL(18,4) NOT NULL DEFAULT 0,
    scenario_code   VARCHAR(32)   DEFAULT 'BASE',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_scenario (company_id, scenario_code, period_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='负债现金流';


-- ============================================================
-- Part 5: 市场数据域
-- ============================================================

-- 5.1 收益率曲线(类型)
CREATE TABLE IF NOT EXISTS ialm_yield_curve (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    curve_code      VARCHAR(64)   NOT NULL COMMENT '曲线编码: GOVT_BOND/POLICY_FIN_BOND/CREDIT_BOND/SHIBOR',
    curve_name      VARCHAR(128)  NOT NULL COMMENT '曲线名称',
    curve_type      VARCHAR(16)   NOT NULL COMMENT '曲线类型: SPOT(即期)/FORWARD(远期)/PAR(平价)/YIELD_TO_MAT',
    currency        VARCHAR(8)    NOT NULL DEFAULT 'CNY',
    data_source     VARCHAR(32)   NOT NULL DEFAULT 'WIND' COMMENT '数据源: WIND/CHOICE/MANUAL',
    description     VARCHAR(512)  DEFAULT '',
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_curve_code (curve_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='收益率曲线';

-- 5.2 收益率曲线点
CREATE TABLE IF NOT EXISTS ialm_yield_curve_point (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    curve_id        BIGINT        NOT NULL,
    curve_date      DATE          NOT NULL COMMENT '日期',
    tenor           DECIMAL(6,2)  NOT NULL COMMENT '期限(年): 0.083/0.25/0.5/1/2/3/5/7/10/20/30',
    rate            DECIMAL(8,4)  NOT NULL COMMENT '利率(%)',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_curve_date_tenor (curve_id, curve_date, tenor),
    INDEX idx_curve_date (curve_id, curve_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='收益率曲线点';

-- 5.3 汇率数据
CREATE TABLE IF NOT EXISTS ialm_fx_rate (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    currency_pair   VARCHAR(16)   NOT NULL COMMENT '货币对: USD/CNY',
    rate_date       DATE          NOT NULL,
    bid_rate        DECIMAL(10,6) NOT NULL COMMENT '买入价',
    ask_rate        DECIMAL(10,6) NOT NULL COMMENT '卖出价',
    mid_rate        DECIMAL(10,6) NOT NULL COMMENT '中间价',
    data_source     VARCHAR(32)   NOT NULL DEFAULT 'WIND',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_pair_date (currency_pair, rate_date),
    INDEX idx_pair_date (currency_pair, rate_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='汇率数据';

-- 5.4 股票指数
CREATE TABLE IF NOT EXISTS ialm_equity_index (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    index_code      VARCHAR(64)   NOT NULL COMMENT '指数编码: SHCOMP/SZCOMP/HS300/CYBER/...',
    index_name      VARCHAR(128)  NOT NULL,
    trade_date      DATE          NOT NULL,
    open_price      DECIMAL(12,4) NOT NULL DEFAULT 0,
    high_price      DECIMAL(12,4) NOT NULL DEFAULT 0,
    low_price       DECIMAL(12,4) NOT NULL DEFAULT 0,
    close_price     DECIMAL(12,4) NOT NULL DEFAULT 0,
    volume          BIGINT        NOT NULL DEFAULT 0,
    amount          DECIMAL(20,4) NOT NULL DEFAULT 0,
    change_rate        DECIMAL(8,4)  NOT NULL DEFAULT 0 COMMENT '涨跌幅(%)',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_index_date (index_code, trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='股票指数';

-- 5.5 信用利差
CREATE TABLE IF NOT EXISTS ialm_credit_spread (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    rating          VARCHAR(8)    NOT NULL COMMENT '评级: AAA/AA+/AA/AA-/A+/A/A-',
    tenor           DECIMAL(6,2)  NOT NULL COMMENT '期限(年)',
    spread_date     DATE          NOT NULL,
    spread_bps      DECIMAL(8,2)  NOT NULL COMMENT '利差(bps)',
    data_source     VARCHAR(32)   DEFAULT 'WIND',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_rating_tenor_date (rating, tenor, spread_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='信用利差';


-- ============================================================
-- Part 6: 算法计算结果域 (5号规则核心指标 + 其他)
-- ============================================================

-- 6.1 资产负债匹配分析结果
CREATE TABLE IF NOT EXISTS ialm_match_analysis (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    report_date     DATE          NOT NULL,
    scenario_code   VARCHAR(32)   NOT NULL DEFAULT 'BASE' COMMENT '对应情景',
    duration_match_ratio DECIMAL(8,4) NOT NULL DEFAULT 0 COMMENT '期限结构匹配率(0-1)',
    duration_match_warning TINYINT NOT NULL DEFAULT 0 COMMENT '是否触发80%阈值预警: 0/1',
    cost_yield_ratio DECIMAL(8,4) NOT NULL DEFAULT 0 COMMENT '综合成本收益比',
    cost_yield_zone VARCHAR(16)  DEFAULT '' COMMENT '成本收益区间: HEALTHY/WARNING/DANGER',
    cashflow_payback_years DECIMAL(8,2) NOT NULL DEFAULT -1 COMMENT '现金流回正期(年), -1=未回正',
    payback_warning TINYINT      NOT NULL DEFAULT 0 COMMENT '是否触发5年阈值预警',
    duration_gap_years DECIMAL(8,4) NOT NULL DEFAULT 0 COMMENT '久期缺口(年)',
    asset_duration  DECIMAL(8,4)  NOT NULL DEFAULT 0,
    liability_duration DECIMAL(8,4) NOT NULL DEFAULT 0,
    nav_change_bps  DECIMAL(12,4) NOT NULL DEFAULT 0 COMMENT '100bp利率变动净资产变化',
    detail_json     JSON          DEFAULT NULL COMMENT '分险种/分账户分解',
    calculation_log TEXT          DEFAULT NULL COMMENT '计算过程日志',
    exec_status     VARCHAR(16)   NOT NULL DEFAULT 'COMPLETED' COMMENT 'PENDING/RUNNING/COMPLETED/FAILED',
    exec_elapsed_ms INT           NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_date (company_id, report_date, scenario_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='资产负债匹配分析结果(5号规则三项核心)';

-- 6.2 现金流预测结果
CREATE TABLE IF NOT EXISTS ialm_cashflow_forecast (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    report_date     DATE          NOT NULL,
    scenario_code   VARCHAR(32)   NOT NULL DEFAULT 'BASE' COMMENT 'BASE/OPTIMISTIC/PESSIMISTIC/STRESS',
    forecast_horizon_years INT    NOT NULL DEFAULT 30 COMMENT '预测年限',
    time_step       VARCHAR(8)    NOT NULL DEFAULT 'YEARLY' COMMENT 'DAILY/MONTHLY/QUARTERLY/YEARLY',
    assumption_set_code VARCHAR(64) DEFAULT '' COMMENT '精算假设集编码',
    total_pv_asset  DECIMAL(20,4) NOT NULL DEFAULT 0 COMMENT '资产端现值合计',
    total_pv_liability DECIMAL(20,4) NOT NULL DEFAULT 0 COMMENT '负债端现值合计',
    total_pv_net    DECIMAL(20,4) NOT NULL DEFAULT 0 COMMENT '净现值',
    irr            DECIMAL(8,4)  NOT NULL DEFAULT 0 COMMENT '内部收益率(%)',
    detail_json     JSON          DEFAULT NULL COMMENT '分年现金流明细 + 现值',
    exec_status     VARCHAR(16)   NOT NULL DEFAULT 'COMPLETED',
    exec_elapsed_ms INT           NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_scenario (company_id, scenario_code, report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='现金流预测结果';


-- ============================================================
-- Part 7: 压力测试域
-- ============================================================

-- 7.1 压力情景定义
CREATE TABLE IF NOT EXISTS ialm_stress_scenario (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    scenario_code   VARCHAR(64)   NOT NULL COMMENT '情景编码',
    scenario_name   VARCHAR(128)  NOT NULL COMMENT '情景名称',
    scenario_type   VARCHAR(16)   NOT NULL COMMENT '类型: INTEREST/FX/LAPSE/MORTALITY/INVESTMENT/COMPREHENSIVE/REVERSE/HISTORICAL',
    source          VARCHAR(32)   NOT NULL DEFAULT 'CUSTOM' COMMENT '来源: REGULATORY(监管)/CUSTOM(自定义)/HISTORICAL(历史)',
    description     VARCHAR(512)  DEFAULT '',
    shocks_json     JSON          NOT NULL COMMENT '冲击定义JSON: {factors: [{name, type, value}], correlations: [...]}',
    is_active       TINYINT       NOT NULL DEFAULT 1,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_scenario_code (scenario_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='压力情景定义';

-- 7.2 压力测试执行结果
CREATE TABLE IF NOT EXISTS ialm_stress_result (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    scenario_id     BIGINT        NOT NULL,
    scenario_code   VARCHAR(64)   NOT NULL,
    report_date     DATE          NOT NULL,
    asset_impact    DECIMAL(20,4) NOT NULL DEFAULT 0 COMMENT '资产端影响(万元)',
    liability_impact DECIMAL(20,4) NOT NULL DEFAULT 0 COMMENT '负债端影响(万元)',
    nav_change      DECIMAL(20,4) NOT NULL DEFAULT 0 COMMENT '净资产变化(万元)',
    nav_change_pct  DECIMAL(8,4) NOT NULL DEFAULT 0 COMMENT '净资产变化率(%)',
    solvency_ratio_before DECIMAL(8,4) NOT NULL DEFAULT 0 COMMENT '压力前偿付能力充足率',
    solvency_ratio_after DECIMAL(8,4) NOT NULL DEFAULT 0 COMMENT '压力后偿付能力充足率',
    liquidity_gap   DECIMAL(20,4) NOT NULL DEFAULT 0 COMMENT '流动性缺口(万元)',
    liquidity_gap_after DECIMAL(20,4) NOT NULL DEFAULT 0,
    is_breached     TINYINT       NOT NULL DEFAULT 0 COMMENT '是否突破阈值: 0=否, 1=是',
    detail_json     JSON          DEFAULT NULL COMMENT '多因子分解/分险种影响',
    n_paths         INT           NOT NULL DEFAULT 0 COMMENT 'Monte Carlo 路径数',
    exec_status     VARCHAR(16)   NOT NULL DEFAULT 'COMPLETED',
    exec_elapsed_ms INT           NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_scenario (company_id, scenario_code, report_date),
    INDEX idx_breach (is_breached, report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='压力测试结果';


-- ============================================================
-- Part 8: 投资组合与业绩归因域
-- ============================================================

-- 8.1 投资组合配置
CREATE TABLE IF NOT EXISTS ialm_portfolio_allocation (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    allocation_name VARCHAR(128)  NOT NULL COMMENT '配置方案名称',
    optimization_method VARCHAR(32) NOT NULL COMMENT '方法: MEAN_VARIANCE/BLACK_LITTERMAN/RISK_PARITY/EQUAL_WEIGHT',
    asset_code      VARCHAR(64)   NOT NULL,
    asset_category_id BIGINT      DEFAULT NULL,
    weight          DECIMAL(8,6)  NOT NULL DEFAULT 0 COMMENT '权重(0-1)',
    expected_return DECIMAL(8,4)  NOT NULL DEFAULT 0 COMMENT '预期年化收益率(%)',
    expected_risk   DECIMAL(8,4)  NOT NULL DEFAULT 0 COMMENT '预期年化风险(%)',
    report_date     DATE          NOT NULL,
    sharpe_ratio    DECIMAL(8,4)  NOT NULL DEFAULT 0,
    extra_json      JSON          DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_date (company_id, report_date, optimization_method)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='投资组合配置';

-- 8.2 业绩归因
CREATE TABLE IF NOT EXISTS ialm_performance_attribution (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    portfolio_code  VARCHAR(64)   NOT NULL COMMENT '组合编码',
    benchmark_code  VARCHAR(64)   NOT NULL COMMENT '基准编码',
    period_start    DATE          NOT NULL,
    period_end      DATE          NOT NULL,
    period_type     VARCHAR(16)   NOT NULL COMMENT '频率: MONTHLY/QUARTERLY/YEARLY',
    asset_category_id BIGINT      DEFAULT NULL COMMENT '资产分类ID(空=总组合)',
    total_excess    DECIMAL(8,4)  NOT NULL DEFAULT 0 COMMENT '总超额收益(%)',
    allocation_effect DECIMAL(8,4) NOT NULL DEFAULT 0 COMMENT '配置效应(%)',
    selection_effect DECIMAL(8,4) NOT NULL DEFAULT 0 COMMENT '选择效应(%)',
    interaction_effect DECIMAL(8,4) NOT NULL DEFAULT 0 COMMENT '交互效应(%)',
    detail_json     JSON          DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_period (company_id, period_end, portfolio_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='业绩归因';


-- ============================================================
-- Part 9: 监管报表域
-- ============================================================

-- 9.1 监管报表生成记录
CREATE TABLE IF NOT EXISTS ialm_regulatory_report (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    report_type     VARCHAR(32)   NOT NULL COMMENT '报表类型: QUANT_EVAL_QUARTERLY(5号规则量化季度表)/CAPABILITY_ANNUAL(能力自评年度)/STRESS_ANNUAL(压力测试年度)/MATCH_SEMIANNUAL(匹配分析半年)/MONTHLY_INFO(月度信息)',
    report_period   VARCHAR(16)   NOT NULL COMMENT '报告期: 2026Q1/2025/2025H1/202501',
    report_date     DATE          NOT NULL,
    filing_deadline DATE          DEFAULT NULL COMMENT '报送截止日期',
    file_path       VARCHAR(256)  DEFAULT '' COMMENT '报表文件路径',
    file_format     VARCHAR(16)   DEFAULT 'EXCEL' COMMENT 'EXCEL/PDF/XML',
    status          VARCHAR(16)   NOT NULL DEFAULT 'DRAFT' COMMENT 'DRAFT/GENERATED/REVIEWED/FILED',
    filed_at        DATETIME      DEFAULT NULL,
    detail_json     JSON          DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_company_type_period (company_id, report_type, report_period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='监管报表';


-- ============================================================
-- Part 10: 风险预警与偏好
-- ============================================================

-- 10.1 风险偏好
CREATE TABLE IF NOT EXISTS ialm_risk_preference (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    preference_name VARCHAR(128)  NOT NULL,
    effective_date  DATE          NOT NULL,
    expiry_date     DATE          DEFAULT NULL,
    duration_gap_min DECIMAL(8,4) NOT NULL DEFAULT -1 COMMENT '久期缺口容忍下限(年)',
    duration_gap_max DECIMAL(8,4) NOT NULL DEFAULT 1 COMMENT '久期缺口容忍上限(年)',
    duration_match_min DECIMAL(5,4) NOT NULL DEFAULT 0.80 COMMENT '期限匹配率最低要求',
    cashflow_payback_max DECIMAL(5,2) NOT NULL DEFAULT 5 COMMENT '现金流回正期最长(年)',
    cost_yield_ratio_min DECIMAL(5,4) NOT NULL DEFAULT 1.05 COMMENT '成本收益比最低',
    extra_json      JSON          DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_company_effective (company_id, effective_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='风险偏好';

-- 10.2 风险指标(KRI)实时监控
CREATE TABLE IF NOT EXISTS ialm_risk_indicator (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    indicator_code  VARCHAR(64)   NOT NULL COMMENT '指标编码: DURATION_GAP/MATCH_RATIO/PAYBACK_PERIOD/COST_YIELD_RATIO',
    indicator_name   VARCHAR(128)  NOT NULL,
    report_date     DATE          NOT NULL,
    current_value   DECIMAL(18,6) NOT NULL DEFAULT 0,
    threshold_green DECIMAL(18,6) DEFAULT NULL COMMENT '绿色区间上限',
    threshold_yellow DECIMAL(18,6) DEFAULT NULL COMMENT '黄色区间上限',
    threshold_red   DECIMAL(18,6) DEFAULT NULL COMMENT '红色阈值',
    alert_level     VARCHAR(8)    NOT NULL DEFAULT 'GREEN' COMMENT 'GREEN/YELLOW/RED',
    trend           VARCHAR(8)    DEFAULT 'STABLE' COMMENT 'UP/DOWN/STABLE',
    extra_json      JSON          DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_date (company_id, indicator_code, report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='风险指标(KRI)';

-- 10.3 风险事件
CREATE TABLE IF NOT EXISTS ialm_risk_event (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id      BIGINT        NOT NULL,
    event_code      VARCHAR(64)   NOT NULL,
    event_name      VARCHAR(128)  NOT NULL,
    event_level     VARCHAR(8)    NOT NULL COMMENT 'LOW/MEDIUM/HIGH/CRITICAL',
    event_type      VARCHAR(32)   NOT NULL COMMENT '类型: MATCH_BREACH/THRESHOLD_BREACH/STRE_FAIL/...',
    trigger_value   DECIMAL(18,6) DEFAULT 0,
    threshold_value DECIMAL(18,6) DEFAULT 0,
    trigger_date    DATETIME      DEFAULT NULL,
    status          VARCHAR(16)   NOT NULL DEFAULT 'OPEN' COMMENT 'OPEN/INVESTIGATING/RESOLVED/CLOSED',
    description     TEXT          DEFAULT NULL,
    resolution      TEXT          DEFAULT NULL,
    resolved_at     DATETIME      DEFAULT NULL,
    resolved_by     BIGINT        DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_company_status (company_id, status, event_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='风险事件';


-- ============================================================
-- Part 11: 模型管理域
-- ============================================================

-- 11.1 算法模型定义(14种)
CREATE TABLE IF NOT EXISTS ialm_model_definition (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    model_code      VARCHAR(64)   NOT NULL COMMENT '模型编码: ALG-001..ALG-014',
    model_name      VARCHAR(128)  NOT NULL COMMENT '模型名称',
    category        VARCHAR(16)   NOT NULL COMMENT '类别: MATCH/CASHFLOW/STRESS/INVESTMENT/ATTRIBUTION/RISK',
    priority        VARCHAR(8)    NOT NULL DEFAULT 'P1' COMMENT 'P0/P1/P2',
    regulatory_code VARCHAR(64)   DEFAULT '' COMMENT '对应监管条款: 5号规则/6号规则/...',
    description     VARCHAR(512)  DEFAULT '',
    algorithm_summary TEXT         DEFAULT NULL COMMENT '算法描述',
    input_schema_json JSON         DEFAULT NULL COMMENT '入参 schema',
    output_schema_json JSON        DEFAULT NULL COMMENT '出参 schema',
    status          TINYINT       NOT NULL DEFAULT 1,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_model_code (model_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='算法模型定义';

-- 11.2 模型版本
CREATE TABLE IF NOT EXISTS ialm_model_version (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    model_id        BIGINT        NOT NULL,
    version_code    VARCHAR(32)   NOT NULL COMMENT '版本号: 1.0.0',
    version_name    VARCHAR(128)  NOT NULL,
    changelog       TEXT          DEFAULT NULL,
    release_date    DATE          NOT NULL,
    is_current      TINYINT       NOT NULL DEFAULT 0 COMMENT '是否当前版本',
    parameters_json JSON          DEFAULT NULL COMMENT '默认参数',
    benchmark_metrics_json JSON    DEFAULT NULL COMMENT '基准指标',
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_model_version (model_id, version_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='模型版本';

-- 11.3 模型参数
CREATE TABLE IF NOT EXISTS ialm_model_parameter (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    model_version_id BIGINT       NOT NULL,
    param_code      VARCHAR(64)   NOT NULL COMMENT '参数编码',
    param_name      VARCHAR(128)  NOT NULL,
    param_value     VARCHAR(512)  NOT NULL DEFAULT '' COMMENT '参数值(字符串)',
    param_type      VARCHAR(16)   NOT NULL DEFAULT 'STRING' COMMENT '类型: STRING/NUMBER/JSON/BOOL',
    default_value   VARCHAR(512)  DEFAULT '' COMMENT '默认值',
    description     VARCHAR(512)  DEFAULT '',
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_version_param (model_version_id, param_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='模型参数';


-- ============================================================
-- Part 12: 工作流(沿用 ALMD 多 Agent 引擎)
-- ============================================================

-- 12.1 工作流定义
CREATE TABLE IF NOT EXISTS ialm_workflow_def (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    workflow_name   VARCHAR(128)  NOT NULL,
    workflow_code   VARCHAR(64)   NOT NULL,
    description     VARCHAR(512)  DEFAULT '',
    node_json       JSON          NOT NULL COMMENT '节点+边的 DAG JSON',
    trigger_type    VARCHAR(16)   NOT NULL DEFAULT 'MANUAL' COMMENT 'MANUAL/SCHEDULED',
    cron_expr       VARCHAR(64)   DEFAULT '',
    status          TINYINT       NOT NULL DEFAULT 1,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    updated_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_workflow_code (workflow_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='工作流定义';

-- 12.2 工作流执行
CREATE TABLE IF NOT EXISTS ialm_workflow_exec (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    workflow_id     BIGINT        NOT NULL,
    company_id      BIGINT        DEFAULT NULL COMMENT '执行保险公司',
    exec_status     VARCHAR(16)   NOT NULL DEFAULT 'RUNNING',
    input_json      JSON          DEFAULT NULL,
    output_json     JSON          DEFAULT NULL,
    error_msg       VARCHAR(2048) DEFAULT '',
    started_at      DATETIME      DEFAULT NULL,
    finished_at     DATETIME      DEFAULT NULL,
    triggered_by    BIGINT        DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_by      BIGINT        DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_workflow (workflow_id, created_at),
    INDEX idx_company (company_id, exec_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='工作流执行';

-- 12.3 工作流节点执行
CREATE TABLE IF NOT EXISTS ialm_workflow_node_exec (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    exec_id         BIGINT        NOT NULL,
    node_id         VARCHAR(64)   NOT NULL,
    node_type       VARCHAR(32)   NOT NULL COMMENT 'EXTRACT/CALC/BENCHMARK/ATTRIBUTE/REPORT',
    agent_type      VARCHAR(32)   NOT NULL,
    exec_status     VARCHAR(16)   NOT NULL DEFAULT 'PENDING',
    input_json      JSON          DEFAULT NULL,
    output_json     JSON          DEFAULT NULL,
    error_msg       VARCHAR(2048) DEFAULT '',
    started_at      DATETIME      DEFAULT NULL,
    finished_at     DATETIME      DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_exec (exec_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='工作流节点执行';


-- ============================================================
-- Part 13: 智能对话(沿用 ALMD chat)
-- ============================================================

-- 13.1 对话 session
CREATE TABLE IF NOT EXISTS ialm_chat_session (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id         BIGINT        NOT NULL,
    company_id      BIGINT        DEFAULT NULL,
    session_title   VARCHAR(256)  NOT NULL DEFAULT '',
    context_json    JSON          DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id, updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='IALM 对话 session';

-- 13.2 对话消息
CREATE TABLE IF NOT EXISTS ialm_chat_message (
    id              BIGINT        NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    session_id      BIGINT        NOT NULL,
    role            VARCHAR(16)   NOT NULL COMMENT 'user/assistant/system',
    content         LONGTEXT      NOT NULL,
    references_json JSON          DEFAULT NULL,
    is_deleted      TINYINT       NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='IALM 对话消息';


-- ============================================================
-- Part 14: 初始数据
-- ============================================================

-- 默认角色
INSERT IGNORE INTO sys_role (role_name, role_code, description, sort_order, created_by) VALUES
('ALCO主席', 'ALCO_CHAIR', '资产负债管理委员会主席', 1, 1),
('风险管理经理', 'RISK_MANAGER', '风险管理部经理', 2, 1),
('精算师', 'ACTUARY', '精算师', 3, 1),
('资产管理经理', 'ASSET_MANAGER', '资产管理部经理', 4, 1),
('系统管理员', 'ADMIN', 'IALM 系统管理员', 99, 1);

-- 默认权限示例
INSERT IGNORE INTO sys_permission (permission_code, permission_name, parent_id, permission_type, sort_order, created_by) VALUES
('alm:dashboard:view', '资产负债驾驶舱', 0, 'MENU', 1, 1),
('alm:match:view', '匹配分析', 0, 'MENU', 2, 1),
('alm:match:run', '执行匹配分析', 0, 'BUTTON', 3, 1),
('alm:cashflow:view', '现金流预测', 0, 'MENU', 4, 1),
('alm:cashflow:run', '执行现金流预测', 0, 'BUTTON', 5, 1),
('alm:stress:view', '压力测试', 0, 'MENU', 6, 1),
('alm:stress:run', '执行压力测试', 0, 'BUTTON', 7, 1),
('alm:invest:view', '投资决策', 0, 'MENU', 8, 1),
('alm:product:view', '产品定价联动', 0, 'MENU', 9, 1),
('alm:report:view', '监管报表', 0, 'MENU', 10, 1),
('alm:report:generate', '生成监管报表', 0, 'BUTTON', 11, 1),
('alm:report:file', '报送监管报表', 0, 'BUTTON', 12, 1),
('alm:risk:view', '风险预警', 0, 'MENU', 13, 1),
('alm:model:view', '模型管理', 0, 'MENU', 14, 1),
('alm:data:view', '数据底座', 0, 'MENU', 15, 1),
('alm:data:upload', '数据接入', 0, 'BUTTON', 16, 1),
('alm:system:view', '系统管理', 0, 'MENU', 99, 1);

-- 14 项算法模型定义(基于算法详细设计.md §1.3)
INSERT IGNORE INTO ialm_model_definition (model_code, model_name, category, priority, regulatory_code, description, algorithm_summary, created_by) VALUES
('ALG-001', '期限结构匹配率', 'MATCH', 'P0', '5号规则', '基于修正久期加权计算资产端与负债端现金流期限匹配度', 'Min(D^A_i, D^L_i) / Σ D^L_i, 阈值≥80%', 1),
('ALG-002', '综合成本收益比', 'MATCH', 'P0', '5号规则', '投资收益对负债端成本的覆盖能力', 'R_CR = 综合投资收益率 / Σ(C_i + R_i + E_i)', 1),
('ALG-003', '现金流回正期', 'MATCH', 'P0', '5号规则', '资产端累计现金流首次覆盖负债端累计现金流的时间点', 'NC_t = Σ(A_s - L_s), T*=min{t: NC_t≥0, ∀s≤t}, 阈值≤5年', 1),
('ALG-004', '修正久期/有效久期', 'MATCH', 'P0', '', '债券价格对利率变动的敏感性', 'D_mod = D_mac / (1+y/m), D_eff = (P(y-Δy)-P(y+Δy))/(2PΔy)', 1),
('ALG-005', '久期缺口', 'MATCH', 'P0', '', '资产端与负债端修正久期差', 'DGAP = D_A - D_L, DR = D_A / D_L', 1),
('ALG-006', '现金流贴现预测', 'CASHFLOW', 'P0', '', '基于精算假设预测未来多期资产/负债现金流', 'PV = Σ CF_t/(1+d)^t, IRR 反推', 1),
('ALG-007', '蒙特卡洛随机情景生成', 'STRESS', 'P0', '6号规则', '基于历史数据生成利率/汇率/收益率随机路径', 'Vasicek/CIR/Hull-White 模型 Euler-Maruyama 离散化', 1),
('ALG-008', '多因子冲击传导', 'STRESS', 'P0', '6号规则', '将预设冲击情景传导至资产/负债端', 'ΔNAV = -(D_A·A - D_L·L)·Δy + 0.5·(C_A·A - C_L·L)·(Δy)²', 1),
('ALG-009', '反向压力测试', 'STRESS', 'P1', '内部管理', '从监管阈值出发反向寻找极端情景', 'x*=argmax||x-x_0|| s.t. f(x*)=T', 1),
('ALG-010', '均值-方差资产配置', 'INVESTMENT', 'P1', '', 'Markowitz 均值-方差模型求最优配置', 'max (w^T·μ-r_f)/√(w^T·Σ·w) s.t. Σw=1, w≥0', 1),
('ALG-011', 'Black-Litterman 配置', 'INVESTMENT', 'P1', '', '融合市场均衡与主观观点的配置模型', 'E[R]=[(τΣ)⁻¹+P^T·Ω⁻¹·P]⁻¹·[(τΣ)⁻¹·Π+P^T·Ω⁻¹·Q]', 1),
('ALG-012', 'Brinson 业绩归因', 'INVESTMENT', 'P2', '', '超额收益分解为配置/选择/交互效应', 'R_p-R_b = Σ(w^p-w^b)·R^b + Σw^b·(R^p-R^b) + Σ(w^p-w^b)·(R^p-R^b)', 1),
('ALG-013', 'VaR/CVaR 风险度量', 'RISK', 'P1', '', '在险价值/条件在险价值', 'VaR_α=-q_α(R), CVaR_α=-E[R|R≤-VaR_α]', 1),
('ALG-014', '再保险现金流影响测算', 'CASHFLOW', 'P2', '', '不同再保方案对资产负债现金流影响', 'CF_t^net = CF_t^gross - CF_t^ceded + CF_t^recover', 1);

-- 监管情景预置
INSERT IGNORE INTO ialm_stress_scenario (scenario_code, scenario_name, scenario_type, source, description, shocks_json, is_active, created_by) VALUES
('REG_INT_UP200', '监管-利率上行200bp', 'INTEREST', 'REGULATORY', '银保监会规定必选压力情景', JSON_OBJECT('factors', JSON_ARRAY(JSON_OBJECT('name','interest_rate','type','parallel_shift','value',2.0))), 1, 1),
('REG_INT_DOWN200', '监管-利率下行200bp', 'INTEREST', 'REGULATORY', '银保监会规定必选压力情景', JSON_OBJECT('factors', JSON_ARRAY(JSON_OBJECT('name','interest_rate','type','parallel_shift','value',-2.0))), 1, 1),
('REG_LAPSE_UP50', '监管-退保率上升50%', 'LAPSE', 'REGULATORY', '银保监会规定必选压力情景', JSON_OBJECT('factors', JSON_ARRAY(JSON_OBJECT('name','lapse_rate','type','multiplier','value',1.5))), 1, 1),
('REG_INV_DOWN50', '监管-投资收益率下降50%', 'INVESTMENT', 'REGULATORY', '银保监会规定必选压力情景', JSON_OBJECT('factors', JSON_ARRAY(JSON_OBJECT('name','investment_yield','type','multiplier','value',0.5))), 1, 1),
('REG_FX_UP15', '监管-USD/CNY上升15%', 'FX', 'REGULATORY', '汇率冲击', JSON_OBJECT('factors', JSON_ARRAY(JSON_OBJECT('name','USD_CNY','type','pct_change','value',15))), 1, 1),
('REG_COMPREHENSIVE', '监管-综合压力测试', 'COMPREHENSIVE', 'REGULATORY', '多因子同时冲击', JSON_OBJECT('factors', JSON_ARRAY(JSON_OBJECT('name','interest_rate','type','parallel_shift','value',1.5), JSON_OBJECT('name','lapse_rate','type','multiplier','value',1.3), JSON_OBJECT('name','investment_yield','type','multiplier','value',0.7))), 1, 1);

SET FOREIGN_KEY_CHECKS=1;

-- ============================================================
-- 初始化完成
-- 共建表数: 40+ 张
-- 涵盖域: 系统管理 / 保险公司 / 资产端 / 负债端 / 市场数据
--         匹配分析 / 现金流预测 / 压力测试 / 投资组合 / 业绩归因
--         监管报表 / 风险预警 / 模型管理 / 工作流 / 智能对话
-- ============================================================

SELECT 'IALM 数据库初始化完成 ✅' AS status;