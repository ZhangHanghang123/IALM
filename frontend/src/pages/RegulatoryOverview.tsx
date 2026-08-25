/**
 * IALM 监管全景监控
 */
import { useEffect, useState } from 'react'
import { Card, Row, Col, Tag, Typography, Spin } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, WarningOutlined, AlertOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { algorithmsApi, riskApi } from '../api'

const { Title, Text } = Typography

const statusColor = { PASS: 'green', WARN: 'orange', FAIL: 'red' }

export default function RegulatoryOverview() {
  const [history, setHistory] = useState<any[]>([])
  const [indicators, setIndicators] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      algorithmsApi.history({ page: 1, page_size: 50 }),
      riskApi.indicators({ page: 1, page_size: 50 }),
    ]).then(([h, i]) => {
      setHistory(h.data.items || [])
      setIndicators(i.data.items || [])
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin tip="加载中..." style={{ width: '100%', marginTop: 100 }} />

  const statusCount = { PASS: 0, WARN: 0, FAIL: 0 }
  history.forEach(h => {
    const worst = h.overall_status
    if (worst && statusCount[worst as keyof typeof statusCount] != null) {
      statusCount[worst as keyof typeof statusCount]++
    }
  })

  const indiCount = { NORMAL: 0, LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 }
  indicators.forEach(i => {
    const w = i.warning_level
    if (w && indiCount[w as keyof typeof indiCount] != null) {
      indiCount[w as keyof typeof indiCount]++
    }
  })

  const passRate = history.length > 0 ? Math.round((statusCount.PASS / history.length) * 100) : 0

  const pieOption = {
    title: { text: '5号规则历史分析结果', left: 'center' },
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      data: [
        { value: statusCount.PASS, name: '通过', itemStyle: { color: '#52c41a' } },
        { value: statusCount.WARN, name: '预警', itemStyle: { color: '#faad14' } },
        { value: statusCount.FAIL, name: '不达标', itemStyle: { color: '#ff4d4f' } },
      ],
      label: { formatter: '{b}: {c}' },
    }],
  }

  return (
    <div>
      <Title level={3}>🏛️ 监管全景监控</Title>
      <Text type="secondary">5号规则 + 6号规则 + 风险预警 一站式监管视图</Text>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={6}><Card><div style={{ display: 'flex', alignItems: 'center' }}>
          <CheckCircleOutlined style={{ fontSize: 32, color: '#52c41a', marginRight: 12 }} />
          <div><div style={{ fontSize: 24, fontWeight: 600 }}>{statusCount.PASS}</div><div style={{ color: '#999', fontSize: 12 }}>5号规则通过</div></div>
        </div></Card></Col>
        <Col span={6}><Card><div style={{ display: 'flex', alignItems: 'center' }}>
          <WarningOutlined style={{ fontSize: 32, color: '#faad14', marginRight: 12 }} />
          <div><div style={{ fontSize: 24, fontWeight: 600 }}>{statusCount.WARN}</div><div style={{ color: '#999', fontSize: 12 }}>预警</div></div>
        </div></Card></Col>
        <Col span={6}><Card><div style={{ display: 'flex', alignItems: 'center' }}>
          <CloseCircleOutlined style={{ fontSize: 32, color: '#ff4d4f', marginRight: 12 }} />
          <div><div style={{ fontSize: 24, fontWeight: 600 }}>{statusCount.FAIL}</div><div style={{ color: '#999', fontSize: 12 }}>不达标</div></div>
        </div></Card></Col>
        <Col span={6}><Card><div style={{ display: 'flex', alignItems: 'center' }}>
          <AlertOutlined style={{ fontSize: 32, color: '#c2410c', marginRight: 12 }} />
          <div><div style={{ fontSize: 24, fontWeight: 600 }}>{passRate}%</div><div style={{ color: '#999', fontSize: 12 }}>整体合规率</div></div>
        </div></Card></Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}><Card title="5号规则历史分析"><ReactECharts option={pieOption} style={{ height: 300 }} /></Card></Col>
        <Col span={12}><Card title="风险指标分布">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
            {Object.entries(indiCount).map(([k, v]) => (
              <div key={k} style={{ flex: '0 0 calc(50% - 6px)' }}>
                <Tag color={k === 'CRITICAL' || k === 'HIGH' ? 'red' : k === 'MEDIUM' ? 'orange' : k === 'LOW' ? 'blue' : 'green'} style={{ fontSize: 13, padding: '4px 8px' }}>
                  {k}: {v}
                </Tag>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 16 }}>
            <Title level={5}>最近 5 条分析记录</Title>
            {history.slice(0, 5).map(h => (
              <div key={h.id} style={{ marginBottom: 8 }}>
                <Tag color={statusColor[h.overall_status as keyof typeof statusColor]}>{h.overall_status}</Tag>
                <Text>公司 {h.company_id} · 期限匹配 {(h.duration_match_ratio * 100 || 0).toFixed(2)}%</Text>
              </div>
            ))}
          </div>
        </Card></Col>
      </Row>
    </div>
  )
}