/**
 * IALM 负债端管理
 * - 保单主档 ↔ 负债现金流 双向联动（参考资产端处理）
 * - 保单 tab 增"查看现金流"按钮 → 切换到现金流 tab 并预选保单
 * - 现金流 tab 顶部增"按保单筛选"选择器 + 当前保单信息 + 统计卡片
 */
import { useState, useEffect, useMemo } from 'react'
import { Card, Tabs, Tag, Space, Tooltip, Button, Select, Table, Empty, Statistic as AntStatistic, Typography } from 'antd'
import { FundViewOutlined, ClearOutlined, ReloadOutlined, ExperimentOutlined } from '@ant-design/icons'
import { liabilitiesApi, systemApi } from '../api'
import EngineRegenerateModal from '../components/EngineRegenerateModal'

export default function Liabilities() {
  const [activeTab, setActiveTab] = useState('policies')
  const [policies, setPolicies] = useState<any[]>([])
  const [periodUnits, setPeriodUnits] = useState<any[]>([])
  const [engineOpen, setEngineOpen] = useState(false)
  // === 联动状态 ===
  const [selectedPolicyId, setSelectedPolicyId] = useState<number | null>(null)
  const [cashflows, setCashflows] = useState<any[]>([])
  const [cfTotal, setCfTotal] = useState(0)
  const [cfLoading, setCfLoading] = useState(false)

  // 加载全部保单 + 期限单位字典
  useEffect(() => {
    const load = async () => {
      const [rP, rD] = await Promise.all([
        liabilitiesApi.policies({ page: 1, page_size: 200 }),
        systemApi.periodUnits(),
      ])
      setPolicies(rP.data?.items || [])
      setPeriodUnits(rD.data?.items || [])
    }
    load()
  }, [])

  // 当前选中保单的元数据
  const selectedPolicy = useMemo(
    () => policies.find((p) => p.id === selectedPolicyId) || null,
    [policies, selectedPolicyId]
  )

  // === 加载现金流（联动）===
  const loadCashflows = async (policyId: number | null) => {
    setCfLoading(true)
    try {
      const params = policyId !== null
        ? { page: 1, page_size: 500, policy_id: policyId }
        : { page: 1, page_size: 500 }
      const r = await liabilitiesApi.cashflows(params)
      setCashflows(r.data?.items || [])
      setCfTotal(r.data?.total || 0)
    } finally {
      setCfLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'cashflows') {
      loadCashflows(selectedPolicyId)
    }
    // eslint-disable-next-line react-exhaustive-deps
  }, [activeTab, selectedPolicyId])

  // 保单 tab → 现金流 tab 的联动
  const viewCashflows = (row: any) => {
    setSelectedPolicyId(row.id)
    setActiveTab('cashflows')
  }

  // 现金流汇总
  const cfStats = useMemo(() => {
    let premiumIn = 0, benefitOut = 0, claimOut = 0, surrenderOut = 0, totalPV = 0
    for (const cf of cashflows) {
      if (cf.cashflow_type === 'PREMIUM_IN') premiumIn += cf.amount
      if (cf.cashflow_type === 'BENEFIT_OUT') benefitOut += cf.amount
      if (cf.cashflow_type === 'CLAIM_OUT') claimOut += cf.amount
      if (cf.cashflow_type === 'SURRENDER') surrenderOut += cf.amount
      totalPV += cf.present_value
    }
    return {
      premiumIn, benefitOut, claimOut, surrenderOut, totalPV,
      net: premiumIn - benefitOut - claimOut - surrenderOut,
    }
  }, [cashflows])

  return (
    <>
    <Tabs
      activeKey={activeTab}
      onChange={setActiveTab}
      type="card"
      items={[
        {
          key: 'policies',
          label: '保单主档',
          children: <PoliciesTab policies={viewCashflows} />,
        },
        {
          key: 'cashflows',
          label: selectedPolicy
            ? `现金流（${selectedPolicy.policy_no}）`
            : '负债现金流',
          children: (
            <LiabilityCashflowsTab
              policies={policies}
              periodUnits={periodUnits}
              selectedPolicyId={selectedPolicyId}
              setSelectedPolicyId={setSelectedPolicyId}
              selectedPolicy={selectedPolicy}
              cashflows={cashflows}
              cfTotal={cfTotal}
              cfLoading={cfLoading}
              cfStats={cfStats}
              reload={() => loadCashflows(selectedPolicyId)}
              onEngine={() => setEngineOpen(true)}
            />
          ),
        },
        {
          key: 'product-categories',
          label: '产品分类',
          children: <ProductCategoriesTab />,
        },
        {
          key: 'reserves',
          label: '准备金',
          children: <ReservesTab />,
        },
        {
          key: 'assumptions',
          label: '精算假设',
          children: <AssumptionsTab />,
        },
      ]}
    />

    <EngineRegenerateModal
      open={engineOpen}
      companyId={4}
      companyShort="新华保险"
      onClose={() => setEngineOpen(false)}
      onCompleted={() => loadCashflows(selectedPolicyId)}
    />
    </>
  )
}

