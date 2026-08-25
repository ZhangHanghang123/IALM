/**
 * IALM 风险与监管（风险偏好 + 风险指标 + 风险事件 + 监管报表）
 */
import { Card, Tabs, Tag, Typography } from 'antd'
import DataListPage from '../components/DataListPage'
import { riskApi } from '../api'

const { Title, Text } = Typography

const warningColors: Record<string, string> = {
  NORMAL: 'green',
  LOW: 'blue',
  MEDIUM: 'orange',
  HIGH: 'red',
  CRITICAL: 'red',
}

const statusColors: Record<string, string> = {
  ACTIVE: 'green',
  CLOSED: 'default',
  INVESTIGATING: 'orange',
  RESOLVED: 'blue',
}

const complianceColors: Record<string, string> = {
  COMPLIANT: 'green',
  NON_COMPLIANT: 'red',
  PENDING: 'orange',
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
              subtitle="公司层面的风险容忍度（最大回撤/VaR/久期缺口等）"
              fetcher={(p) => riskApi.preferences(p)}
              columns={[
                { title: '公司ID', dataIndex: 'company_id', width: 100 },
                { title: '偏好等级', dataIndex: 'preference_level', width: 160 },
                { title: '最大回撤', dataIndex: 'max_drawdown', width: 140,
                  render: (v: number) => v != null ? `${(v * 100).toFixed(2)}%` : '-' },
                { title: '最大 VaR', dataIndex: 'max_var', width: 140,
                  render: (v: number) => v != null ? `${(v * 100).toFixed(2)}%` : '-' },
                { title: '久期缺口', dataIndex: 'max_duration_gap', width: 120,
                  render: (v: number) => v != null ? `${v.toFixed(2)} 年` : '-' },
                { title: '偿付能力', dataIndex: 'target_solvency_ratio', width: 140,
                  render: (v: number) => v != null ? `${(v * 100).toFixed(1)}%` : '-' },
                { title: '目标 LCR', dataIndex: 'target_lcr', width: 120,
                  render: (v: number) => v != null ? `${(v * 100).toFixed(1)}%` : '-' },
                { title: '生效日', dataIndex: 'effective_date', width: 120 },
                { title: '审批人', dataIndex: 'approved_by', width: 120 },
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
              subtitle="实时风险指标 + 阈值预警"
              fetcher={(p) => riskApi.indicators(p)}
              columns={[
                { title: '保险公司', dataIndex: 'company_name', width: 140 },
                { title: '指标编码', dataIndex: 'indicator_code', width: 160 },
                { title: '指标名称', dataIndex: 'indicator_name' },
                { title: '当前值', dataIndex: 'current_value', width: 120,
                  render: (v: number) => v?.toFixed(4) },
                { title: '阈值', dataIndex: 'threshold_value', width: 120,
                  render: (v: number) => v?.toFixed(4) },
                { title: '预警等级', dataIndex: 'warning_level', width: 100,
                  render: (v: string) => <Tag color={warningColors[v]}>{v}</Tag> },
                { title: '监控日', dataIndex: 'monitor_date', width: 120 },
                { title: '状态', dataIndex: 'status', width: 100,
                  render: (v: string) => <Tag color={v === 'BREACH' ? 'red' : 'green'}>{v}</Tag> },
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
              subtitle="重大风险事件追踪与处置"
              fetcher={(p) => riskApi.events(p)}
              columns={[
                { title: '保险公司', dataIndex: 'company_name', width: 140 },
                { title: '事件类型', dataIndex: 'event_type', width: 160 },
                { title: '等级', dataIndex: 'event_level', width: 100,
                  render: (v: string) => <Tag color={v === 'CRITICAL' ? 'red' : v === 'HIGH' ? 'orange' : 'blue'}>{v}</Tag> },
                { title: '标题', dataIndex: 'title', width: 200 },
                { title: '描述', dataIndex: 'description', width: 240 },
                { title: '发生时间', dataIndex: 'occurred_at', width: 180 },
                { title: '状态', dataIndex: 'status', width: 120,
                  render: (v: string) => <Tag color={statusColors[v]}>{v}</Tag> },
                { title: '处理人', dataIndex: 'handler', width: 100 },
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
              subtitle="季度量化评估 / 年度压力测试 / 半年度匹配分析"
              fetcher={(p) => riskApi.regulatoryReports(p)}
              columns={[
                { title: '保险公司', dataIndex: 'company_name', width: 140 },
                { title: '报表类型', dataIndex: 'report_type', width: 180 },
                { title: '报告期间', dataIndex: 'report_period', width: 120 },
                { title: '提交日', dataIndex: 'submit_date', width: 140 },
                { title: '合规状态', dataIndex: 'compliance_status', width: 130,
                  render: (v: string) => <Tag color={complianceColors[v]}>{v}</Tag> },
                { title: '备注', dataIndex: 'remark', width: 240 },
              ]}
            />
          ),
        },
      ]}
    />
  )
}