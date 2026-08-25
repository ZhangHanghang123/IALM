/**
 * IALM 压力测试（监管情景 + 结果 + 运行模拟）
 */
import { Card, Tabs, Tag, Typography, Statistic, Row, Col } from 'antd'
import { ThunderboltOutlined } from '@ant-design/icons'
import DataListPage from '../components/DataListPage'
import StressRunner from '../components/StressRunner'
import { stressApi } from '../api'

const { Title, Text } = Typography

const scenarioColors: Record<string, string> = {
  INTEREST: 'blue',
  LAPSE: 'orange',
  INVESTMENT: 'purple',
  FX: 'cyan',
  COMPREHENSIVE: 'red',
}

export default function Stress() {
  return (
    <Tabs
      defaultActiveKey="scenarios"
      type="card"
      items={[
        {
          key: 'scenarios',
          label: '监管情景',
          children: (
            <DataListPage
              title="监管压力情景（银保监会 6 个必选）"
              subtitle="5号规则+6号规则 规定的必选压力测试情景"
              fetcher={(p) => stressApi.scenarios(p)}
              columns={[
                { title: '情景编码', dataIndex: 'scenario_code', width: 200,
                  render: (v: string) => <Tag color="blue">{v}</Tag> },
                { title: '情景名称', dataIndex: 'scenario_name' },
                { title: '类型', dataIndex: 'scenario_type', width: 130,
                  render: (v: string) => <Tag color={scenarioColors[v]}>{v}</Tag> },
                { title: '来源', dataIndex: 'source', width: 120 },
                { title: '说明', dataIndex: 'description', width: 280 },
              ]}
            />
          ),
        },
        {
          key: 'results',
          label: '测试结果',
          children: (
            <DataListPage
              title="压力测试结果"
              subtitle="历史压力测试的 NAV/SCR/LCR 影响记录"
              fetcher={(p) => stressApi.results(p)}
              columns={[
                { title: '保险公司', dataIndex: 'company_name', width: 140 },
                { title: '情景', dataIndex: 'scenario_name' },
                { title: '测试日', dataIndex: 'test_date', width: 140 },
                { title: 'NAV 影响(万)', dataIndex: 'nav_impact', width: 140,
                  render: (v: number) => (
                    <span style={{ color: v < 0 ? '#ff4d4f' : '#52c41a' }}>
                      {v > 0 ? '+' : ''}{v?.toLocaleString()}
                    </span>
                  ) },
                { title: 'SCR 变化', dataIndex: 'scr_change', width: 120,
                  render: (v: number) => `${v?.toFixed(2)}%` },
                { title: 'LCR 变化', dataIndex: 'lcr_change', width: 120,
                  render: (v: number) => `${v?.toFixed(2)}%` },
                { title: '结果', dataIndex: 'passed', width: 100,
                  render: (v: number) => v ? <Tag color="green">通过</Tag> : <Tag color="red">未通过</Tag> },
              ]}
            />
          ),
        },
        {
          key: 'run',
          label: '运行模拟',
          children: <StressRunner />,
        },
      ]}
    />
  )
}