// ═══ 保单主档 Tab（带"查看现金流"操作列） ═══
function PoliciesTab({ policies }: any) {
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      const r = await liabilitiesApi.policies({ page: 1, page_size: 200 })
      setItems(r.data?.items || [])
      setTotal(r.data?.total || 0)
      setLoading(false)
    }
    load()
  }, [])

  return (
    <div>
      <h3 style={{ marginBottom: 0 }}>保单主档管理</h3>
      <p style={{ color: '#999', marginTop: 4 }}>
        保险合同主档（关联 ialm_insurance_company / ialm_product_category）·
        点击「查看现金流」跳转到该保单的现金流
      </p>
      <Card style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          dataSource={items}
          loading={loading}
          pagination={{ pageSize: 20, total, showSizeChanger: false, showTotal: (t: number) => `共 ${t} 条` }}
          scroll={{ x: 1600 }}
          columns={[
            { title: '保单号', dataIndex: 'policy_no', width: 170 },
            { title: '机构编码', dataIndex: 'company_code', width: 130,
              render: (v: string) => <Tag color="purple">{v}</Tag> },
            { title: '保险公司', dataIndex: 'company_name', width: 90,
              render: (v: string, row: any) => (
                <Tooltip title={`全称: ${row.company_full_name || ''} | ID=${row.company_id}`}>
                  <span>{v}</span>
                </Tooltip>
              ) },
            { title: '产品编码', dataIndex: 'product_code', width: 130 },
            { title: '产品名称', dataIndex: 'product_name', width: 160 },
            { title: '保额(万)', dataIndex: 'sum_insured', width: 120,
              render: (v: number) => v?.toLocaleString() },
            { title: '年保费(万)', dataIndex: 'annual_premium', width: 120,
              render: (v: number) => v?.toLocaleString() },
            { title: '缴费期(年)', dataIndex: 'payment_period', width: 100 },
            { title: '保险期(年)', dataIndex: 'insurance_period', width: 100 },
            { title: '生效日', dataIndex: 'effective_date', width: 110 },
            { title: '到期日', dataIndex: 'maturity_date', width: 110 },
            // === 操作列：联动核心 ===
            { title: '操作', key: 'action', width: 110, fixed: 'right' as const,
              render: (_: any, row: any) => (
                <Button
                  type="link"
                  size="small"
                  icon={<FundViewOutlined />}
                  onClick={() => policies(row)}
                >
                  查看现金流
                </Button>
              ) },
          ]}
        />
      </Card>
    </div>
  )
}

