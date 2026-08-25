/**
 * IALM 5号规则 - 期限匹配率独立分析
 */
import { useState } from 'react'
import { Card, Form, InputNumber, Select, Button, Row, Col, Statistic, Alert, Typography, Tag, message, Table } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'
import { algorithmsApi } from '../api'

const { Title, Text } = Typography

interface CashflowRow {
  period_year: number
  amount: number
}

export default function DurationMatch() {
  const [form] = Form.useForm()
  const [bucketYears, setBucketYears] = useState(5)
  const [assetCfs, setAssetCfs] = useState<CashflowRow[]>([
    { period_year: 1, amount: 1000 },
    { period_year: 3, amount: 2000 },
    { period_year: 5, amount: 3000 },
    { period_year: 10, amount: 5000 },
    { period_year: 15, amount: 3000 },
    { period_year: 20, amount: 1000 },
  ])
  const [liabilityCfs, setLiabilityCfs] = useState<CashflowRow[]>([
    { period_year: 1, amount: 1200 },
    { period_year: 3, amount: 1800 },
    { period_year: 5, amount: 2800 },
    { period_year: 10, amount: 5500 },
    { period_year: 15, amount: 3500 },
    { period_year: 20, amount: 800 },
  ])
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const onAnalyze = async () => {
    setLoading(true)
    try {
      const values = await form.validateFields()
      const r = await algorithmsApi.fullAnalysis({
        company_id: 1,
        company_type: 'LIFE',
        asset_cashflows: assetCfs,
        liability_cashflows: liabilityCfs,
        investment_yield_rate: values.yieldRate / 100,
        liability_cost_rate: values.costRate / 100,
        expense_ratio: 0.012,
        discount_rate: 0.03,
        save_to_db: false,
      })
      setResult(r.data)
      message.success('分析完成')
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '分析失败')
    }
    setLoading(false)
  }

  return (
    <div>
      <Title level={3}>📊 期限结构匹配率分析</Title>
      <Text type="secondary">5号规则第一铁律：期限结构匹配率 ≥ 0.80</Text>

      <Card style={{ marginTop: 16 }}>
        <Form form={form} layout="inline" initialValues={{ yieldRate: 4.5, costRate: 3.5 }}>
          <Form.Item label="投资收益率" name="yieldRate" rules={[{ required: true }]}>
            <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="负债成本" name="costRate" rules={[{ required: true }]}>
            <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="时间桶宽度(年)">
            <Select value={bucketYears} onChange={setBucketYears} style={{ width: 130 }}
              options={[1, 3, 5, 10].map(v => ({ value: v, label: `${v} 年` }))} />
          </Form.Item>
        </Form>
      </Card>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="💰 资产端现金流" size="small">
            <CashflowTable data={assetCfs} onChange={setAssetCfs} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="📋 负债端现金流" size="small">
            <CashflowTable data={liabilityCfs} onChange={setLiabilityCfs} />
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: 16, textAlign: 'center' }}>
        <Button type="primary" size="large" loading={loading} icon={<PlayCircleOutlined />}
          onClick={onAnalyze}
          style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none', minWidth: 200 }}>
          计算期限匹配率
        </Button>
      </Card>

      {result && result.alg_001_duration_match && (
        <Card style={{ marginTop: 16 }} title={
          <Space>
            <span>分析结果</span>
            <Tag color={result.alg_001_duration_match.status === 'PASS' ? 'green' : result.alg_001_duration_match.status === 'WARN' ? 'orange' : 'red'}>
              {result.alg_001_duration_match.status}
            </Tag>
          </Space>
        }>
          <Row gutter={16}>
            <Col span={8}>
              <Statistic title="期限匹配率"
                value={result.alg_001_duration_match.match_ratio}
                precision={4}
                valueStyle={{ color: result.alg_001_duration_match.status === 'PASS' ? '#52c41a' : '#ff4d4f' }}
              />
              <Text type="secondary">阈值 ≥ 0.80</Text>
            </Col>
            <Col span={8}>
              <Statistic title="资产总额(万)"
                value={result.alg_001_duration_match.asset_total}
                precision={2} />
            </Col>
            <Col span={8}>
              <Statistic title="负债总额(万)"
                value={result.alg_001_duration_match.liability_total}
                precision={2} />
            </Col>
          </Row>

          <Alert
            style={{ marginTop: 16 }}
            type={result.alg_001_duration_match.status === 'PASS' ? 'success' : 'warning'}
            message={`公式: ${result.alg_001_duration_match.formula}`}
            description={
              <Table
                size="small"
                dataSource={result.alg_001_duration_match.asset_distribution.map((_: any, i: number) => ({
                  idx: i,
                  bucket: `${i * bucketYears + 1}-${(i + 1) * bucketYears}年`,
                  asset_pct: result.alg_001_duration_match.asset_distribution[i],
                  liability_pct: result.alg_001_duration_match.liability_distribution[i],
                }))}
                pagination={false}
                columns={[
                  { title: '桶', dataIndex: 'bucket', width: 120 },
                  { title: '资产占比', dataIndex: 'asset_pct', render: (v: number) => `${(v * 100).toFixed(2)}%` },
                  { title: '负债占比', dataIndex: 'liability_pct', render: (v: number) => `${(v * 100).toFixed(2)}%` },
                  { title: '差异', key: 'diff', render: (_: any, r: any) => `${((r.asset_pct - r.liability_pct) * 100).toFixed(2)}%` },
                ]}
              />
            }
          />
        </Card>
      )}
    </div>
  )
}

function CashflowTable({ data, onChange }: { data: CashflowRow[]; onChange: (d: CashflowRow[]) => void }) {
  const update = (idx: number, key: keyof CashflowRow, value: number) => {
    const arr = [...data]
    arr[idx] = { ...arr[idx], [key]: value }
    onChange(arr)
  }
  const add = () => {
    const maxY = Math.max(0, ...data.map(d => d.period_year))
    onChange([...data, { period_year: maxY + 5, amount: 1000 }])
  }
  const remove = (idx: number) => onChange(data.filter((_, i) => i !== idx))

  return (
    <>
      <Table
        size="small"
        dataSource={data.map((d, i) => ({ ...d, idx: i }))}
        rowKey="idx"
        pagination={false}
        columns={[
          { title: '期数 (年)', dataIndex: 'period_year', width: 100,
            render: (v: number, _: any, idx: number) => (
              <InputNumber value={v} min={1} max={50} onChange={(e) => update(idx, 'period_year', e as number)} style={{ width: 80 }} />
            ) },
          { title: '金额(万)', dataIndex: 'amount',
            render: (v: number, _: any, idx: number) => (
              <InputNumber value={v} min={0} step={100} onChange={(e) => update(idx, 'amount', e as number)} style={{ width: 120 }} />
            ) },
          { title: '操作', width: 80,
            render: (_: any, __: any, idx: number) => (
              <Button danger size="small" onClick={() => remove(idx)}>删</Button>
            ) },
        ]}
      />
      <Button onClick={add} size="small" style={{ marginTop: 8 }}>+ 添加期间</Button>
    </>
  )
}