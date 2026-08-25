/**
 * IALM 5号规则 - 现金流回正期独立分析
 */
import { useState } from 'react'
import { Card, Form, InputNumber, Button, Row, Col, Statistic, Alert, Typography, Tag, message, Table, Select } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'
import { algorithmsApi } from '../api'

const { Title, Text } = Typography

interface NetCashflow {
  year: number
  net: number
}

export default function CashflowPayback() {
  const [form] = Form.useForm()
  const [annualNet, setAnnualNet] = useState<NetCashflow[]>([
    { year: 2025, net: -1500 },
    { year: 2026, net: 300 },
    { year: 2027, net: 400 },
    { year: 2028, net: 500 },
    { year: 2029, net: 600 },
    { year: 2030, net: 700 },
    { year: 2031, net: 800 },
    { year: 2032, net: 900 },
  ])
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const update = (idx: number, key: keyof NetCashflow, value: number) => {
    const arr = [...annualNet]
    arr[idx] = { ...arr[idx], [key]: value }
    setAnnualNet(arr)
  }
  const add = () => {
    const maxY = Math.max(0, ...annualNet.map(d => d.year))
    setAnnualNet([...annualNet, { year: maxY + 1, net: 0 }])
  }
  const remove = (idx: number) => setAnnualNet(annualNet.filter((_, i) => i !== idx))

  // 计算累计（前端预览）
  const cumulative = (() => {
    let cum = 0
    return annualNet.map(d => { cum += d.net; return { ...d, cum } })
  })()

  const onAnalyze = async () => {
    setLoading(true)
    try {
      const v = await form.validateFields()
      // 这里调用专门的回正期 API，但目前算法集成在 full-analysis 里
      // 用一个简化模拟：传入相同现金流 + 收益率
      const r = await algorithmsApi.fullAnalysis({
        company_id: 1,
        company_type: 'LIFE',
        asset_cashflows: annualNet.map(d => ({ period_year: d.year - 2024, amount: Math.max(d.net, 0) })),
        liability_cashflows: annualNet.map(d => ({ period_year: d.year - 2024, amount: Math.max(-d.net, 0) })),
        investment_yield_rate: v.yieldRate / 100,
        liability_cost_rate: v.costRate / 100,
        expense_ratio: 0.012,
        discount_rate: 0.03,
        save_to_db: false,
      })
      setResult(r.data.alg_003_cashflow_payback)
      message.success('计算完成')
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '计算失败')
    }
    setLoading(false)
  }

  return (
    <div>
      <Title level={3}>⏱️ 现金流回正期分析</Title>
      <Text type="secondary">5号规则第三铁律：累计净现金流首次 ≥ 0 的年份 ≤ 5 年</Text>

      <Card style={{ marginTop: 16 }}>
        <Form form={form} layout="inline" initialValues={{ yieldRate: 4.5, costRate: 3.5 }}>
          <Form.Item label="投资收益率" name="yieldRate">
            <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="负债成本" name="costRate">
            <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="阈值">
            <Select defaultValue="5" style={{ width: 100 }}
              options={[{ value: '5', label: '5 年' }, { value: '7', label: '7 年' }, { value: '10', label: '10 年' }]} />
          </Form.Item>
        </Form>
      </Card>

      <Card style={{ marginTop: 16 }} title="📈 每年净现金流（资产收入 − 负债支出）" size="small">
        <Table
          size="small"
          dataSource={annualNet.map((d, i) => ({ ...d, idx: i, cum: cumulative[i].cum }))}
          rowKey="idx"
          pagination={false}
          columns={[
            { title: '年', dataIndex: 'year', width: 100,
              render: (v: number, _: any, idx: number) => (
                <InputNumber value={v} min={2000} max={2100} onChange={(e) => update(idx, 'year', e as number)} style={{ width: 90 }} />
              ) },
            { title: '净现金流(万)', dataIndex: 'net',
              render: (v: number, _: any, idx: number) => (
                <InputNumber value={v} step={100} onChange={(e) => update(idx, 'net', e as number)} style={{ width: 130 }} />
              ) },
            { title: '累计', dataIndex: 'cum',
              render: (v: number) => (
                <span style={{ color: v >= 0 ? '#52c41a' : '#ff4d4f', fontWeight: 600 }}>
                  {v?.toFixed(2)}
                </span>
              ) },
            { title: '操作', width: 80,
              render: (_: any, __: any, idx: number) => (
                <Button danger size="small" onClick={() => remove(idx)}>删</Button>
              ) },
          ]}
        />
        <Button onClick={add} size="small" style={{ marginTop: 8 }}>+ 添加年份</Button>
      </Card>

      <Card style={{ marginTop: 16, textAlign: 'center' }}>
        <Button type="primary" size="large" loading={loading} icon={<PlayCircleOutlined />}
          onClick={onAnalyze}
          style={{ background: 'linear-gradient(135deg, #c2410c 0%, #9a3412 100%)', border: 'none', minWidth: 200 }}>
          计算回正期
        </Button>
      </Card>

      {result && (
        <Card style={{ marginTop: 16 }} title={
          <span>分析结果 <Tag color={result.status === 'PASS' ? 'green' : result.status === 'WARN' ? 'orange' : 'red'}>{result.status}</Tag></span>
        }>
          <Row gutter={16}>
            <Col span={8}>
              <Statistic title="回正期"
                value={result.payback_years ?? 'N/A'}
                suffix={result.payback_years != null ? '年' : ''}
                valueStyle={{ color: result.status === 'PASS' ? '#52c41a' : '#ff4d4f' }}
              />
              <Text type="secondary">阈值 ≤ {result.threshold} 年</Text>
            </Col>
            <Col span={8}>
              <Statistic title="回正年份"
                value={result.break_even_year ?? '未回正'}
              />
            </Col>
            <Col span={8}>
              <Statistic title="预测期"
                value={result.total_horizon}
                suffix="年"
              />
            </Col>
          </Row>

          <Alert
            style={{ marginTop: 16 }}
            type={result.status === 'PASS' ? 'success' : result.status === 'WARN' ? 'warning' : 'error'}
            message={`公式: ${result.formula}`}
            description={
              <div>
                <div>• 累计净现金流 = 每年净现金流之和</div>
                <div>• 跨越 0 的时点 = 上一年累计 + (|上一年累计| / 当年增量) × (当年 - 上一年)</div>
                <div>• 回正期 = 跨越点距起始年的时长</div>
              </div>
            }
          />
        </Card>
      )}
    </div>
  )
}