// ═══ 负债现金流 Tab（联动核心：保单筛选 + 信息卡 + 统计 + 现金流） ═══
function LiabilityCashflowsTab({
  policies, periodUnits, selectedPolicyId, setSelectedPolicyId,
  selectedPolicy, cashflows, cfTotal, cfLoading, cfStats, reload, onEngine,
}: any) {
  // === 期限单位筛选 ===
  const [unitFilter, setUnitFilter] = useState<string | null>(null)
  const filteredCashflows = useMemo(() => {
    if (!unitFilter) return cashflows
    return cashflows.filter((cf) => cf.period_unit === unitFilter)
  }, [cashflows, unitFilter])

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ marginBottom: 0 }}>
            负债现金流
            {selectedPolicy && (
              <Tag color="processing" style={{ marginLeft: 8, fontSize: 14, padding: '4px 12px' }}>
                {selectedPolicy.policy_no} · {selectedPolicy.product_name}
              </Tag>
            )}
          </h3>
          <p style={{ color: '#999', marginTop: 4, marginBottom: 0 }}>
            按期预测的负债端现金流（保费/给付/退保） · 与保单的 <code>policy_id</code> 关联
          </p>
        </div>
        <Button type="primary" icon={<ExperimentOutlined />} onClick={onEngine}>
          引擎重算
        </Button>
      </div>

      {/* === 筛选区 === */}
      <Card style={{ marginTop: 16 }}>
        <Space size={12} wrap>
          <span>按保单筛选：</span>
          <Select
            showSearch
            allowClear
            placeholder="选择保单（留空显示全部）"
            style={{ width: 380 }}
            value={selectedPolicyId || undefined}
            onChange={(v) => setSelectedPolicyId(v ?? null)}
            optionFilterProp="label"
            options={policies.map((p: any) => ({
              value: p.id,
              label: `${p.policy_no} · ${p.product_name}`,
            }))}
          />
          {selectedPolicyId !== null && (
            <Button icon={<ClearOutlined />} onClick={() => setSelectedPolicyId(null)}>
              清除筛选
            </Button>
          )}
          <Button icon={<ReloadOutlined />} onClick={reload}>刷新</Button>
          <span style={{ marginLeft: 16 }}>期限单位：</span>
          <Select
            allowClear
            placeholder="全部单位"
            style={{ width: 120 }}
            value={unitFilter || undefined}
            onChange={(v) => setUnitFilter(v ?? null)}
            options={periodUnits.map((u: any) => ({
              value: u.unit_code,
              label: u.unit_name,
            }))}
          />
        </Space>
      </Card>

      {/* === 当前选中保单信息卡 === */}
      {selectedPolicy && (
        <Card style={{ marginTop: 16 }} size="small" title={
          <Space>
            <span>📌 当前保单信息</span>
            <Tag color="blue">{selectedPolicy.policy_no}</Tag>
          </Space>
        }>
          <Space size={32} wrap>
            <div><span style={{ color: '#999' }}>产品：</span>{selectedPolicy.product_name}</div>
            <div><span style={{ color: '#999' }}>保额：</span>{selectedPolicy.sum_insured?.toLocaleString()} 万</div>
            <div><span style={{ color: '#999' }}>年保费：</span>{selectedPolicy.annual_premium?.toLocaleString()} 万</div>
            <div><span style={{ color: '#999' }}>缴费期：</span>{selectedPolicy.payment_period} 年</div>
            <div><span style={{ color: '#999' }}>保险期：</span>{selectedPolicy.insurance_period} 年</div>
            <div><span style={{ color: '#999' }}>生效日：</span>{selectedPolicy.effective_date}</div>
            <div><span style={{ color: '#999' }}>到期日：</span>{selectedPolicy.maturity_date}</div>
          </Space>
        </Card>
      )}

      {/* === 现金流汇总统计 === */}
      <Card style={{ marginTop: 16 }} size="small">
        <Space size={40} wrap>
          <AntStatistic
            title="现金流记录数"
            value={cfTotal}
            suffix="条"
            valueStyle={{ color: '#667eea', fontSize: 24 }}
          />
          <AntStatistic
            title="保费流入（PREMIUM_IN）"
            value={cfStats.premiumIn}
            precision={2}
            valueStyle={{ color: '#52c41a', fontSize: 24 }}
            suffix="万"
          />
          <AntStatistic
            title="给付支出（BENEFIT_OUT）"
            value={cfStats.benefitOut}
            precision={2}
            valueStyle={{ color: '#ff4d4f', fontSize: 24 }}
            suffix="万"
          />
          <AntStatistic
            title="理赔支出（CLAIM_OUT）"
            value={cfStats.claimOut}
            precision={2}
            valueStyle={{ color: '#fa8c16', fontSize: 24 }}
            suffix="万"
          />
          <AntStatistic
            title="净流量"
            value={cfStats.net}
            precision={2}
            valueStyle={{ color: cfStats.net > 0 ? '#52c41a' : '#ff4d4f', fontSize: 24 }}
            suffix="万"
          />
          <AntStatistic
            title="现值合计"
            value={cfStats.totalPV}
            precision={2}
            valueStyle={{ color: '#722ed1', fontSize: 24 }}
            suffix="万"
          />
        </Space>
      </Card>

      {/* === 现金流表 === */}
      <Card style={{ marginTop: 16 }} title="现金流明细">
        <Table
          rowKey="id"
          dataSource={filteredCashflows}
          loading={cfLoading}
          pagination={{ pageSize: 20, showSizeChanger: false, showTotal: (t) => `共 ${t} 条` }}
          locale={{ emptyText: <Empty description={selectedPolicyId ? '该保单暂无现金流' : '请先选择保单'} /> }}
          columns={[
            { title: '保单号', dataIndex: 'policy_id', width: 100,
              render: (v: number) => <Tag color="blue">#{v}</Tag> },
            { title: '期数', dataIndex: 'period_number', width: 70 },
            { title: '期限', dataIndex: 'period_count', width: 80,
              render: (v: number) => v?.toFixed(0) },
            { title: '期限单位', dataIndex: 'period_unit_name', width: 90,
              render: (v: string, row: any) => <Tag color={
                row.period_unit === 'DAY' ? 'magenta' :
                row.period_unit === 'WEEK' ? 'purple' :
                row.period_unit === 'MONTH' ? 'orange' :
                row.period_unit === 'QUARTER' ? 'cyan' :
                row.period_unit === 'HALF_YEAR' ? 'geekblue' :
                row.period_unit === 'YEAR' ? 'blue' : 'default'
              }>{v || '-'}</Tag> },
            { title: '现金流类型', dataIndex: 'cashflow_type', width: 140,
              render: (v: string) => <Tag color={
                v === 'PREMIUM_IN' ? 'green' :
                v === 'BENEFIT_OUT' ? 'red' :
                v === 'CLAIM_OUT' ? 'orange' :
                v === 'SURRENDER' ? 'purple' : 'default'
              }>{v}</Tag> },
            { title: '金额(万)', dataIndex: 'amount', width: 130,
              render: (v: number) => v?.toLocaleString(undefined, { maximumFractionDigits: 2 }) },
            { title: '折现因子', dataIndex: 'discount_factor', width: 100,
              render: (v: number) => v?.toFixed(4) },
            { title: '现值(万)', dataIndex: 'present_value', width: 140,
              render: (v: number) => v?.toLocaleString(undefined, { maximumFractionDigits: 2 }) },
            { title: '现金流日期', dataIndex: 'period_date', width: 110 },
          ]}
        />
      </Card>
    </div>
  )
}

