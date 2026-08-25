/**
 * IALM 5 号规则分析页 - 综合分析
 * 从「资产端管理 + 负债端管理」按时间区间聚合现金流 → 调用算法 → 输出四项指标
 */
import { useState, useEffect } from 'react'
import {
  Card, Form, InputNumber, Select, Button, Space, Row, Col, Alert, Tag, Statistic, message,
  Table, Typography, Divider, Spin,
} from 'antd'
import { PlayCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined, DownloadOutlined } from '@ant-design/icons'
import { algorithmsApi, companiesApi } from '../api'

const { Title, Text } = Typography

interface CashflowRow {
  period_year: number
  amount: number
  holding_count?: number
  policy_count?: number
  record_count?: number
}

export default function MatchAnalysis() {
  const [form] = Form.useForm()
  const [companyType, setCompanyType] = useState('LIFE')
  const [startYear, setStartYear] = useState<number>(0)
  const [endYear, setEndYear] = useState<number>(20)
  const [scenarioCode, setScenarioCode] = useState<string>('BASE')
  const [assetCfs, setAssetCfs] = useState<CashflowRow[]>([])
  const [liabilityCfs, setLiabilityCfs] = useState<CashflowRow[]>([])
  const [aggregateSummary, setAggregateSummary] = useState<any>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [aggregating, setAggregating] = useState(false)
  const [companies, setCompanies] = useState<any[]>([])
  const [companyId, setCompanyId] = useState<number>(1)

  // 加载保险公司列表
  useEffect(() => {
    companiesApi.list({ page: 1, page_size: 100 }).then((r) => {
      const items = r.data.items || []
      setCompanies(items)
      if (items.length > 0 && !items.find((c: any) => c.id === companyId)) {
        setCompanyId(items[0].id)
      }
    }).catch(() => { /* 静默失败，保持默认值 */ })
  }, [])

  const addRow = (type: 'asset' | 'liability') => {
    const arr = type === 'asset' ? [...assetCfs] : [...liabilityCfs]
    const maxY = arr.length > 0 ? Math.max(...arr.map((c) => c.period_year)) : 0
    if (type === 'asset') setAssetCfs([...assetCfs, { period_year: maxY + 1, amount: 0 }])
    else setLiabilityCfs([...liabilityCfs, { period_year: maxY + 1, amount: 0 }])
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

  // 从基础数据按时间区间加载聚合现金流
  const onLoadFromBase = async () => {
    if (startYear >= endYear) {
      message.error('起始年必须小于结束年')
      return
    }
    setAggregating(true)
    try {
      const r = await algorithmsApi.aggregateCashflows({
        company_id: companyId,
        start_year: startYear,
        end_year: endYear,
        scenario_code: scenarioCode,
      })
      const data = r.data
      // 后端返回字段已是 period_year + amount
      const ac: CashflowRow[] = (data.asset_cashflows || []).map((d: any) => ({
        period_year: d.period_year,
        amount: d.amount,
        holding_count: d.holding_count,
        record_count: d.record_count,
      }))
      const lc: CashflowRow[] = (data.liability_cashflows || []).map((d: any) => ({
        period_year: d.period_year,
        amount: d.amount,
        policy_count: d.policy_count,
        record_count: d.record_count,
      }))
      setAssetCfs(ac)
      setLiabilityCfs(lc)
      setAggregateSummary(data.summary)
      message.success(`已加载 ${ac.length} 期资产 + ${lc.length} 期负债现金流`)
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载失败')
    }
    setAggregating(false)
  }

  const onAnalyze = async () => {
    setLoading(true)
    try {
      const values = await form.validateFields()
      const r = await algorithmsApi.fullAnalysis({
        company_id: companyId,
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
    countField: 'holding_count' | 'policy_count',
  ) => (
    <Card
      title={title + ` (${data.length} 期)`}
      size="small"
      style={{ marginBottom: 12 }}
      extra={<Button size="small" onClick={() => addRow(type)}>+ 添加期间</Button>}
    >
      <Table
        size="small"
        dataSource={data.map((d, i) => ({ ...d, idx: i }))}
        rowKey="idx"
        pagination={false}
        scroll={{ y: 320 }}
        columns={[
          {
            title: '期数 (年)',
            dataIndex: 'period_year',
            width: 110,
            render: (v: number, _: any, idx: number) => (
              <InputNumber value={v} min={0} max={80} step={1} onChange={(e) => updateRow(type, idx, 'period_year', e as number)} style={{ width: 90 }} />
            ),
          },
          {
            title: '现金流 (万元)',
            dataIndex: 'amount',
            width: 160,
            render: (v: number, _: any, idx: number) => (
              <InputNumber value={v} step={100} onChange={(e) => updateRow(type, idx, 'amount', e as number)} style={{ width: 140 }} />
            ),
          },
          ...(data.length > 0 && data[0][countField] != null ? [{
            title: type === 'asset' ? '持仓数' : '保单数',
            dataIndex: countField,
            width: 90,
            render: (v: number) => v != null ? <Tag color="blue">{v}</Tag> : '-',
          } as any] : []),
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
      <Title level={3}>� 5 号规则综合分析</Title>
      <Text type="secondary">从资产端管理 + 负债端管理 按时间区间聚合现金流 → 输出四项核心监管指标</Text>

      {/* 时间区间 + 公司选择 + 加载 */}
      <Card style={{ marginTop: 16 }} title="� 数据加载条件">
        <Space wrap size="middle">
          <div>
            <Text type="secondary">保险公司：</Text>
            <Select
              value={companyId}
              onChange={setCompanyId}
              style={{ width: 180 }}
              options={companies.map((c: any) => ({
                value: c.id,
                label: `${c.company_short || c.company_name}（${c.company_code}）`,
              }))}
            />
          </div>
          <div>
            <Text type="secondary">起始年：</Text>
            <InputNumber
              value={startYear}
              min={0}
              max={80}
              step={1}
              onChange={(v) => setStartYear(v as number)}
              addonAfter="年"
              style={{ width: 120 }}
            />
          </div>
          <div>
            <Text type="secondary">结束年：</Text>
            <InputNumber
              value={endYear}
              min={1}
              max={80}
              step={1}
              onChange={(v) => setEndYear(v as number)}
              addonAfter="年"
              style={{ width: 120 }}
            />
          </div>
          <div>
            <Text type="secondary">情景：</Text>
            <Select
              value={scenarioCode}
              onChange={setScenarioCode}
              style={{ width: 130 }}
              options={[
                { value: 'BASE', label: '基准情景' },
                { value: 'UP200', label: '利率上行200bp' },
                { value: 'DOWN200', label: '利率下行200bp' },
                { value: 'STRESS', label: '压力测试' },
              ]}
            />
          </div>
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            loading={aggregating}
            onClick={onLoadFromBase}
            style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}
          >
            从基础数据加载
          </Button>
        </Space>

        {aggregateSummary && (
          <Alert
            style={{ marginTop: 12 }}
            type="info"
            showIcon
            message={
              <Space wrap>
                <Tag color="purple">区间 [{aggregateSummary.start_year}, {aggregateSummary.end_year}] 年</Tag>
                <Tag color="cyan">情景 {aggregateSummary.scenario_code}</Tag>
                <Tag color="green">资产收入合计 {aggregateSummary.asset_total_in.toLocaleString()} 万元</Tag>
                <Tag color="orange">负债支出合计 {aggregateSummary.liability_total_out.toLocaleString()} 万元</Tag>
                <Tag color={aggregateSummary.net >= 0 ? 'green' : 'red'}>
                  净现金流 {aggregateSummary.net >= 0 ? '+' : ''}{aggregateSummary.net.toLocaleString()} 万元
                </Tag>
              </Space>
            }
          />
        )}
      </Card>

      {/* 分析参数 */}
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

      {/* 现金流列表 */}
      <Spin spinning={aggregating} tip="正在聚合基础数据...">
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={12}>{renderCashflowTable('💰 资产端现金流（资产端管理聚合）', 'asset', assetCfs, 'holding_count')}</Col>
          <Col span={12}>{renderCashflowTable('� 负债端现金流（负债端管理聚合）', 'liability', liabilityCfs, 'policy_count')}</Col>
        </Row>
      </Spin>

      <Card style={{ marginTop: 16, textAlign: 'center' }}>
        <Button type="primary" size="large" loading={loading} icon={<PlayCircleOutlined />}
          onClick={onAnalyze}
          disabled={assetCfs.length === 0 || liabilityCfs.length === 0}
          style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none', minWidth: 200 }}
        >
          运行 5 号规则分析
        </Button>
        {(assetCfs.length === 0 || liabilityCfs.length === 0) && (
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">请先点击「从基础数据加载」按时间区间拉取现金流</Text>
          </div>
        )}
      </Card>

      {result && (
        <Card title={`分析结果 - 总体: ${result.overall_status === 'PASS' ? '✅ 通过' : result.overall_status === 'WARN' ? '⚠️ 预警' : '� 不达标'}`} style={{ marginTop: 16 }}>
          <Row gutter={16}>
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
