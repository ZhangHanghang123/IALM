/**
 * IALM 5 号规则分析页
 * 输入资产/负债现金流 + 收益率 + 负债成本 → 调用算法 → 输出四项指标
 */
import { useState } from 'react'
import {
  Card, Form, InputNumber, Select, Button, Space, Row, Col, Alert, Tag, Statistic, message,
  Table, Typography, Divider,
} from 'antd'
import { PlayCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons'
import { algorithmsApi } from '../api'

const { Title, Text } = Typography

interface CashflowRow {
  period_year: number
  amount: number
}

export default function MatchAnalysis() {
  const [form] = Form.useForm()
  const [companyType, setCompanyType] = useState('LIFE')
  const [assetCfs, setAssetCfs] = useState<CashflowRow[]>([
    { period_year: 1, amount: 1000 },
    { period_year: 3, amount: 2000 },
    { period_year: 5, amount: 3000 },
    { period_year: 10, amount: 5000 },
    { period_year: 15, amount: 4000 },
    { period_year: 20, amount: 2000 },
  ])
  const [liabilityCfs, setLiabilityCfs] = useState<CashflowRow[]>([
    { period_year: 1, amount: 1200 },
    { period_year: 3, amount: 1800 },
    { period_year: 5, amount: 2800 },
    { period_year: 10, amount: 5500 },
    { period_year: 15, amount: 4500 },
    { period_year: 20, amount: 1500 },
  ])
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const addRow = (type: 'asset' | 'liability') => {
    const maxY = type === 'asset'
      ? Math.max(0, ...assetCfs.map((c) => c.period_year))
      : Math.max(0, ...liabilityCfs.map((c) => c.period_year))
    const newRow = { period_year: maxY + 5, amount: 1000 }
    if (type === 'asset') setAssetCfs([...assetCfs, newRow])
    else setLiabilityCfs([...liabilityCfs, newRow])
  }

  const updateRow = (type: 'asset' | 'liability', idx: number, key: keyof CashflowRow, value: number) => {
    const arr = type === 'asset' ? [...assetCfs] : [...liabilityCfs]
    arr[idx] = { ...arr[idx], [key]: value }
    if (type === 'asset') setAssetCfs(arr)
    else setLiabilityCfs(arr)
  }

  const removeRow = (type: 'asset' | 'liability', idx: number) => {
    if (type === 'asset') setAssetCfs(assetCfs.filter((_, i) => i !== idx))
    else setLiabilityCfs(liabilityCfs.filter((_, i) => i !== idx))
  }

  const onAnalyze = async () => {
    setLoading(true)
    try {
      const values = await form.validateFields()
      const r = await algorithmsApi.fullAnalysis({
        company_id: 1,
        company_type: companyType,
        asset_cashflows: assetCfs,
        liability_cashflows: liabilityCfs,
        investment_yield_rate: values.yieldRate / 100,
        liability_cost_rate: values.costRate / 100,
        expense_ratio: values.expenseRatio / 100,
        discount_rate: values.discountRate / 100,
        save_to_db: false,
      })
      setResult(r.data)
      message.success('分析完成')
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '分析失败')
    }
    setLoading(false)
  }

  const renderCashflowTable = (
    title: string,
    type: 'asset' | 'liability',
    data: CashflowRow[],
  ) => (
    <Card title={title + ` (${data.length} 期)`} size="small" style={{ marginBottom: 12 }}
      extra={<Button size="small" onClick={() => addRow(type)}>+ 添加期间</Button>}>
      <Table
        size="small"
        dataSource={data.map((d, i) => ({ ...d, idx: i }))}
        rowKey="idx"
        pagination={false}
        columns={[
          {
            title: '期数 (年)',
            dataIndex: 'period_year',
            width: 120,
            render: (v: number, _: any, idx: number) => (
              <InputNumber value={v} min={1} max={50} onChange={(e) => updateRow(type, idx, 'period_year', e as number)} style={{ width: 100 }} />
            ),
          },
          {
            title: '现金流 (万元)',
            dataIndex: 'amount',
            render: (v: number, _: any, idx: number) => (
              <InputNumber value={v} min={0} step={100} onChange={(e) => updateRow(type, idx, 'amount', e as number)} style={{ width: 140 }} />
            ),
          },
          {
            title: '操作',
            width: 80,
            render: (_: any, __: any, idx: number) => (
              <Button danger size="small" onClick={() => removeRow(type, idx)}>删除</Button>
            ),
          },
        ]}
      />
    </Card>
  )

  return (
    <div>
      <Title level={3}>📈 5 号规则三项核心分析</Title>
      <Text type="secondary">输入资产/负债现金流 + 收益率 + 负债成本，输出四项核心监管指标</Text>

      <Card style={{ marginTop: 16 }}>
        <Form form={form} layout="inline" initialValues={{ yieldRate: 4.5, costRate: 3.5, expenseRatio: 1.2, discountRate: 3.0 }}>
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
          <Form.Item label="费用率" name="expenseRatio">
            <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="折现率" name="discountRate">
            <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: 130 }} />
          </Form.Item>
        </Form>
      </Card>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>{renderCashflowTable('💰 资产端现金流', 'asset', assetCfs)}</Col>
        <Col span={12}>{renderCashflowTable('📋 负债端现金流', 'liability', liabilityCfs)}</Col>
      </Row>

      <Card style={{ marginTop: 16, textAlign: 'center' }}>
        <Button type="primary" size="large" loading={loading} icon={<PlayCircleOutlined />}
          onClick={onAnalyze}
          style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none', minWidth: 200 }}
        >
          运行 5 号规则分析
        </Button>
      </Card>

      {result && (
        <Card title={`分析结果 - 总体: ${result.overall_status === 'PASS' ? '✅ 通过' : result.overall_status === 'WARN' ? '⚠️ 预警' : '❌ 不达标'}`} style={{ marginTop: 16 }}>
          <Row gutter={16}>
            {/* ALG-001 */}
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title={<Space>ALG-001 期限匹配率 <Tag color="blue">≥ 0.80</Tag></Space>}
                  value={result.alg_001_duration_match.match_ratio}
                  precision={4}
                  valueStyle={{ color: result.alg_001_duration_match.status === 'PASS' ? '#52c41a' : result.alg_001_duration_match.status === 'WARN' ? '#faad14' : '#ff4d4f' }}
                />
                <Divider style={{ margin: '8px 0' }} />
                {result.alg_001_duration_match.status === 'PASS' ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : result.alg_001_duration_match.status === 'WARN' ? <WarningOutlined style={{ color: '#faad14' }} /> : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                <Text> 状态: {result.alg_001_duration_match.status}</Text>
              </Card>
            </Col>
            {/* ALG-002 */}
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title={<Space>ALG-002 成本收益比 <Tag color="blue">{companyType === 'LIFE' ? '≥1.05' : '≥1.10'}</Tag></Space>}
                  value={result.alg_002_cost_yield.ratio}
                  precision={4}
                  valueStyle={{ color: result.alg_002_cost_yield.status === 'PASS' ? '#52c41a' : result.alg_002_cost_yield.status === 'WARN' ? '#faad14' : '#ff4d4f' }}
                />
                <Divider style={{ margin: '8px 0' }} />
                {result.alg_002_cost_yield.status === 'PASS' ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                <Text> 状态: {result.alg_002_cost_yield.status}</Text>
              </Card>
            </Col>
            {/* ALG-003 */}
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title={<Space>ALG-003 回正期 <Tag color="blue">≤ 5 年</Tag></Space>}
                  value={result.alg_003_cashflow_payback.payback_years ?? '-'}
                  suffix="年"
                  valueStyle={{ color: result.alg_003_cashflow_payback.status === 'PASS' ? '#52c41a' : result.alg_003_cashflow_payback.status === 'WARN' ? '#faad14' : '#ff4d4f' }}
                />
                <Divider style={{ margin: '8px 0' }} />
                {result.alg_003_cashflow_payback.status === 'PASS' ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                <Text> 状态: {result.alg_003_cashflow_payback.status}</Text>
              </Card>
            </Col>
            {/* ALG-004 */}
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title={<Space>ALG-004 久期缺口 <Tag color="blue">[-1,+1]</Tag></Space>}
                  value={result.alg_004_duration_gap.duration_gap}
                  suffix="年"
                  precision={4}
                  valueStyle={{ color: result.alg_004_duration_gap.status === 'PASS' ? '#52c41a' : result.alg_004_duration_gap.status === 'WARN' ? '#faad14' : '#ff4d4f' }}
                />
                <Divider style={{ margin: '8px 0' }} />
                {result.alg_004_duration_gap.status === 'PASS' ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                <Text> 状态: {result.alg_004_duration_gap.status}</Text>
              </Card>
            </Col>
          </Row>

          <Alert
            style={{ marginTop: 16 }}
            type={result.overall_status === 'PASS' ? 'success' : result.overall_status === 'WARN' ? 'warning' : 'error'}
            message={
              result.overall_status === 'PASS'
                ? '✅ 通过银保监会 5 号规则全部四项监管指标'
                : result.overall_status === 'WARN'
                ? '⚠️ 部分指标处于预警状态，需关注'
                : '❌ 不满足 5 号规则监管要求'
            }
            description={
              <div>
                <div>资产久期 {result.alg_004_duration_gap.asset_duration.toFixed(2)} 年 ｜ 负债久期 {result.alg_004_duration_gap.liability_duration.toFixed(2)} 年</div>
                <div>综合成本 = 负债成本 + 费用率 = {(result.alg_002_cost_yield.total_cost * 100).toFixed(2)}%</div>
                <div>回正年份 = {result.alg_003_cashflow_payback.break_even_year ?? '未回正'}</div>
              </div>
            }
          />
        </Card>
      )}
    </div>
  )
}