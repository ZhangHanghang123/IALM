/**
 * IALM 监管全局监控（新版）
 *
 * 设计要点：
 * 1. 顶部 Header: Title + 公司筛选 + Refresh + AI 助手入口
 * 2. 两行 6+6 共 12 张 KPI 卡：
 *    - 第一行"5号规则 + 6号规则 + 监管报表"
 *    - 第二行"压力测试 + 风险监控 + 资产负债"
 * 3. Row 3: 监管 6 情景压力测试结果表格
 * 4. Row 4: 风险指标告警列表 + 监管报表清单（左右两栏）
 * 5. Row 5: 最近风险事件列表（最新 10 条）
 *
 * 数据源：
 * - /algorithms/rule5/history → 5号规则历史（PASS/WARN/FAIL）
 * - /stress/results → 6号规则 + 压力测试超限
 * - /stress/scenarios → 6 大监管情景
 * - /risk/indicators → 风险指标（RED/YELLOW/GREEN）
 * - /risk/events → 风险事件
 * - /risk/regulatory-reports → 监管报表（filed_at 状态）
 * - /assets/holdings + /liabilities/cashflows → 资产规模合计
 */
import { useState, useEffect, useMemo } from 'react'
import {
  Row, Col, Card, Tag, Table, Spin, Empty, Select, Button, Space, Tooltip,
} from 'antd'
import {
  ReloadOutlined, RobotOutlined, CheckCircleOutlined,
  WarningOutlined, CloseCircleOutlined, AlertOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import {
  algorithmsApi, stressApi, riskApi, companiesApi, assetsApi, liabilitiesApi,
} from '../api'

// ═══ 6 色 KPI 主色 ═══
const KPI_COLORS = ['#667eea', '#722ed1', '#52c41a', '#fa8c16', '#13c2c2', '#eb2f96']

export default function RegulatoryOverview() {
  const [companyId, setCompanyId] = useState<number | undefined>(undefined)
  const [loading, setLoading] = useState(false)
  const [companies, setCompanies] = useState<any[]>([])

  // === 数据 ===
  const [history, setHistory] = useState<any[]>([])
  const [stressResults, setStressResults] = useState<any[]>([])
  const [scenarios, setScenarios] = useState<any[]>([])
  const [indicators, setIndicators] = useState<any[]>([])
  const [events, setEvents] = useState<any[]>([])
  const [regReports, setRegReports] = useState<any[]>([])
  const [holdings, setHoldings] = useState<any[]>([])

  const loadAll = async () => {
    setLoading(true)
    try {
      const f = (params: any) => companyId ? { ...params, company_id: companyId } : params
      const [
        rHist, rSR, rSc, rInd, rEv, rRR, rCmp, rH,
      ] = await Promise.all([
        algorithmsApi.history({ page: 1, page_size: 100 }),
        stressApi.results({ page: 1, page_size: 100 }),
        stressApi.scenarios({ page: 1, page_size: 50 }),
        riskApi.indicators({ page: 1, page_size: 100 }),
        riskApi.events({ page: 1, page_size: 100 }),
        riskApi.regulatoryReports({ page: 1, page_size: 100 }),
        companiesApi.list({ page: 1, page_size: 50 }),
        assetsApi.holdings(f({ page: 1, page_size: 200 })),
      ])
      setHistory(rHist.data?.items || [])
      setStressResults(rSR.data?.items || [])
      setScenarios(rSc.data?.items || [])
      setIndicators(rInd.data?.items || [])
      setEvents(rEv.data?.items || [])
      setRegReports(rRR.data?.items || [])
      setCompanies(rCmp.data?.items || [])
      setHoldings(rH.data?.items || [])
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => { loadAll() }, [companyId])

  // === 派生 KPI ===
  const derived = useMemo(() => {
    const pass = history.filter((h: any) => h.overall_status === 'PASS').length
    const warn = history.filter((h: any) => h.overall_status === 'WARN').length
    const fail = history.filter((h: any) => h.overall_status === 'FAIL').length
    const total = history.length
    const compliance = total > 0 ? Math.round((pass / total) * 100) : 0

    // 6号规则：压力测试达标率 = 通过 / 全部
    const passedStress = stressResults.filter((s: any) => s.passed || !s.is_breached).length
    const stressTotal = stressResults.length
    const stressPass = stressTotal > 0 ? Math.round((passedStress / stressTotal) * 100) : 0

    // 监管报表：已提交率
    const filed = regReports.filter((r: any) => r.status === 'FILED' || r.status === 'SUBMITTED').length
    const reportTotal = regReports.length
    const reportRate = reportTotal > 0 ? Math.round((filed / reportTotal) * 100) : 0

    // 超限情景
    const breached = stressResults.filter((s: any) => s.is_breached).length

    // 红色预警事件
    const redEvents = events.filter((e: any) => e.event_level === 'RED' || e.event_level === 'CRITICAL').length

    // 资产规模合计
    const totalAssetValue = holdings.reduce((acc: number, h: any) => acc + (h.cost_value || 0), 0)

    // 久期缺口均值（从 history 算）
    const gaps = history.filter((h: any) => h.duration_gap_years != null).map((h: any) => Number(h.duration_gap_years))
    const avgGap = gaps.length > 0 ? gaps.reduce((a: number, b: number) => a + b, 0) / gaps.length : 0

    return {
      pass, warn, fail, total, compliance,
      stressPass, stressTotal,
      filed, reportTotal, reportRate,
      breached,
      redEvents,
      totalAssetValue,
      avgGap,
    }
  }, [history, stressResults, regReports, events, holdings])

  // ═══ 5号规则饼图 ═══
  const rule5PieOption = useMemo(() => ({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'],
      data: [
        { name: '达标', value: derived.pass, itemStyle: { color: '#52c41a' } },
        { name: '预警', value: derived.warn, itemStyle: { color: '#faad14' } },
        { name: '不达标', value: derived.fail, itemStyle: { color: '#ff4d4f' } },
      ],
      label: { fontSize: 11, formatter: '{b}: {c}' },
    }],
  }), [derived])

  // ═══ 风险指标告警分布饼图 ═══
  const indicatorPieOption = useMemo(() => {
    const red = indicators.filter((i: any) => i.alert_level === 'RED').length
    const yellow = indicators.filter((i: any) => i.alert_level === 'YELLOW').length
    const green = indicators.filter((i: any) => i.alert_level === 'GREEN').length
    return {
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { fontSize: 11 } },
      series: [{
        type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'],
        data: [
          { name: '红色预警', value: red, itemStyle: { color: '#ff4d4f' } },
          { name: '黄色关注', value: yellow, itemStyle: { color: '#faad14' } },
          { name: '正常', value: green, itemStyle: { color: '#52c41a' } },
        ],
        label: { fontSize: 11, formatter: '{b}: {c}' },
      }],
    }
  }, [indicators])

  const kpiRow1 = [
    { label: '5号规则达标', value: derived.pass, color: '#52c41a', icon: <CheckCircleOutlined /> },
    { label: '5号规则预警', value: derived.warn, color: '#faad14', icon: <WarningOutlined /> },
    { label: '5号规则不达标', value: derived.fail, color: '#ff4d4f', icon: <CloseCircleOutlined /> },
    { label: '整体合规率', value: `${derived.compliance}%`, color: KPI_COLORS[0], icon: <AlertOutlined /> },
    { label: '6号规则达标率', value: derived.stressTotal > 0 ? `${derived.stressPass}%` : 'N/A', color: KPI_COLORS[1] },
    { label: '监管报表已提交', value: `${derived.filed} / ${derived.reportTotal}`, color: KPI_COLORS[4] },
  ]
  const kpiRow2 = [
    { label: '压力测试已运行', value: derived.stressTotal, color: '#666' },
    { label: '超限情景', value: derived.breached, color: derived.breached > 0 ? '#ff4d4f' : '#52c41a' },
    { label: '风险指标监控', value: indicators.length, color: '#666' },
    { label: '红色预警事件', value: derived.redEvents, color: derived.redEvents > 0 ? '#ff4d4f' : '#52c41a' },
    { label: '资产规模合计', value: `${derived.totalAssetValue.toLocaleString(undefined, { maximumFractionDigits: 0 })} 万`, color: '#666' },
    { label: '久期缺口均值', value: `${derived.avgGap > 0 ? '+' : ''}${derived.avgGap.toFixed(2)} 年`, color: Math.abs(derived.avgGap) > 2 ? '#faad14' : '#52c41a' },
  ]

  // === 压力测试结果表列 ===
  const stressColumns = [
    { title: '情景编码', dataIndex: 'scenario_code', width: 140, fixed: 'left' as const,
      render: (v: string) => <Tag color="purple">{v || '-'}</Tag> },
    { title: '情景名称', dataIndex: 'scenario_name', width: 160, ellipsis: true },
    { title: '机构', dataIndex: 'company_name', width: 100,
      render: (v: string) => <Tag>{v || '-'}</Tag> },
    { title: '报告日', dataIndex: 'report_date', width: 110,
      render: (v: string) => v?.slice(0, 10) || '-' },
    { title: '资产影响(万)', dataIndex: 'asset_impact', width: 130, align: 'right' as const,
      render: (v: number) => (
        <span style={{ color: v < 0 ? '#ff4d4f' : '#52c41a' }}>
          {v.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        </span>
      ),
      sorter: (a: any, b: any) => (a.asset_impact || 0) - (b.asset_impact || 0) },
    { title: '负债影响(万)', dataIndex: 'liability_impact', width: 130, align: 'right' as const,
      render: (v: number) => (
        <span style={{ color: v > 0 ? '#ff4d4f' : '#52c41a' }}>
          {v.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        </span>
      ) },
    { title: '净值变动(%)', dataIndex: 'nav_change_pct', width: 120, align: 'right' as const,
      render: (v: number) => {
        const pct = Number(v) * 100
        return (
          <span style={{ color: pct < 0 ? '#ff4d4f' : '#52c41a' }}>
            {pct.toFixed(2)}%
          </span>
        )
      },
      sorter: (a: any, b: any) => (a.nav_change_pct || 0) - (b.nav_change_pct || 0) },
    { title: '偿付能力(前→后)', width: 160, align: 'right' as const,
      render: (_: any, row: any) => {
        const b = Number(row.solvency_ratio_before || 0) * 100
        const a = Number(row.solvency_ratio_after || 0) * 100
        return <span>{b.toFixed(0)}% → {a.toFixed(0)}%</span>
      } },
    { title: '是否超限', dataIndex: 'is_breached', width: 100, fixed: 'right' as const,
      render: (v: boolean) => v ? <Tag color="error">超限</Tag> : <Tag color="success">达标</Tag>,
      filters: [{ text: '超限', value: true }, { text: '达标', value: false }],
      onFilter: (v: any, row: any) => row.is_breached === v,
    },
  ]

  // === 风险指标告警列表列 ===
  const indicatorColumns = [
    { title: '指标', dataIndex: 'indicator_name', width: 180, ellipsis: true },
    { title: '机构', dataIndex: 'company_name', width: 90 },
    { title: '当前值', dataIndex: 'current_value', width: 100, align: 'right' as const,
      render: (v: number) => v != null ? Number(v).toFixed(4) : '-' },
    { title: '告警级别', dataIndex: 'alert_level', width: 100, fixed: 'right' as const,
      render: (v: string) => {
        if (v === 'RED') return <Tag color="error" icon={<CloseCircleOutlined />}>红色</Tag>
        if (v === 'YELLOW') return <Tag color="warning" icon={<WarningOutlined />}>黄色</Tag>
        if (v === 'GREEN') return <Tag color="success" icon={<CheckCircleOutlined />}>绿色</Tag>
        return <Tag>{v || '-'}</Tag>
      },
      filters: [{ text: '红色', value: 'RED' }, { text: '黄色', value: 'YELLOW' }, { text: '绿色', value: 'GREEN' }],
      onFilter: (v: any, row: any) => row.alert_level === v },
  ]

  // === 监管报表清单列 ===
  const regReportColumns = [
    { title: '报表类型', dataIndex: 'report_type', width: 180, ellipsis: true },
    { title: '机构', dataIndex: 'company_name', width: 90 },
    { title: '报告期间', dataIndex: 'report_period', width: 120 },
    { title: '截止日期', dataIndex: 'filing_deadline', width: 110,
      render: (v: string) => v?.slice(0, 10) || '-' },
    { title: '状态', dataIndex: 'status', width: 110, fixed: 'right' as const,
      render: (v: string) => {
        if (v === 'FILED' || v === 'SUBMITTED') return <Tag color="success" icon={<CheckCircleOutlined />}>已提交</Tag>
        if (v === 'IN_PROGRESS' || v === 'DRAFT') return <Tag color="processing">编制中</Tag>
        if (v === 'OVERDUE' || v === 'EXPIRED') return <Tag color="error" icon={<CloseCircleOutlined />}>逾期</Tag>
        return <Tag>{v || '-'}</Tag>
      } },
  ]

  // === 风险事件列 ===
  const eventColumns = [
    { title: '事件', dataIndex: 'title', width: 240, ellipsis: true,
      render: (v: string, row: any) => (
        <Tooltip title={row.description || ''}>
          <span>{v || '-'}</span>
        </Tooltip>
      ) },
    { title: '机构', dataIndex: 'company_name', width: 90 },
    { title: '级别', dataIndex: 'event_level', width: 90, fixed: 'left' as const,
      render: (v: string) => {
        if (v === 'RED' || v === 'CRITICAL') return <Tag color="error">{v}</Tag>
        if (v === 'YELLOW' || v === 'HIGH') return <Tag color="warning">{v}</Tag>
        if (v === 'BLUE' || v === 'MEDIUM') return <Tag color="blue">{v}</Tag>
        return <Tag color="success">{v || '-'}</Tag>
      } },
    { title: '触发日期', dataIndex: 'occurred_at', width: 120,
      render: (v: string) => v?.slice(0, 10) || '-' },
    { title: '状态', dataIndex: 'status', width: 100, fixed: 'right' as const,
      render: (v: string) => {
        if (v === 'OPEN' || v === 'ACTIVE') return <Tag color="error">待处理</Tag>
        if (v === 'RESOLVED' || v === 'CLOSED') return <Tag color="success">已处理</Tag>
        if (v === 'IN_PROGRESS') return <Tag color="processing">处理中</Tag>
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
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 500 }}>IALM 监管全局监控</h2>
          <p style={{ color: '#999', fontSize: 13, margin: '4px 0 0' }}>
            5号规则 / 6号规则 / 压力测试 / 监管报表 · 数据更新时间 {new Date().toLocaleString('zh-CN')}
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

      {/* ═══ Row 1: 5号规则 + 6号规则 + 监管报表 ═══ */}
      <Row gutter={[12, 12]} style={{ marginBottom: 12 }}>
        {kpiRow1.map((k, i) => (
          <Col key={i} xs={12} sm={8} md={4}>
            <Card
              size="small"
              bordered={false}
              style={{ borderTop: `3px solid ${k.color}` }}
            >
              <div style={{ color: '#999', fontSize: 12, marginBottom: 4 }}>{k.label}</div>
              <div style={{ color: k.color, fontSize: 24, fontWeight: 500 }}>
                {k.icon && <span style={{ marginRight: 6, fontSize: 20 }}>{k.icon}</span>}
                {k.value}
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* ═══ Row 2: 压力测试 + 风险监控 + 资产负债 ═══ */}
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

      {/* ═══ Row 3: 监管 6 情景压力测试结果表 ═══ */}
      <Card
        size="small"
        title="监管 6 大压力情景测试结果（按报告日期倒序）"
        extra={<Tag color="purple">共 {stressResults.length} 条</Tag>}
        style={{ marginBottom: 12 }}
      >
        <Table
          rowKey="id"
          size="small"
          dataSource={stressResults.slice(0, 12)}
          columns={stressColumns}
          pagination={false}
          scroll={{ x: 1100 }}
          locale={{ emptyText: <Empty description="尚无压力测试结果，请前往【压力测试】运行监管情景" /> }}
        />
      </Card>

      {/* ═══ Row 4: 风险指标 + 风险指标分布 ═══ */}
      <Row gutter={[12, 12]} style={{ marginBottom: 12 }}>
        <Col xs={24} lg={12}>
          <Card
            size="small"
            title="风险指标监控告警（按告警级别排序）"
            extra={<Tag color="blue">共 {indicators.length} 项</Tag>}
          >
            <Table
              rowKey="id"
              size="small"
              dataSource={indicators.slice(0, 8)}
              columns={indicatorColumns}
              pagination={false}
              scroll={{ x: 600 }}
              locale={{ emptyText: <Empty description="暂无风险指标数据" /> }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card size="small" title="风险指标分布（按告警级别）">
            {indicators.length > 0 ? (
              <ReactECharts option={indicatorPieOption} style={{ height: 280 }} />
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
      </Row>

      {/* ═══ Row 5: 监管报表清单 + 风险事件 ═══ */}
      <Row gutter={[12, 12]}>
        <Col xs={24} lg={12}>
          <Card
            size="small"
            title="监管报表清单（按截止日期）"
            extra={<Tag color="cyan">共 {regReports.length} 份</Tag>}
          >
            <Table
              rowKey="id"
              size="small"
              dataSource={regReports.slice(0, 8)}
              columns={regReportColumns}
              pagination={false}
              scroll={{ x: 600 }}
              locale={{ emptyText: <Empty description="暂无监管报表数据" /> }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card
            size="small"
            title="近期风险事件（按触发日期倒序）"
            extra={<Tag color="orange">共 {events.length} 件</Tag>}
          >
            <Table
              rowKey="id"
              size="small"
              dataSource={events.slice(0, 8)}
              columns={eventColumns}
              pagination={false}
              scroll={{ x: 700 }}
              locale={{ emptyText: <Empty description="暂无风险事件" /> }}
            />
          </Card>
        </Col>
      </Row>
    </Spin>
  )
}