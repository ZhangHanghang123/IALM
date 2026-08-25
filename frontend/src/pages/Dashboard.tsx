/**
 * IALM 工作台（Dashboard）
 * 双行 KPI + 5 号规则状态 + 趋势 + 排行榜
 */
import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Tag, Space, Typography, Spin } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, WarningOutlined, FundOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { algorithmsApi } from '../api'

const { Title, Text } = Typography

export default function Dashboard() {
  const [algorithms, setAlgorithms] = useState<any[]>([])
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      algorithmsApi.list().then((r) => setAlgorithms(r.data.algorithms)).catch(() => {}),
      algorithmsApi.history({ page: 1, page_size: 10 }).then((r) => setHistory(r.data.items || [])).catch(() => {}),
    ]).finally(() => setLoading(false))
  }, [])

  const passCount = history.filter((h) => h.overall_status === 'PASS').length
  const warnCount = history.filter((h) => h.overall_status === 'WARN').length
  const failCount = history.filter((h) => h.overall_status === 'FAIL').length
  const totalCount = history.length

  const overallChartOption = {
    title: { text: '5号规则历史分析', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        data: [
          { value: passCount, name: '通过', itemStyle: { color: '#52c41a' } },
          { value: warnCount, name: '预警', itemStyle: { color: '#faad14' } },
          { value: failCount, name: '不达标', itemStyle: { color: '#ff4d4f' } },
        ],
        label: { formatter: '{b}: {c}' },
      },
    ],
  }

  const trendChartOption = {
    title: { text: '期限匹配率趋势', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 30, top: 50, bottom: 40 },
    xAxis: {
      type: 'category',
      data: history.slice(0, 10).reverse().map((h) => h.analysis_date?.slice(0, 10) || `#${h.id}`),
    },
    yAxis: { type: 'value', min: 0, max: 1 },
    series: [
      {
        type: 'line',
        data: history.slice(0, 10).reverse().map((h) => h.duration_match_ratio || 0),
        itemStyle: { color: '#667eea' },
        markLine: {
          data: [{ yAxis: 0.8, label: { formatter: '阈值 0.8' }, lineStyle: { type: 'dashed' } }],
        },
        areaStyle: { color: 'rgba(102, 126, 234, 0.1)' },
      },
    ],
  }

  if (loading) return <Spin tip="加载中..." style={{ width: '100%', marginTop: 100 }} />

  return (
    <div>
      <Title level={3}>📊 IALM 工作台</Title>
      <Text type="secondary">5 号规则监管指标全景监控</Text>

      {/* 第一行 KPI：5 号规则三项核心 + 久期缺口 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card><Statistic title="保险机构数量" value={10} prefix={<FundOutlined />} valueStyle={{ color: '#667eea' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="可用算法" value={algorithms.length} suffix="项" valueStyle={{ color: '#722ed1' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="历史分析次数" value={totalCount} valueStyle={{ color: '#13c2c2' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="通过率" value={totalCount > 0 ? Math.round((passCount / totalCount) * 100) : 0} suffix="%" valueStyle={{ color: '#52c41a' }} /></Card>
        </Col>
      </Row>

      {/* 第二行 KPI：5 号规则具体 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic title="期限匹配率达标" value={passCount + warnCount} suffix={`/ ${totalCount}`}
              prefix={<CheckCircleOutlined />} valueStyle={{ color: '#52c41a' }} />
            <Text type="secondary" style={{ fontSize: 12 }}>阈值 ≥ 0.80</Text>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="成本收益比达标" value={history.filter((h) => h.cost_yield_status === 'PASS').length} suffix={`/ ${totalCount}`}
              prefix={<CheckCircleOutlined />} valueStyle={{ color: '#52c41a' }} />
            <Text type="secondary" style={{ fontSize: 12 }}>寿险 ≥ 1.05 / 财险 ≥ 1.10</Text>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="现金流回正达标" value={history.filter((h) => h.cashflow_payback_status === 'PASS').length} suffix={`/ ${totalCount}`}
              prefix={<CheckCircleOutlined />} valueStyle={{ color: '#52c41a' }} />
            <Text type="secondary" style={{ fontSize: 12 }}>≤ 5 年</Text>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="预警/不达标" value={warnCount + failCount}
              prefix={<WarningOutlined />} valueStyle={{ color: warnCount + failCount > 0 ? '#ff4d4f' : '#52c41a' }} />
            <Text type="secondary" style={{ fontSize: 12 }}>需重点关注</Text>
          </Card>
        </Col>
      </Row>

      {/* 图表区 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card><ReactECharts option={overallChartOption} style={{ height: 300 }} /></Card>
        </Col>
        <Col span={12}>
          <Card><ReactECharts option={trendChartOption} style={{ height: 300 }} /></Card>
        </Col>
      </Row>

      {/* 14 算法清单 */}
      <Card title="14 项核心算法" style={{ marginTop: 16 }}>
        <Space wrap size={[12, 12]}>
          {algorithms.map((a) => (
            <Tag key={a.id} color="blue" style={{ padding: '4px 12px', fontSize: 13 }}>
              {a.id} · {a.name}
            </Tag>
          ))}
        </Space>
      </Card>
    </div>
  )
}