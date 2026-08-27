/**
 * IALM 系统仪表盘（新版）
 *
 * 设计要点：
 * 1. 顶部 Header 含 Title + 公司筛选 + 情景筛选 + Refresh + AI 助手入口
 * 2. 两行 6+6 共 12 张 KPI 卡：
 *    - 第一行"核心指标"：borderTop 3px 实色 + 大字号 + 品牌主色
 *    - 第二行"能力指标"：白底居中，无 borderTop
 * 3. Row 3: 5号规则历史趋势（折线）+ 资产配置分布（环形）
 * 4. Row 4: 最近 10 条 5号规则分析记录（精简 6 列表格）
 *
 * 数据源：
 * - /companies  → 保险公司数量
 * - /assets/holdings → 资产持仓数 + 资产配置分布
 * - /liabilities/policies → 保单数
 * - /algorithms/rule5/algorithms → 14 项核心算法
 * - /assets/cashflows + /liabilities/cashflows → 现金流记录合计
 * - /algorithms/rule5/history → 历史趋势 + 最近分析
 * - /stress/scenarios + /models/versions + /risk/indicators + /risk/regulatory-reports
 */
import { useState, useEffect, useMemo } from 'react'
import {
  Row, Col, Card, Tag, Table, Spin, Empty, Select, Button, Space, Tooltip,
} from 'antd'
import {
  ReloadOutlined, RobotOutlined, CheckCircleOutlined,
  WarningOutlined, CloseCircleOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import {
  algorithmsApi, assetsApi, liabilitiesApi, companiesApi, stressApi,
  riskApi, modelsApi,
} from '../api'

// ═══ 6 色 KPI 主色（沿用 5 项目统一门户配色循环） ═══
const KPI_COLORS = ['#667eea', '#722ed1', '#52c41a', '#fa8c16', '#13c2c2', '#eb2f96']

const ICON_MAP: Record<string, string> = {
  PASS: '✓', WARN: '⚠', FAIL: '✗', GREEN: '●', YELLOW: '●', RED: '●',
}

export default function Dashboard() {
  // === 筛选与状态 ===
  const [companyId, setCompanyId] = useState<number | undefined>(undefined)
  const [scenarioCode, setScenarioCode] = useState<string>('BASE')
  const [loading, setLoading] = useState(false)
  const [companies, setCompanies] = useState<any[]>([])

  // === 数据 ===
  const [holdings, setHoldings] = useState<any[]>([])
  const [policies, setPolicies] = useState<any[]>([])
  const [assetCFs, setAssetCFs] = useState<any[]>([])
  const [liabCFs, setLiabCFs] = useState<any[]>([])
  const [algorithms, setAlgorithms] = useState<any[]>([])
  const [history, setHistory] = useState<any[]>([])
  const [scenarios, setScenarios] = useState<any[]>([])
  const [indicators, setIndicators] = useState<any[]>([])
  const [modelVersions, setModelVersions] = useState<any[]>([])
  const [regReports, setRegReports] = useState<any[]>([])

  const loadAll = async () => {
    setLoading(true)
    try {
      const filter = (params: any) => companyId ? { ...params, company_id: companyId } : params
      const [
        rHoldings, rPolicies, rAssCF, rLiabCF, rAlgo, rHist,
        rSc, rInd, rMV, rRR, rCmp,
      ] = await Promise.all([
        assetsApi.holdings(filter({ page: 1, page_size: 200 })),
        liabilitiesApi.policies(filter({ page: 1, page_size: 200 })),
        assetsApi.cashflows(filter({ page: 1, page_size: 500 })),
        liabilitiesApi.cashflows(filter({ page: 1, page_size: 500 })),
        algorithmsApi.list(),
        algorithmsApi.history({ page: 1, page_size: 20 }),
        stressApi.scenarios({ page: 1, page_size: 50 }),
        riskApi.indicators({ page: 1, page_size: 100 }),
        modelsApi.versions({ page: 1, page_size: 50 }),
        riskApi.regulatoryReports({ page: 1, page_size: 50 }),
        companiesApi.list({ page: 1, page_size: 50 }),
      ])
      setHoldings(rHoldings.data?.items || [])
      setPolicies(rPolicies.data?.items || [])
      setAssetCFs(rAssCF.data?.items || [])
      setLiabCFs(rLiabCF.data?.items || [])
      setAlgorithms(rAlgo.data || [])
      setHistory(rHist.data?.items || [])
      setScenarios(rSc.data?.items || [])
      setIndicators(rInd.data?.items || [])
      setModelVersions(rMV.data?.items || [])
      setRegReports(rRR.data?.items || [])
      setCompanies(rCmp.data?.items || [])
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => { loadAll() }, [companyId])
  useEffect(() => { setScenarioCode(scenarioCode) }, [scenarioCode])

  // === KPI 派生指标 ===
  const stats = useMemo(() => {
    const companiesCount = companies.length
    const holdingsCount = holdings.length
    const policiesCount = policies.length
    const algorithmsCount = algorithms.length
    const totalCF = assetCFs.length + liabCFs.length
    const histories = history

    const pass = histories.filter((h: any) => h.overall_status === 'PASS').length
    const warn = histories.filter((h: any) => h.overall_status === 'WARN').length
    const fail = histories.filter((h: any) => h.overall_status === 'FAIL').length
    const total = histories.length
    const compliance = total > 0 ? Math.round((pass / total) * 100) : 0

    return {
      companiesCount, holdingsCount, policiesCount, algorithmsCount,
      totalCF, histories, pass, warn, fail, total, compliance,
      scenariosCount: scenarios.length,
      indicatorsCount: indicators.length,
      modelVersionsCount: modelVersions.length,
      regReportsCount: regReports.length,
    }
  }, [companies, holdings, policies, algorithms, assetCFs, liabCFs, history, scenarios, indicators, modelVersions, regReports])

  // === 资产配置分布（按 category_code 聚合）===
  const allocationByCategory = useMemo(() => {
    const map = new Map<string, number>()
    for (const h of holdings) {
      const k = h.category_code || 'OTHER'
      map.set(k, (map.get(k) || 0) + (h.cost_value || 0))
    }
    return Array.from(map.entries())
      .map(([k, v]) => ({ name: k, value: v }))
      .sort((a, b) => b.value - a.value)
  }, [holdings])

  // === 5号规则历史趋势（按 analysis_date 聚合 PASS 占比）===
  const trendData = useMemo(() => {
    return stats.histories
      .slice()
      .reverse()
      .slice(-12)
      .map((h: any) => {
        const date = (h.analysis_date || h.report_date || '').slice(0, 10)
        const ratio = h.duration_match_ratio != null ? Number(h.duration_match_ratio) * 100 : 0
        return { date, ratio }
      })
      .filter((d: any) => d.date)
  }, [stats.histories])

  // === 趋势图配置 ===
  const trendOption = useMemo(() => ({
    grid: { left: 40, right: 16, top: 16, bottom: 32 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: trendData.map((d: any) => d.date),
      axisLabel: { fontSize: 11, color: '#999', rotate: trendData.length > 8 ? 30 : 0 },
    },
    yAxis: {
      type: 'value', min: 50, max: 100,
      axisLabel: { fontSize: 11, color: '#999', formatter: '{value}%' },
    },
    series: [{
      type: 'line', smooth: true, symbol: 'circle', symbolSize: 6,
      data: trendData.map((d: any) => d.ratio.toFixed(1)),
      lineStyle: { color: '#667eea', width: 2 },
      itemStyle: { color: '#667eea' },
      areaStyle: { color: 'rgba(102,126,234,0.10)' },
      markLine: {
        symbol: 'none', silent: true,
        lineStyle: { color: '#faad14', type: 'dashed', width: 1 },
        label: { fontSize: 11, color: '#faad14' },
        data: [{ yAxis: 80, name: '阈值 80%' }],
      },
    }],
  }), [trendData])

  // === 资产配置饼图配置 ===
  const allocationOption = useMemo(() => ({
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => `${p.name}<br/>${p.value.toLocaleString(undefined, { maximumFractionDigits: 0 })} 万 (${p.percent.toFixed(1)}%)`,
    },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '45%'],
      label: { fontSize: 11, formatter: '{b}: {c}' },
      labelLine: { length: 8, length2: 8 },
      data: allocationByCategory.length > 0
        ? allocationByCategory
        : [{ name: '暂无数据', value: 1 }],
      color: KPI_COLORS,
    }],
  }), [allocationByCategory])

  const kpiRow1 = [
    { label: '保险公司', value: stats.companiesCount, color: KPI_COLORS[0] },
    { label: '资产持仓数', value: stats.holdingsCount, color: KPI_COLORS[1] },
    { label: '保单主档', value: stats.policiesCount, color: KPI_COLORS[2] },
    { label: '14 项核心算法', value: `${stats.algorithmsCount} / 14`, color: KPI_COLORS[3] },
    { label: '现金流记录', value: stats.totalCF.toLocaleString(), color: KPI_COLORS[4] },
    { label: '5号规则合规率', value: `${stats.compliance}%`, color: stats.compliance >= 80 ? '#52c41a' : stats.compliance >= 60 ? '#faad14' : '#ff4d4f' },
  ]
  const kpiRow2 = [
    { label: '历史分析次数', value: stats.total, color: '#666' },
    { label: '监管压力情景', value: stats.scenariosCount, color: '#666' },
    { label: '风险指标监控', value: stats.indicatorsCount, color: '#666' },
    { label: '模型版本', value: stats.modelVersionsCount, color: '#666' },
    { label: '监管报表', value: stats.regReportsCount, color: '#666' },
    { label: '达标 / 预警 / 不达标', value: `${stats.pass} / ${stats.warn} / ${stats.fail}`, color: stats.fail > 0 ? '#ff4d4f' : stats.warn > 0 ? '#faad14' : '#52c41a' },
  ]

  // === 最近分析记录表格列 ===
  const historyColumns = [
    { title: '机构', dataIndex: 'company_id', width: 90, render: (v: number) => <Tag color="purple">{v}</Tag> },
    { title: '分析日期', dataIndex: 'analysis_date', width: 130, render: (v: string) => v?.slice(0, 10) || '-' },
    { title: '期限匹配率', dataIndex: 'duration_match_ratio', width: 120,
      render: (v: number) => v != null ? `${(Number(v) * 100).toFixed(1)}%` : '-',
      sorter: (a: any, b: any) => (a.duration_match_ratio || 0) - (b.duration_match_ratio || 0) },
    { title: '成本收益比', dataIndex: 'cost_yield_ratio', width: 110,
      render: (v: number) => v != null ? Number(v).toFixed(3) : '-',
      sorter: (a: any, b: any) => (a.cost_yield_ratio || 0) - (b.cost_yield_ratio || 0) },
    { title: '回正期(年)', dataIndex: 'cashflow_payback_years', width: 110,
      render: (v: number) => v != null ? `${Number(v).toFixed(1)}` : '-',
      sorter: (a: any, b: any) => (a.cashflow_payback_years || 0) - (b.cashflow_payback_years || 0) },
    { title: '状态', dataIndex: 'overall_status', width: 100, fixed: 'right' as const,
      render: (v: string) => {
        if (v === 'PASS') return <Tag color="success" icon={<CheckCircleOutlined />}>达标</Tag>
        if (v === 'WARN') return <Tag color="warning" icon={<WarningOutlined />}>预警</Tag>
        if (v === 'FAIL') return <Tag color="error" icon={<CloseCircleOutlined />}>不达标</Tag>
        return <Tag>{v || '-'}</Tag>
      } },
  ]

  return (
    <Spin spinning={loading}>
      {/* ═══ 顶部 Header ═══ */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: 16, flexWrap: 'wrap', gap: 8,
      }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 500 }}>IALM 系统仪表盘</h2>
          <p style={{ color: '#999', fontSize: 13, margin: '4px 0 0' }}>
            资产负债全景监控 · 数据更新时间 {new Date().toLocaleString('zh-CN')}
          </p>
        </div>
        <Space size={8} wrap>
          <Select
            allowClear
            value={companyId}
            onChange={(v) => setCompanyId(v)}
            placeholder="全部机构"
            style={{ width: 160 }}
            options={companies.map((c: any) => ({
              value: c.id, label: c.company_short || c.company_name || `机构 ${c.id}`,
            }))}
          />
          <Select
            value={scenarioCode}
            onChange={setScenarioCode}
            style={{ width: 130 }}
            options={[
              { value: 'BASE', label: '基础情景' },
              { value: 'UP200', label: '利率 +200bp' },
              { value: 'DOWN200', label: '利率 -200bp' },
              { value: 'STRESS', label: '压力情景' },
            ]}
          />
          <Button icon={<ReloadOutlined />} onClick={loadAll}>刷新</Button>
          <Tooltip title="AI 智能助手（即将上线）">
            <Button
              type="primary"
              shape="circle"
              icon={<RobotOutlined />}
              style={{ background: 'linear-gradient(135deg, #667eea, #764ba2)' }}
            />
          </Tooltip>
        </Space>
      </div>

      {/* ═══ Row 1: 6 张核心 KPI 卡（borderTop 3px 实色） ═══ */}
      <Row gutter={[12, 12]} style={{ marginBottom: 12 }}>
        {kpiRow1.map((k, i) => (
          <Col key={i} xs={12} sm={8} md={4}>
            <Card
              size="small"
              bordered={false}
              style={{ borderTop: `3px solid ${k.color}` }}
            >
              <div style={{ color: '#999', fontSize: 12, marginBottom: 4 }}>{k.label}</div>
              <div style={{ color: k.color, fontSize: 24, fontWeight: 500 }}>{k.value}</div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* ═══ Row 2: 6 张能力 KPI 卡（白底居中，无 borderTop） ═══ */}
      <Row gutter={[12, 12]} style={{ marginBottom: 12 }}>
        {kpiRow2.map((k, i) => (
          <Col key={i} xs={12} sm={8} md={4}>
            <Card size="small" bordered={false}>
              <div style={{ color: '#999', fontSize: 12, marginBottom: 4 }}>{k.label}</div>
              <div style={{ color: k.color, fontSize: 22, fontWeight: 500, textAlign: 'center' }}>{k.value}</div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* ═══ Row 3: 趋势图 + 资产配置分布 ═══ */}
      <Row gutter={[12, 12]} style={{ marginBottom: 12 }}>
        <Col xs={24} lg={12}>
          <Card size="small" title="5号规则历史趋势（期限匹配率，近 12 次）">
            {trendData.length > 0 ? (
              <ReactECharts option={trendOption} style={{ height: 280 }} />
            ) : (
              <Empty description="暂无历史分析记录" />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card size="small" title="资产配置分布（按分类账面价值，万元）">
            {allocationByCategory.length > 0 ? (
              <ReactECharts option={allocationOption} style={{ height: 280 }} />
            ) : (
              <Empty description="暂无持仓数据" />
            )}
          </Card>
        </Col>
      </Row>

      {/* ═══ Row 4: 最近 N 条 5号规则分析记录 ═══ */}
      <Card
        size="small"
        title={`最近 ${Math.min(stats.histories.length, 10)} 条 5号规则分析记录`}
        extra={<Tag color="blue">共 {stats.histories.length} 条</Tag>}
      >
        <Table
          rowKey="id"
          size="small"
          dataSource={stats.histories.slice(0, 10)}
          columns={historyColumns}
          pagination={false}
          scroll={{ x: 700 }}
          locale={{ emptyText: <Empty description="暂无历史分析记录" /> }}
        />
      </Card>
    </Spin>
  )
}