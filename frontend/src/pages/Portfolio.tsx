/**
 * IALM 投资组合（Markowitz + Black-Litterman + 资产配置 + 业绩归因）
 */
import { useState, useEffect } from 'react'
import { Card, Tabs, Form, InputNumber, Button, Row, Col, Statistic, Table, Typography, Alert, message } from 'antd'
import { FundOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import DataListPage from '../components/DataListPage'
import { portfolioApi } from '../api'

const { Title, Text } = Typography

export default function Portfolio() {
  return (
    <Tabs
      defaultActiveKey="markowitz"
      type="card"
      items={[
        { key: 'markowitz', label: 'Markowitz 配置', children: <MarkowitzPage /> },
        { key: 'black-litterman', label: 'Black-Litterman', children: <BlackLittermanPage /> },
        { key: 'allocations', label: '资产配置', children: <AllocationsPage /> },
        { key: 'attributions', label: 'Brinson 业绩归因', children: <AttributionsPage /> },
      ]}
    />
  )
}

function MarkowitzPage() {
  const [form] = Form.useForm()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const onOptimize = async () => {
    const v = await form.validateFields()
    setLoading(true)
    try {
      const returns = JSON.parse(`[${v.returns}]`) as number[]
      const covRows = v.cov.split(';').map(r => r.split(',').map(Number))
      const r = await portfolioApi.markowitz({
        expected_returns: returns,
        cov_matrix: covRows,
        risk_free_rate: v.rfRate / 100,
      })
      setResult(r.data)
      if (r.data.error) message.error(r.data.error)
      else message.success('优化完成')
    } catch (e: any) {
      message.error(e?.message || '优化失败')
    }
    setLoading(false)
  }

  const chartOption = result && !result.error && {
    title: { text: 'Markowitz 最优权重', left: 'center' },
    tooltip: {},
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      label: { formatter: '{b}: {(c*100).toFixed(1)}%' },
      data: result.weights.map((w: number, i: number) => ({
        value: w,
        name: `资产${i + 1}`,
      })),
    }],
  }

  return (
    <div>
      <Title level={3}>📊 Markowitz 均值-方差最优配置（ALG-008）</Title>
      <Text type="secondary">max(μᵀw) s.t. wᵀΣw ≤ σ²_max, Σw = 1, w ≥ 0</Text>

      <Card style={{ marginTop: 16 }}>
        <Form form={form} layout="vertical" initialValues={{
          returns: '0.06, 0.08, 0.10, 0.12',
          cov: '0.04,0.01,0.01,0.01; 0.01,0.09,0.02,0.02; 0.01,0.02,0.16,0.03; 0.01,0.02,0.03,0.25',
          rfRate: 2.5,
        }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="预期收益率（逗号分隔）" name="returns" rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} placeholder="0.06, 0.08, 0.10, 0.12" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="无风险利率" name="rfRate">
                <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="协方差矩阵（行用分号分隔，元素用逗号）" name="cov" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} placeholder="0.04,0.01,...; 0.01,0.09,..." />
          </Form.Item>
          <Button type="primary" icon={<FundOutlined />} loading={loading} onClick={onOptimize}>运行优化</Button>
        </Form>
      </Card>

      {result && !result.error && (
        <Card style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={6}><Statistic title="预期收益" value={result.expected_return * 100} precision={3} suffix="%" /></Col>
            <Col span={6}><Statistic title="波动率" value={result.volatility * 100} precision={3} suffix="%" /></Col>
            <Col span={6}><Statistic title="夏普比率" value={result.sharpe_ratio} precision={4} /></Col>
            <Col span={6}><Statistic title="状态" value={result.status} /></Col>
          </Row>
          <ReactECharts option={chartOption} style={{ height: 300, marginTop: 16 }} />
        </Card>
      )}
    </div>
  )
}

function BlackLittermanPage() {
  const [result, setResult] = useState<any>(null)
  return (
    <div>
      <Title level={3}>📊 Black-Litterman 配置（ALG-009）</Title>
      <Text type="secondary">E(R) = [(τΣ)⁻¹ + PᵀΩ⁻¹P]⁻¹·[(τΣ)⁻¹·Π + PᵀΩ⁻¹·Q]</Text>
      <Card style={{ marginTop: 16 }}>
        <Text>Black-Litterman 模型综合市场均衡与主观观点生成新的预期收益和权重。</Text>
        <Text>实际计算请通过 API 调用 <code>POST /portfolio/black-litterman</code></Text>
      </Card>
    </div>
  )
}

function AllocationsPage() {
  return (
    <DataListPage
      title="资产配置"
      subtitle="按资产类别/保险公司配置比例"
      fetcher={(p) => portfolioApi.allocations(p)}
      columns={[
        { title: '保险公司', dataIndex: 'company_name', width: 140 },
        { title: '配置日', dataIndex: 'allocation_date', width: 120 },
        { title: '资产类别', dataIndex: 'asset_class', width: 140 },
        { title: '权重', dataIndex: 'weight', width: 120,
          render: (v: number) => `${(v * 100).toFixed(2)}%` },
        { title: '基准权重', dataIndex: 'benchmark_weight', width: 120,
          render: (v: number) => `${(v * 100).toFixed(2)}%` },
        { title: '预期收益', dataIndex: 'expected_return', width: 120,
          render: (v: number) => `${(v * 100).toFixed(2)}%` },
      ]}
    />
  )
}

function AttributionsPage() {
  return (
    <DataListPage
      title="Brinson 业绩归因（ALG-012）"
      subtitle="超额收益 = 配置效应 + 选择效应 + 交互效应"
      fetcher={(p) => portfolioApi.attributions(p)}
      columns={[
        { title: '保险公司', dataIndex: 'company_name', width: 140 },
        { title: '归因日', dataIndex: 'attribution_date', width: 120 },
        { title: '资产类别', dataIndex: 'asset_class', width: 140 },
        { title: '配置效应', dataIndex: 'allocation_effect', width: 120,
          render: (v: number) => (
            <span style={{ color: v >= 0 ? '#52c41a' : '#ff4d4f' }}>
              {v > 0 ? '+' : ''}{v?.toFixed(4)}
            </span>
          ) },
        { title: '选择效应', dataIndex: 'selection_effect', width: 120,
          render: (v: number) => (
            <span style={{ color: v >= 0 ? '#52c41a' : '#ff4d4f' }}>
              {v > 0 ? '+' : ''}{v?.toFixed(4)}
            </span>
          ) },
        { title: '交互效应', dataIndex: 'interaction_effect', width: 120,
          render: (v: number) => (
            <span style={{ color: v >= 0 ? '#52c41a' : '#ff4d4f' }}>
              {v > 0 ? '+' : ''}{v?.toFixed(4)}
            </span>
          ) },
        { title: '主动总收益', dataIndex: 'total_active_return', width: 130,
          render: (v: number) => (
            <b style={{ color: v >= 0 ? '#52c41a' : '#ff4d4f' }}>
              {v > 0 ? '+' : ''}{v?.toFixed(4)}
            </b>
          ) },
      ]}
    />
  )
}