/**
 * IALM 5号规则 - 综合成本收益比独立分析
 */
import { useState } from 'react'
import { Card, Form, InputNumber, Select, Button, Row, Col, Statistic, Alert, Typography, Tag, message } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'
import { algorithmsApi } from '../api'

const { Title, Text } = Typography

export default function CostYield() {
  const [form] = Form.useForm()
  const [companyType, setCompanyType] = useState('LIFE')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const threshold = companyType === 'LIFE' ? 1.05 : companyType === 'PROPERTY' ? 1.10 : companyType === 'HEALTH' ? 1.10 : 1.07

  const onAnalyze = async () => {
    setLoading(true)
    try {
      const v = await form.validateFields()
      const r = await algorithmsApi.fullAnalysis({
        company_id: 1,
        company_type: companyType,
        asset_cashflows: [{ period_year: 1, amount: 1000 }],
        liability_cashflows: [{ period_year: 1, amount: 1000 }],
        investment_yield_rate: v.yieldRate / 100,
        liability_cost_rate: v.costRate / 100,
        expense_ratio: v.expenseRate / 100,
        discount_rate: 0.03,
        save_to_db: false,
      })
      setResult(r.data.alg_002_cost_yield)
      message.success('计算完成')
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '计算失败')
    }
    setLoading(false)
  }

  return (
    <div>
      <Title level={3}>📈 综合成本收益比分析</Title>
      <Text type="secondary">5号规则第二铁律：寿险 ≥ 1.05 / 财险 ≥ 1.10 / 健康险 ≥ 1.10 / 再保 ≥ 1.07</Text>

      <Card style={{ marginTop: 16 }}>
        <Form form={form} layout="inline" initialValues={{ yieldRate: 4.5, costRate: 3.5, expenseRate: 1.2 }}>
          <Form.Item label="公司类型" required>
            <Select value={companyType} onChange={setCompanyType} style={{ width: 130 }}
              options={[
                { value: 'LIFE', label: '寿险' },
                { value: 'PROPERTY', label: '财险' },
                { value: 'HEALTH', label: '健康险' },
                { value: 'REINSURANCE', label: '再保险' },
              ]} />
          </Form.Item>
          <Form.Item label="投资收益率" name="yieldRate" rules={[{ required: true }]}>
            <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="负债成本率" name="costRate" rules={[{ required: true }]}>
            <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="费用率" name="expenseRate">
            <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="所得税率">
            <InputNumber min={0} max={50} step={1} addonAfter="%" defaultValue={0} style={{ width: 120 }} />
          </Form.Item>
        </Form>
      </Card>

      <Card style={{ marginTop: 16, textAlign: 'center' }}>
        <Button type="primary" size="large" loading={loading} icon={<PlayCircleOutlined />}
          onClick={onAnalyze}
          style={{ background: 'linear-gradient(135deg, #c2410c 0%, #9a3412 100%)', border: 'none', minWidth: 200 }}>
          计算综合成本收益比
        </Button>
        <div style={{ marginTop: 12 }}>
          <Text type="secondary">当前阈值：</Text>
          <Tag color="orange" style={{ fontSize: 14, padding: '4px 12px' }}>≥ {threshold}</Tag>
        </div>
      </Card>

      {result && (
        <Card style={{ marginTop: 16 }} title={
          <span>分析结果 <Tag color={result.status === 'PASS' ? 'green' : result.status === 'WARN' ? 'orange' : 'red'}>{result.status}</Tag></span>
        }>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic title="综合成本收益比"
                value={result.ratio}
                precision={4}
                valueStyle={{ color: result.status === 'PASS' ? '#52c41a' : '#ff4d4f' }}
              />
              <Text type="secondary">阈值 ≥ {result.threshold}</Text>
            </Col>
            <Col span={6}>
              <Statistic title="净收益率"
                value={result.net_yield * 100}
                precision={3} suffix="%" />
            </Col>
            <Col span={6}>
              <Statistic title="总成本率"
                value={result.total_cost * 100}
                precision={3} suffix="%" />
            </Col>
            <Col span={6}>
              <Statistic title="公司类型"
                value={result.company_type}
              />
            </Col>
          </Row>

          <Alert
            style={{ marginTop: 16 }}
            type={result.status === 'PASS' ? 'success' : result.status === 'WARN' ? 'warning' : 'error'}
            message={`公式: ${result.formula}`}
            description={
              <div>
                <div>• 投资收益率（扣税后）= {(result.net_yield * 100).toFixed(2)}%</div>
                <div>• 总成本 = 负债成本 + 费用率 = {(result.total_cost * 100).toFixed(2)}%</div>
                <div>• 比值 = {(result.net_yield * 100).toFixed(2)}% / {(result.total_cost * 100).toFixed(2)}% = <b>{result.ratio.toFixed(4)}</b></div>
              </div>
            }
          />
        </Card>
      )}
    </div>
  )
}