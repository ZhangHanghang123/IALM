# IALM - 保险资产负债管理智能分析平台

> Insurance Asset-Liability Management — 基于 5 号规则的智能化资产负债匹配分析平台

## 项目简介

IALM 是面向保险公司的资产负债管理智能分析平台，严格遵循中国银保监会**5 号规则**（关于规范保险机构开展保险资金运用业务的通知）三项核心监管指标：
- **期限结构匹配率** ≥ 80%
- **综合成本收益比** ≥ 1.05（寿险）/ ≥ 1.10（财险）
- **现金流回正期** ≤ 5 年

## 技术架构

| 层 | 技术 |
|---|---|
| 前端 | React 18 + Ant Design 5 + Vite + ECharts |
| 后端 | FastAPI + Uvicorn + SQLAlchemy 2.0 + Pydantic v2 |
| 数据库 | MySQL 8.0 + Redis 7 |
| 计算引擎 | NumPy + Pandas + cvxpy（Markowitz） + SciPy（优化） |
| 智能体 | LangChain + LangGraph + DeepSeek |
| 部署 | Git + nginx + systemd + SSL（TrustAsia） |

## 快速开始

### 本地开发

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 填入数据库连接
python init_db.py  # 初始化表 + 种子数据
uvicorn app.main:app --reload --port 8004

# 前端
cd ../frontend
npm install
npm run dev  # 默认 5174 端口（避免与 IALMD 5173 冲突）
```

### 生产部署

```bash
# 一键部署（Git Bash）
../deploy.sh ialm "feat: ..."
```

## 项目结构

```
IALM/
├── backend/                       # FastAPI 后端
│   ├── app/
│   │   ├── main.py               # 入口
│   │   ├── config.py             # 配置（DATABASE_URL_OVERRIDE 优先）
│   │   ├── database.py           # SQLAlchemy
│   │   ├── models/               # ORM 模型
│   │   ├── routers/              # 路由（auth/insurance/asset/liability/match/...）
│   │   ├── services/             # 业务服务
│   │   └── algorithms/           # 14 项核心算法引擎
│   ├── sql/init.sql              # 46 张表 DDL + 种子数据
│   ├── requirements.txt
│   └── init_db.py
├── frontend/                      # React 前端
│   ├── src/
│   │   ├── pages/                # 页面（Login/Dashboard/Match/Stress/Cashflow/...）
│   │   ├── api/                  # API 客户端
│   │   ├── components/           # 公共组件
│   │   └── layouts/              # 布局
│   ├── package.json
│   └── vite.config.ts
├── IALM_保险资产负债管理产品需求文档.md
├── IALM_保险资产负债管理算法详细设计.md
├── IALM_保险资产负债管理算法案例模板.xlsx
├── IALM_资料分析报告.md
├── IALM_数据库设计文档.md
└── deploy/nginx/ialm.nginx.conf  # nginx 配置
```

## 核心算法

| 编号 | 算法 | 阈值 |
|---|---|---|
| ALG-001 | 期限结构匹配率 | ≥ 80% |
| ALG-002 | 综合成本收益比 | 寿险≥1.05 / 财险≥1.10 |
| ALG-003 | 现金流回正期 | ≤ 5 年 |
| ALG-004 | 久期与凸性 | 缺口 [-1, +1] 年 |
| ALG-005 | 现金流预测（蒙特卡洛） | - |
| ALG-006 | Hull-White 利率模型 | - |
| ALG-007 | 压力测试（6 个监管情景） | - |
| ALG-008 | Markowitz 最优配置 | - |
| ALG-009 | Black-Litterman 配置 | - |
| ALG-010 | Brinson 业绩归因 | - |
| ALG-011 | VaR / CVaR | - |
| ALG-012 | 动态复制免疫 | - |
| ALG-013 | 再保现金流建模 | - |
| ALG-014 | 久期匹配资产负债管理 | - |

## 部署访问

- **统一门户**：https://wxfzhh.online/
- **IALM 直接访问**：https://wxfzhh.online/ialm/
- **API**：https://wxfzhh.online/ialm/api/
- **后端端口**：8004
- **默认账号**：admin / admin123

## 监管驱动

银保监会"关于规范保险机构开展保险资金运用业务的通知"（保监发〔2018〕6号，俗称"5 号规则"）核心要求：
1. 资产端与负债端期限匹配；
2. 投资收益率覆盖负债成本；
3. 现金流稳健，避免集中到期。

## License

Internal Use Only