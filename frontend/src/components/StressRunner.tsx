/**
 * IALM 压力测试运行器（多因子冲击模拟）
 * 参数从基础数据自动聚合 + 用户可微调
 */
import { useState, useEffect } from 'react'
import { Card, Form, InputNumber, Select, Button, Row, Col, Statistic, Typography, Alert, Table, message, Space, Tag } from 'antd'
import { ThunderboltOutlined, ReloadOutlined, DatabaseOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { stressApi, companiesApi } from '../api'

const { Title, Text } = Typography

export default function StressRunner() {
  const [form] = Form.useForm()
  const [scenarios, setScenarios] = useState<any[]>([])
  const [companies, setCompanies] = useState<any[]>([])
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [paramSummary, setParamSummary] = useState<any>(null)
  const [paramLoading, setParamLoading] = useState(false)

  // 初始加载：拉情景 + 公司
  useEffect(() => {
    stressApi.scenarios({ page: 1, page_size: 50 }).then(r => setScenarios(r.data.items || []))
    companiesApi.list({ page: 1, page_size: 100 }).then(r => {
      const items = r.data.items || []
      setCompanies(items)
      // 如果当前 form 没公司且列表有数据，自动选第一家并加载参数
      const currentCompany = form.getFieldValue('company_id')
      if (!currentCompany && items.length > 0) {
        form.setFieldValue('company_id', items[0].id)
        loadBaseParams(items[0].id)
      }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 从基础数据加载参数
  const loadBaseParams = async (companyId: number) => {
    if (!companyId) return
    setParamLoading(true)
    try {
      const r = await stressApi.baseParameters({ company_id: companyId })
      const p = r.data
      setParamSummary(p)
      // 把后端聚合的参数填入表单
      form.setFieldsValue({
        assetValue: p.asset_value,
        liabilityValue: p.liability_value,
        assetDuration: p.asset_duration,
        liabilityDuration: p.liability_duration,
        baseScr: p.base_scr,
      })
      message.success(`已加载 ${p.company_short} 的基础参数（${p.summary.asset_holding_count} 个持仓）`)
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载基础参数失败')
    }
    setParamLoading(false)
  }

  const onCompanyChange = (companyId: number) => {
    // 切换公司时自动重新加载参数
    loadBaseParams(companyId)
  }

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

  // 准备 Reserve 分布表的列
  const reserveColumns = [
    { title: '准备金类型', dataIndex: 'type', width: 150 },
    { title: '金额(万)', dataIndex: 'amount', width: 160,
      render: (v: number) => v?.toLocaleString(undefined, { maximumFractionDigits: 2 }) },
    { title: '记录数', dataIndex: 'count', width: 80 },
  ]

  return (
    <div>
      <Title level={3}>⚡ 压力测试运行器</Title>
      <Text type="secondary">基于久期缺口的多因子冲击传导（ALG-007）· 参数自动从基础数据聚合</Text>

      {/* 数据加载条件卡片 */}
      <Card
        style={{ marginTop: 16 }}
        title={<><DatabaseOutlined /> 数据加载条件</>}
        size="small"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} loading={paramLoading} onClick={() => loadBaseParams(form.getFieldValue('company_id'))}>
              重新加载参数
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="inline" initialValues={{ company_id: 1, scenario_id: 1 }}>
          <Form.Item label="公司" name="company_id">
            <Select style={{ width: 180 }}
              onChange={onCompanyChange}
              options={companies.map(c => ({ value: c.id, label: c.company_short || c.company_name }))} />
          </Form.Item>
          <Form.Item label="情景" name="scenario_id">
            <Select style={{ width: 220 }}
              options={scenarios.map(s => ({ value: s.id, label: `${s.scenario_name} (${s.source === 'REGULATORY' ? '监管' : '自定义'})` }))} />
          </Form.Item>
        </Form>

        {paramSummary && (
          <Alert
            style={{ marginTop: 12 }}
            type="info"
            showIcon
            message={
              <Space wrap>
                <Tag color="blue">公司：{paramSummary.company_short}</Tag>
                <Tag color="green">资产规模 {paramSummary.asset_value.toLocaleString()} 万</Tag>
                <Tag color="orange">负债规模 {paramSummary.liability_value.toLocaleString()} 万</Tag>
                <Tag color="purple">基础 SCR {paramSummary.base_scr.toLocaleString()} 万</Tag>
                <Tag>折现率 {(paramSummary.discount_rate * 100).toFixed(2)}%</Tag>
                <Tag>SCR 比率 {paramSummary.summary.scr_ratio_used * 100}%</Tag>
              </Space>
            }
            description={
              <div>
                <Space size="middle" wrap style={{ marginBottom: 8 }}>
                  <Text>资产持仓数：<b>{paramSummary.summary.asset_holding_count}</b></Text>
                  <Text>准备金类型数：<b>{paramSummary.summary.reserve_by_type.length}</b></Text>
                  <Text>资产加权久期：<b>{paramSummary.asset_duration.toFixed(2)}</b> 年</Text>
                  <Text>负债估算久期：<b>{paramSummary.liability_duration.toFixed(2)}</b> 年</Text>
                </Space>
                {paramSummary.summary.reserve_by_type.length > 0 && (
                  <Table
                    size="small"
                    dataSource={paramSummary.summary.reserve_by_type}
                    columns={reserveColumns}
                    rowKey="type"
                    pagination={false}
                    style={{ marginTop: 8 }}
                  />
                )}
              </div>
            }
          />
        )}
      </Card>

      {/* 参数输入卡片（用户可微调） */}
      <Card style={{ marginTop: 16 }} title="运行参数（已从基础数据加载，可微调）" size="small">
        <Form form={form} layout="inline">
          <Form.Item label="资产规模(万)" name="assetValue">
            <InputNumber min={0} step={10000} style={{ width: 140 }} />
          </Form.Item>
          <Form.Item label="负债规模(万)" name="liabilityValue">
            <InputNumber min={0} step={10000} style={{ width: 140 }} />
          </Form.Item>
          <Form.Item label="资产久期(年)" name="assetDuration">
            <InputNumber min={0} max={30} step={0.1} style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="负债久期(年)" name="liabilityDuration">
            <InputNumber min={0} max={30} step={0.1} style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="基础 SCR(万)" name="baseScr">
            <InputNumber min={0} step={1000} style={{ width: 140 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<ThunderboltOutlined />} loading={loading} onClick={onRun}>
              运行模拟
            </Button>
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