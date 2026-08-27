/**
 * IALM 5号规则 - 综合成本收益比独立分析
 * 从「资产端管理 + 负债端管理」按时间区间聚合 → 显示规模参考 → 用户输入率 → ALG-002
 */
import { useState, useEffect } from 'react'
import { Card, Form, InputNumber, Select, Button, Row, Col, Statistic, Alert, Typography, Tag, message, Table, Space, Spin } from 'antd'
import { PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons'
import { algorithmsApi, companiesApi } from '../api'

const { Title, Text } = Typography

interface CashflowRow {
  period_year: number
  amount: number
  holding_count?: number
  policy_count?: number
}

export default function CostYield() {
  const [form] = Form.useForm()
  const [companyType, setCompanyType] = useState('LIFE')
  const [companyId, setCompanyId] = useState<number>(1)
  const [companies, setCompanies] = useState<any[]>([])
  const [startYear, setStartYear] = useState<number>(0)
  const [endYear, setEndYear] = useState<number>(20)
  const [scenarioCode, setScenarioCode] = useState<string>('BASE')
  const [assetCfs, setAssetCfs] = useState<CashflowRow[]>([])
  const [liabilityCfs, setLiabilityCfs] = useState<CashflowRow[]>([])
  const [aggregateSummary, setAggregateSummary] = useState<any>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [aggregating, setAggregating] = useState(false)

  const threshold = companyType === 'LIFE' ? 1.05 : companyType === 'PROPERTY' ? 1.10 : companyType === 'HEALTH' ? 1.10 : 1.07

  // 加载保险公司列表
  useEffect(() => {
    companiesApi.list({ page: 1, page_size: 100 }).then((r) => {
      const items = r.data.items || []
      setCompanies(items)
      if (items.length > 0 && !items.find((c: any) => c.id === companyId)) {
        setCompanyId(items[0].id)
      }
    }).catch(() => { /* 静默失败 */ })
  }, [])

  // 从基础数据按时间区间加载聚合现金流（仅作信息展示，不参与 ALG-002 计算）
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
      const ac: CashflowRow[] = (data.asset_cashflows || []).map((d: any) => ({
        period_year: d.period_year,
        amount: d.amount,
        holding_count: d.holding_count,
      }))
      const lc: CashflowRow[] = (data.liability_cashflows || []).map((d: any) => ({
        period_year: d.period_year,
        amount: d.amount,
        policy_count: d.policy_count,
      }))
      setAssetCfs(ac)
      setLiabilityCfs(lc)
      setAggregateSummary(data.summary)
      message.success(`已加载 ${ac.length} 期资产 + ${lc.length} 期负债现金流（规模参考）`)
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载失败')
    }
    setAggregating(false)
  }

  const onAnalyze = async () => {
    setLoading(true)
    try {
      const v = await form.validateFields()
      const r = await algorithmsApi.fullAnalysis({
        company_id: companyId,
        company_type: companyType,
        // ALG-002 主要使用收益率/成本率/费用率；这里传聚合数据作 placeholder
        asset_cashflows: assetCfs.length > 0 ? assetCfs : [{ period_year: 1, amount: 1000 }],
        liability_cashflows: liabilityCfs.length > 0 ? liabilityCfs : [{ period_year: 1, amount: 1000 }],
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
      <Text type="secondary">5号规则第二铁律：寿险 ≥ 1.05 / 财险 ≥ 1.10 / 健康险 ≥ 1.10 / 再保 ≥ 1.07 ｜ 现金流规模参考</Text>

      {/* 数据加载条件 */}
      <Card style={{ marginTop: 16 }} title="🗂️ 数据加载条件（规模参考）">
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

      {/* 现金流规模参考表 */}
      {(assetCfs.length > 0 || liabilityCfs.length > 0) && (
        <Card style={{ marginTop: 16 }} title="💰 现金流规模参考" size="small">
          <Spin spinning={aggregating} tip="正在聚合基础数据...">
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>资产端 ({assetCfs.length} 期)</Text>
                <Table
                  size="small"
                  style={{ marginTop: 8 }}
                  dataSource={assetCfs.slice(0, 20)}
                  rowKey="period_year"
                  pagination={false}
                  scroll={{ y: 240 }}
                  columns={[
                    { title: '年', dataIndex: 'period_year', width: 70 },
                    { title: '金额(万)', dataIndex: 'amount', render: (v: number) => v.toLocaleString() },
                    { title: '持仓数', dataIndex: 'holding_count', width: 80,
                      render: (v: number) => v != null ? <Tag color="blue">{v}</Tag> : '-' },
                  ]}
                />
              </Col>
              <Col span={12}>
                <Text strong>负债端 ({liabilityCfs.length} 期)</Text>
                <Table
                  size="small"
                  style={{ marginTop: 8 }}
                  dataSource={liabilityCfs.slice(0, 20)}
                  rowKey="period_year"
                  pagination={false}
                  scroll={{ y: 240 }}
                  columns={[
                    { title: '年', dataIndex: 'period_year', width: 70 },
                    { title: '金额(万)', dataIndex: 'amount', render: (v: number) => v.toLocaleString() },
                    { title: '保单数', dataIndex: 'policy_count', width: 80,
                      render: (v: number) => v != null ? <Tag color="blue">{v}</Tag> : '-' },
                  ]}
                />
              </Col>
            </Row>
          </Spin>
        </Card>
      )}

      {/* 分析参数 */}
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
                valueStyle={{ color: result.status === 'PASS' ? '#52c41a' : result.status === 'WARN' ? '#faad14' : '#ff4d4f' }}
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