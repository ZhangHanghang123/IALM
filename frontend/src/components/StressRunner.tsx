/**
 * IALM 压力测试运行器（多因子冲击模拟）
 */
import { useState, useEffect } from 'react'
import { Card, Form, InputNumber, Select, Button, Row, Col, Statistic, Typography, Alert, Table, message } from 'antd'
import { ThunderboltOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { stressApi, companiesApi } from '../api'

const { Title, Text } = Typography

export default function StressRunner() {
  const [form] = Form.useForm()
  const [scenarios, setScenarios] = useState<any[]>([])
  const [companies, setCompanies] = useState<any[]>([])
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    stressApi.scenarios({ page: 1, page_size: 50 }).then(r => setScenarios(r.data.items || []))
    companiesApi.list({ page: 1, page_size: 100 }).then(r => setCompanies(r.data.items || []))
  }, [])

  const onRun = async () => {
    const v = await form.validateFields()
    setLoading(true)
    try {
      const r = await stressApi.run({
        company_id: v.company_id,
        scenario_id: v.scenario_id,
        asset_value: v.assetValue,
        liability_value: v.liabilityValue,
        asset_duration: v.assetDuration,
        liability_duration: v.liabilityDuration,
        base_scr: v.baseScr,
      })
      setResult(r.data)
      message.success('模拟完成')
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '运行失败')
    }
    setLoading(false)
  }

  const chartOption = result && {
    title: { text: '多因子冲击传导分析', left: 'center' },
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 30, top: 50, bottom: 60 },
    xAxis: { type: 'category', data: result.detail.map((d: any) => `${d.factor}(${d.value})`) },
    yAxis: { type: 'value', name: '影响金额(万)' },
    series: [{
      type: 'bar',
      data: result.detail.map((d: any) => d.impact),
      itemStyle: { color: (params: any) => params.value >= 0 ? '#52c41a' : '#ff4d4f' },
    }],
  }

  return (
    <div>
      <Title level={3}>⚡ 压力测试运行器</Title>
      <Text type="secondary">基于久期缺口的多因子冲击传导（ALG-007）</Text>

      <Card style={{ marginTop: 16 }}>
        <Form form={form} layout="inline" initialValues={{ company_id: 1, scenario_id: 1, assetValue: 500000, liabilityValue: 450000, assetDuration: 7.5, liabilityDuration: 8.5, baseScr: 50000 }}>
          <Form.Item label="公司" name="company_id">
            <Select style={{ width: 180 }}
              options={companies.map(c => ({ value: c.id, label: c.company_short || c.company_name }))} />
          </Form.Item>
          <Form.Item label="情景" name="scenario_id">
            <Select style={{ width: 200 }}
              options={scenarios.map(s => ({ value: s.id, label: s.scenario_name }))} />
          </Form.Item>
          <Form.Item label="资产规模(万)" name="assetValue">
            <InputNumber min={0} step={10000} style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="负债规模(万)" name="liabilityValue">
            <InputNumber min={0} step={10000} style={{ width: 130 }} />
          </Form.Item>
        </Form>
        <Form form={form} layout="inline" style={{ marginTop: 12 }}>
          <Form.Item label="资产久期(年)" name="assetDuration">
            <InputNumber min={0} max={30} step={0.1} style={{ width: 120 }} />
          </Form.Item>
          <Form.Item label="负债久期(年)" name="liabilityDuration">
            <InputNumber min={0} max={30} step={0.1} style={{ width: 120 }} />
          </Form.Item>
          <Form.Item label="基础 SCR(万)" name="baseScr">
            <InputNumber min={0} step={1000} style={{ width: 130 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<ThunderboltOutlined />} loading={loading} onClick={onRun}>运行</Button>
          </Form.Item>
        </Form>
      </Card>

      {result && !result.error && (
        <Card style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={6}><Statistic title="基准 NAV(万)" value={result.base_net_value} /></Col>
            <Col span={6}><Statistic title="NAV 变化(万)" value={result.nav_change} valueStyle={{ color: result.nav_change >= 0 ? '#52c41a' : '#ff4d4f' }} /></Col>
            <Col span={6}><Statistic title="压力后 NAV" value={result.new_net_value} /></Col>
            <Col span={6}><Statistic title="SCR 变化" value={result.scr_change_pct} suffix="%" valueStyle={{ color: result.passed ? '#52c41a' : '#ff4d4f' }} /></Col>
          </Row>

          <Alert
            style={{ marginTop: 16 }}
            type={result.passed ? 'success' : 'error'}
            message={`情景: ${result.scenario_name}`}
            description={
              <Table
                size="small"
                dataSource={result.detail}
                pagination={false}
                columns={[
                  { title: '因子', dataIndex: 'factor' },
                  { title: '冲击值', dataIndex: 'value' },
                  { title: '单位', dataIndex: 'unit' },
                  { title: '影响金额(万)', dataIndex: 'impact',
                    render: (v: number) => (
                      <span style={{ color: v >= 0 ? '#52c41a' : '#ff4d4f' }}>
                        {v > 0 ? '+' : ''}{v?.toFixed(2)}
                      </span>
                    ) },
                ]}
              />
            }
          />

          <Card title="冲击传导可视化" style={{ marginTop: 16 }}>
            <ReactECharts option={chartOption} style={{ height: 280 }} />
          </Card>
        </Card>
      )}
    </div>
  )
}