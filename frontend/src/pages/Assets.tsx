/**
 * IALM 资产端管理
 * - 资产持仓 ↔ 资产现金流 双向联动
 * - 持仓 tab 增"查看现金流"按钮 → 切换到现金流 tab 并预选持仓
 * - 现金流 tab 顶部增"按持仓筛选"选择器 + 资产信息面板
 */
import { useState, useEffect, useMemo } from 'react'
import { Card, Tabs, Tag, Space, Tooltip, Button, Select, Table, Input, Empty, Statistic as AntStatistic } from 'antd'
import { FundViewOutlined, ClearOutlined, ReloadOutlined } from '@ant-design/icons'
import { assetsApi } from '../api'

export default function Assets() {
  const [activeTab, setActiveTab] = useState('holdings')
  const [holdings, setHoldings] = useState<any[]>([])
  // === 联动状态 ===
  const [selectedHoldingId, setSelectedHoldingId] = useState<number | null>(null)
  const [cashflows, setCashflows] = useState<any[]>([])
  const [cfTotal, setCfTotal] = useState(0)
  const [cfLoading, setCfLoading] = useState(false)

  // 加载全部持仓（用于下拉选择）
  useEffect(() => {
    const load = async () => {
      const r = await assetsApi.holdings({ page: 1, page_size: 200 })
      setHoldings(r.data?.items || [])
    }
    load()
  }, [])

  // 当前选中持仓的元数据
  const selectedHolding = useMemo(
    () => holdings.find((h) => h.id === selectedHoldingId) || null,
    [holdings, selectedHoldingId]
  )

  // === 加载现金流（联动）===
  const loadCashflows = async (holdingId: number | null) => {
    setCfLoading(true)
    try {
      const params = holdingId !== null
        ? { page: 1, page_size: 500, holding_id: holdingId }
        : { page: 1, page_size: 500 }
      const r = await assetsApi.cashflows(params)
      setCashflows(r.data?.items || [])
      setCfTotal(r.data?.total || 0)
    } finally {
      setCfLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'cashflows') {
      loadCashflows(selectedHoldingId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, selectedHoldingId])

  // 持仓 tab → 现金流 tab 的联动
  const viewCashflows = (row: any) => {
    setSelectedHoldingId(row.id)
    setActiveTab('cashflows')
  }

  // 现金流汇总
  const cfStats = useMemo(() => {
    let totalIn = 0, totalOut = 0, totalPV = 0
    for (const cf of cashflows) {
      if (cf.cashflow_type === 'COUPON' || cf.cashflow_type === 'PRINCIPAL') totalIn += cf.amount
      if (cf.cashflow_type === 'BENEFIT_OUT' || cf.cashflow_type === 'CLAIM_OUT') totalOut += cf.amount
      totalPV += cf.present_value
    }
    return { totalIn, totalOut, totalPV }
  }, [cashflows])

  return (
    <Tabs
      activeKey={activeTab}
      onChange={setActiveTab}
      type="card"
      items={[
        {
          key: 'holdings',
          label: '资产持仓',
          children: (
            <HoldingsTab holdings={holdings} viewCashflows={viewCashflows} />
          ),
        },
        {
          key: 'cashflows',
          label: selectedHolding
            ? `现金流（${selectedHolding.asset_code}）`
            : '资产现金流',
          children: (
            <CashflowsTab
              holdings={holdings}
              selectedHoldingId={selectedHoldingId}
              setSelectedHoldingId={setSelectedHoldingId}
              selectedHolding={selectedHolding}
              cashflows={cashflows}
              cfTotal={cfTotal}
              cfLoading={cfLoading}
              cfStats={cfStats}
              reload={() => loadCashflows(selectedHoldingId)}
            />
          ),
        },
        {
          key: 'categories',
          label: '资产分类',
          children: <CategoriesTab />,
        },
      ]}
    />
  )
}

// ═══ 资产持仓 Tab（保持原 14 列 + 1 操作列） ═══
function HoldingsTab({ holdings, viewCashflows }: any) {
  return (
    <div>
      <h3 style={{ marginBottom: 0}}>资产持仓管理</h3>
      <p style={{ color: '#999', marginTop: 4 }}>
        投资持仓清单（关联 ialm_insurance_company / ialm_asset_category） ·
        点击「查看现金流」跳转到该持仓的现金流
      </p>
      <Card style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          dataSource={holdings}
          pagination={{ pageSize: 20, showSizeChanger: false, showTotal: (t) => `共 ${t} 条` }}
          scroll={{ x: 1700 }}
          columns={[
            { title: '持仓编号', dataIndex: 'asset_code', width: 110 },
            { title: '资产名称', dataIndex: 'asset_name', width: 200 },
            { title: '机构编码', dataIndex: 'company_code', width: 130,
              render: (v: string) => <Tag color="purple">{v}</Tag> },
            { title: '保险公司', dataIndex: 'company_name', width: 90,
              render: (v: string, row: any) => (
                <Tooltip title={`全称: ${row.company_full_name || ''} | ID=${row.company_id}`}>
                  <span>{v}</span>
                </Tooltip>
              ) },
            { title: '资产分类', dataIndex: 'category_code', width: 150 },
            { title: '分类名称', dataIndex: 'category_name', width: 130 },
            { title: '账面价值(万)', dataIndex: 'cost_value', width: 120,
              render: (v: number) => v?.toLocaleString(undefined, { maximumFractionDigits: 0 }) },
            { title: '市值(万)', dataIndex: 'market_value', width: 110,
              render: (v: number) => v?.toLocaleString(undefined, { maximumFractionDigits: 0 }) },
            { title: '票面利率', dataIndex: 'coupon_rate', width: 90,
              render: (v: number) => `${(v * 100).toFixed(2)}%` },
            { title: '久期(年)', dataIndex: 'duration_year', width: 90,
              render: (v: number) => v?.toFixed(2) },
            { title: '到期日', dataIndex: 'maturity_date', width: 110 },
            { title: '评级', dataIndex: 'credit_rating', width: 90,
              render: (v: string, row: any) => {
                const code = row.category_code || ''
                if (v && v.trim()) return <Tag color="blue">{v}</Tag>
                if (code.includes('GOVT') || code.includes('CDB') || code.includes('POLICY'))
                  return <Tag color="cyan">主权AAA</Tag>
                return <Tag>未评级</Tag>
              } },
            { title: '币种', dataIndex: 'currency', width: 70 },
            // === 操作列：联动核心 ===
            { title: '操作', key: 'action', width: 110, fixed: 'right' as const,
              render: (_: any, row: any) => (
                <Button
                  type="link"
                  size="small"
                  icon={<FundViewOutlined />}
                  onClick={() => viewCashflows(row)}
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

// ═══ 资产现金流 Tab（联动核心：持仓筛选 + 持仓信息卡 + 现金流表） ═══
function CashflowsTab({
  holdings, selectedHoldingId, setSelectedHoldingId,
  selectedHolding, cashflows, cfTotal, cfLoading, cfStats, reload,
}: any) {
  return (
    <div>
      <h3 style={{ marginBottom: 0 }}>
        资产现金流
        {selectedHolding && (
          <Tag color="processing" style={{ marginLeft: 8, fontSize: 14, padding: '4px 12px' }}>
            {selectedHolding.asset_code} · {selectedHolding.asset_name}
          </Tag>
        )}
      </h3>
      <p style={{ color: '#999', marginTop: 4 }}>
        按期预测的资产端现金流（息票/本金） · 与资产持仓的 <code>holding_id</code> 关联
      </p>

      {/* === 筛选区 === */}
      <Card style={{ marginTop: 16 }}>
        <Space size={12} wrap>
          <span>按持仓筛选：</span>
          <Select
            showSearch
            allowClear
            placeholder="选择持仓（留空显示全部）"
            style={{ width: 380 }}
            value={selectedHoldingId || undefined}
            onChange={(v) => setSelectedHoldingId(v ?? null)}
            optionFilterProp="label"
            options={holdings.map((h: any) => ({
              value: h.id,
              label: `${h.asset_code} · ${h.asset_name}`,
            }))}
          />
          {selectedHoldingId !== null && (
            <Button icon={<ClearOutlined />} onClick={() => setSelectedHoldingId(null)}>
              清除筛选
            </Button>
          )}
          <Button icon={<ReloadOutlined />} onClick={reload}>刷新</Button>
        </Space>
      </Card>

      {/* === 当前选中持仓信息卡 === */}
      {selectedHolding && (
        <Card style={{ marginTop: 16 }} size="small" title={
          <Space>
            <span>📌 当前持仓信息</span>
            <Tag color="blue">{selectedHolding.asset_code}</Tag>
          </Space>
        }>
          <Space size={32} wrap>
            <div><span style={{ color: '#999' }}>资产名称：</span>{selectedHolding.asset_name}</div>
            <div><span style={{ color: '#999' }}>分类：</span>{selectedHolding.category_name || selectedHolding.category_code}</div>
            <div><span style={{ color: '#999' }}>账面价值：</span>{selectedHolding.cost_value?.toLocaleString()} 万</div>
            <div><span style={{ color: '#999' }}>票面利率：</span>{(selectedHolding.coupon_rate * 100).toFixed(2)}%</div>
            <div><span style={{ color: '#999' }}>久期：</span>{selectedHolding.duration_year?.toFixed(2)} 年</div>
            <div><span style={{ color: '#999' }}>到期日：</span>{selectedHolding.maturity_date}</div>
          </Space>
        </Card>
      )}

      {/* === 现金流汇总统计 === */}
      <Card style={{ marginTop: 16 }} size="small">
        <Space size={48}>
          <AntStatistic
            title="现金流记录数"
            value={cfTotal}
            suffix="条"
            valueStyle={{ color: '#667eea', fontSize: 24 }}
          />
          <AntStatistic
            title="流入合计（息票+本金）"
            value={cfStats.totalIn}
            precision={2}
            valueStyle={{ color: '#52c41a', fontSize: 24 }}
            suffix="万"
          />
          <AntStatistic
            title="流出合计"
            value={cfStats.totalOut}
            precision={2}
            valueStyle={{ color: '#ff4d4f', fontSize: 24 }}
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
          dataSource={cashflows}
          loading={cfLoading}
          pagination={{ pageSize: 20, showSizeChanger: false, showTotal: (t) => `共 ${t} 条` }}
          locale={{ emptyText: <Empty description={selectedHoldingId ? '该持仓暂无现金流' : '请先选择持仓'} /> }}
          columns={[
            { title: '持仓编号', dataIndex: 'asset_code', width: 110 },
            { title: '期数', dataIndex: 'period_number', width: 70 },
            { title: '年', dataIndex: 'period_year', width: 80,
              render: (v: number) => v?.toFixed(0) },
            { title: '现金流类型', dataIndex: 'cashflow_type', width: 130,
              render: (v: string) => <Tag color={
                v === 'COUPON' ? 'blue' :
                v === 'PRINCIPAL' ? 'orange' :
                v === 'BENEFIT_OUT' ? 'red' :
                v === 'CLAIM_OUT' ? 'volcano' : 'default'
              }>{v}</Tag> },
            { title: '金额(万)', dataIndex: 'amount', width: 140,
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

// ═══ 资产分类 Tab（保持原样） ═══
function CategoriesTab() {
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [keyword, setKeyword] = useState('')

  const load = async () => {
    const r = await assetsApi.categories({ page: 1, page_size: 200, keyword: keyword || undefined })
    setItems(r.data?.items || [])
    setTotal(r.data?.total || 0)
  }
  useEffect(() => { load() }, [])

  return (
    <div>
      <h3>资产分类</h3>
      <p style={{ color: '#999' }}>资产分类树（多层级：现金/债券/权益/基金/另类）</p>
      <Card style={{ marginTop: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Input.Search
            placeholder="搜索关键字"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onSearch={load}
            style={{ width: 280 }}
            allowClear
          />
        </Space>
        <Table
          rowKey="id"
          dataSource={items}
          pagination={{ pageSize: 20, total, showSizeChanger: false, showTotal: (t: number) => `共 ${t} 条` }}
          columns={[
            { title: '分类编码', dataIndex: 'category_code', width: 180 },
            { title: '分类名称', dataIndex: 'category_name', width: 200 },
            { title: '父分类ID', dataIndex: 'parent_id', width: 100,
              render: (v: number) => v === 0 ? <Tag>根分类</Tag> : v },
            { title: '分类类型', dataIndex: 'category_type', width: 100,
              render: (v: string) => <Tag color={
                v === 'CASH' ? 'green' : v === 'BOND' ? 'blue' : v === 'EQUITY' ? 'magenta' :
                v === 'FUND' ? 'cyan' : v === 'ALTERNATIVE' ? 'orange' : 'default'
              }>{v}</Tag> },
            { title: '风险权重', dataIndex: 'risk_weight', width: 100,
              render: (v: number) => `${(v * 100).toFixed(1)}%` },
            { title: '默认久期(年)', dataIndex: 'duration_default', width: 120,
              render: (v: number) => v?.toFixed(2) },
          ]}
        />
      </Card>
    </div>
  )
}