// ═══ 产品分类 Tab ═══
function ProductCategoriesTab() {
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [keyword, setKeyword] = useState('')

  const load = async () => {
    const r = await liabilitiesApi.productCategories({ page: 1, page_size: 200, keyword: keyword || undefined })
    setItems(r.data?.items || [])
    setTotal(r.data?.total || 0)
  }
  useEffect(() => { load() }, [])

  return (
    <div>
      <h3>产品分类</h3>
      <p style={{ color: '#999' }}>保险产品分类树（按负债类型）</p>
      <Card style={{ marginTop: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <input
            placeholder="搜索关键字"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            style={{ width: 280, padding: '4px 11px', border: '1px solid #d9d9d9', borderRadius: 2 }}
          />
          <Button type="primary" onClick={load}>搜索</Button>
        </Space>
        <Table
          rowKey="id"
          dataSource={items}
          pagination={{ pageSize: 20, total, showSizeChanger: false, showTotal: (t: number) => `共 ${t} 条` }}
          columns={[
            { title: '编码', dataIndex: 'product_type_code', width: 180 },
            { title: '名称', dataIndex: 'product_type_name' },
            { title: '险种', dataIndex: 'insurance_type', width: 100,
              render: (v: string) => <Tag color={
                v === 'LIFE' ? 'blue' : v === 'PROPERTY' ? 'orange' :
                v === 'HEALTH' ? 'cyan' : v === 'REINSURANCE' ? 'purple' : 'default'
              }>{v}</Tag> },
            { title: '期限类型', dataIndex: 'duration_type', width: 100 },
            { title: '缴费方式', dataIndex: 'payment_type', width: 100 },
            { title: '风险账户', dataIndex: 'is_risk_account', width: 90,
              render: (v: number) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
          ]}
        />
      </Card>
    </div>
  )
}

// ═══ 准备金 Tab ═══
function ReservesTab() {
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)

  useEffect(() => {
    const load = async () => {
      const r = await liabilitiesApi.reserves({ page: 1, page_size: 100 })
      setItems(r.data?.items || [])
      setTotal(r.data?.total || 0)
    }
    load()
  }, [])

  return (
    <div>
      <h3>责任准备金</h3>
      <p style={{ color: '#999' }}>未到期/未决赔款/长寿准备金等</p>
      <Card style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          dataSource={items}
          pagination={{ pageSize: 20, total, showSizeChanger: false, showTotal: (t: number) => `共 ${t} 条` }}
          columns={[
            { title: '保险公司', dataIndex: 'company_name', width: 120 },
            { title: '准备金类型', dataIndex: 'reserve_type', width: 200 },
            { title: '报告日', dataIndex: 'report_date', width: 120 },
            { title: '金额(万)', dataIndex: 'amount', width: 140,
              render: (v: number) => v?.toLocaleString() },
            { title: '会计准则', dataIndex: 'accounting_basis', width: 110 },
            { title: '币种', dataIndex: 'currency', width: 80 },
          ]}
        />
      </Card>
    </div>
  )
}

// ═══ 精算假设 Tab ═══
function AssumptionsTab() {
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)

  useEffect(() => {
    const load = async () => {
      const r = await liabilitiesApi.assumptions({ page: 1, page_size: 100 })
      setItems(r.data?.items || [])
      setTotal(r.data?.total || 0)
    }
    load()
  }, [])

  return (
    <div>
      <h3>精算假设</h3>
      <p style={{ color: '#999' }}>死亡率/退保率/折现率等精算参数</p>
      <Card style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          dataSource={items}
          pagination={{ pageSize: 20, total, showSizeChanger: false, showTotal: (t: number) => `共 ${t} 条` }}
          columns={[
            { title: '假设集', dataIndex: 'assumption_set_code', width: 160 },
            { title: '折现率', dataIndex: 'discount_rate', width: 100,
              render: (v: number) => `${((v || 0) * 100).toFixed(2)}%` },
            { title: '死亡率表', dataIndex: 'mortality_table_code', width: 160 },
            { title: '退保率编码', dataIndex: 'lapse_rate_code', width: 160 },
            { title: '费用率编码', dataIndex: 'expense_rate_code', width: 160 },
            { title: '生效日', dataIndex: 'effective_date', width: 120 },
          ]}
        />
      </Card>
    </div>
  )
}