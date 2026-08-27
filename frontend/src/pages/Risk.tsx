/**
 * IALM 风险与监管（风险偏好 + 风险指标 + 风险事件 + 监管报表）
 */
import { Card, Tabs, Tag, Typography, Tooltip, Statistic, Row, Col, Space } from 'antd'
import DataListPage from '../components/DataListPage'
import { riskApi } from '../api'

const { Title, Text } = Typography

const alertColors: Record<string, string> = {
  GREEN: 'green',
  YELLOW: 'orange',
  RED: 'red',
}

const trendIcons: Record<string, string> = {
  UP: '↑',
  DOWN: '↓',
  STABLE: '→',
}

const eventLevelColors: Record<string, string> = {
  HIGH: 'red',
  MEDIUM: 'orange',
  LOW: 'blue',
}

const eventStatusColors: Record<string, string> = {
  OPEN: 'red',
  MONITORING: 'orange',
  RESOLVED: 'green',
  CLOSED: 'default',
}

const regStatusColors: Record<string, string> = {
  FILED: 'green',
  DRAFT: 'orange',
  OVERDUE: 'red',
  REJECTED: 'red',
}

export default function Risk() {
  return (
    <Tabs
      defaultActiveKey="preferences"
      type="card"
      items={[
        {
          key: 'preferences',
          label: '风险偏好',
          children: (
            <DataListPage
              title="风险偏好声明"
              subtitle="公司层面的风险容忍度（久期缺口/期限匹配/回正期/成本收益比）"
              fetcher={(p) => riskApi.preferences(p)}
              columns={[
                { title: '公司', dataIndex: 'company_id', width: 100,
                  render: (v: number) => v === 4 ? '新华保险' : v },
                { title: '偏好名称', dataIndex: 'preference_name', width: 220 },
                { title: '生效日', dataIndex: 'effective_date', width: 130 },
                { title: '到期日', dataIndex: 'expiry_date', width: 130 },
                { title: '久期缺口(下限)', dataIndex: 'duration_gap_min', width: 150,
                  render: (v: number) => v?.toFixed(2) },
                { title: '久期缺口(上限)', dataIndex: 'duration_gap_max', width: 150,
                  render: (v: number) => v?.toFixed(2) },
                { title: '期限匹配率(最低)', dataIndex: 'duration_match_min', width: 160,
                  render: (v: number) => (v * 100).toFixed(1) + '%' },
                { title: '回正期上限(年)', dataIndex: 'cashflow_payback_max', width: 150,
                  render: (v: number) => v?.toFixed(1) },
                { title: '成本收益比(最低)', dataIndex: 'cost_yield_ratio_min', width: 160,
                  render: (v: number) => v?.toFixed(2) },
              ]}
            />
          ),
        },
        {
          key: 'indicators',
          label: '风险指标',
          children: (
            <DataListPage
              title="风险指标监控"
              subtitle="实时风险指标 + 三色阈值预警（绿/黄/红）"
              fetcher={(p) => riskApi.indicators(p)}
              columns={[
                { title: '保险公司', dataIndex: 'company_name', width: 120 },
                { title: '指标编码', dataIndex: 'indicator_code', width: 160,
                  render: (v: string) => <Tag color="blue">{v}</Tag> },
                { title: '指标名称', dataIndex: 'indicator_name', width: 200 },
                { title: '当前值', dataIndex: 'current_value', width: 110,
                  render: (v: number, r: any) => {
                    if (r.extra_json?.unit === '%') return v?.toFixed(2) + '%'
                    if (r.extra_json?.unit === '年') return v?.toFixed(2) + '年'
                    return v?.toFixed(4)
                  } },
                { title: '绿阈值', dataIndex: 'threshold_green', width: 100,
                  render: (v: number) => v?.toFixed(2) },
                { title: '黄阈值', dataIndex: 'threshold_yellow', width: 100,
                  render: (v: number) => v?.toFixed(2) },
                { title: '红阈值', dataIndex: 'threshold_red', width: 100,
                  render: (v: number) => v?.toFixed(2) },
                { title: '预警等级', dataIndex: 'alert_level', width: 100,
                  render: (v: string) => <Tag color={alertColors[v]}>{v}</Tag> },
                { title: '趋势', dataIndex: 'trend', width: 80,
                  render: (v: string) => (
                    <span style={{ fontSize: 16, fontWeight: 600 }}>
                      {trendIcons[v] || '-'} {v}
                    </span>
                  ) },
                { title: '报告日', dataIndex: 'monitor_date', width: 130 },
              ]}
            />
          ),
        },
        {
          key: 'events',
          label: '风险事件',
          children: (
            <DataListPage
              title="风险事件登记"
              subtitle="重大风险事件追踪与处置（市场/信用/流动性/偿付能力/操作/合规等）"
              fetcher={(p) => riskApi.events(p)}
              columns={[
                { title: '保险公司', dataIndex: 'company_name', width: 120 },
                { title: '事件编码', dataIndex: 'event_code', width: 160,
                  render: (v: string) => <Tag>{v}</Tag> },
                { title: '事件名称', dataIndex: 'title', width: 220, ellipsis: true },
                { title: '类型', dataIndex: 'event_type', width: 130,
                  render: (v: string) => <Tag color="purple">{v}</Tag> },
                { title: '等级', dataIndex: 'event_level', width: 100,
                  render: (v: string) => <Tag color={eventLevelColors[v]}>{v}</Tag> },
                { title: '触发值', dataIndex: 'trigger_value', width: 110,
                  render: (v: number) => v?.toFixed(2) },
                { title: '阈值', dataIndex: 'threshold_value', width: 100,
                  render: (v: number) => v?.toFixed(2) },
                { title: '发生时间', dataIndex: 'occurred_at', width: 180 },
                { title: '状态', dataIndex: 'status', width: 130,
                  render: (v: string) => <Tag color={eventStatusColors[v]}>{v}</Tag> },
              ]}
            />
          ),
        },
        {
          key: 'regulatory-reports',
          label: '监管报表',
          children: (
            <DataListPage
              title="监管报表"
              subtitle="偿付能力季报 / 资产负债季报 / 风险综合评级 / 重大事项报告"
              fetcher={(p) => riskApi.regulatoryReports(p)}
              columns={[
                { title: '保险公司', dataIndex: 'company_name', width: 120 },
                { title: '报表类型', dataIndex: 'report_type', width: 200 },
                { title: '报告期间', dataIndex: 'report_period', width: 120 },
                { title: '报告日', dataIndex: 'report_date', width: 130 },
                { title: '截止日', dataIndex: 'filing_deadline', width: 130 },
                { title: '提交时间', dataIndex: 'filed_at', width: 180 },
                { title: '格式', dataIndex: 'file_format', width: 80,
                  render: (v: string) => <Tag color="blue">{v}</Tag> },
                { title: '文件', dataIndex: 'file_path', width: 240, ellipsis: true,
                  render: (v: string) => <Text type="secondary" style={{ fontFamily: 'monospace' }}>{v}</Text> },
                { title: '状态', dataIndex: 'compliance_status', width: 110,
                  render: (v: string) => <Tag color={regStatusColors[v] || 'default'}>{v}</Tag> },
              ]}
            />
          ),
        },
      ]}
    />
  )
}