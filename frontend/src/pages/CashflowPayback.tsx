/**
 * IALM 5号规则 - 现金流回正期独立分析
 * 从「资产端管理 + 负债端管理」按时间区间聚合 → 资产收入-负债支出 = 每年净现金流 → ALG-003
 */
import { useState, useEffect } from 'react'
import { Card, Form, InputNumber, Button, Row, Col, Statistic, Alert, Typography, Tag, message, Table, Select, Space, Spin } from 'antd'
import { PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons'
import { algorithmsApi, companiesApi } from '../api'

const { Title, Text } = Typography

interface NetCashflow {
  year: number
  net: number
  asset_amount?: number
  liability_amount?: number
}

export default function CashflowPayback() {
  const [form] = Form.useForm()
  const [companyId, setCompanyId] = useState<number>(1)
  const [companies, setCompanies] = useState<any[]>([])
  const [startYear, setStartYear] = useState<number>(0)
  const [endYear, setEndYear] = useState<number>(10)
  const [scenarioCode, setScenarioCode] = useState<string>('BASE')
  const [annualNet, setAnnualNet] = useState<NetCashflow[]>([])
  const [aggregateSummary, setAggregateSummary] = useState<any>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [aggregating, setAggregating] = useState(false)
  const [threshold, setThreshold] = useState<number>(5)

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

  const update = (idx: number, key: keyof NetCashflow, value: number) => {
    const arr = [...annualNet]
    const row = { ...arr[idx], [key]: value }
    // 当资产收入或负债支出变化时，自动重算净现金流
    if (key === 'asset_amount' || key === 'liability_amount') {
      row.net = (row.asset_amount ?? 0) - (row.liability_amount ?? 0)
    }
    arr[idx] = row
    setAnnualNet(arr)
  }
  const add = () => {
    const maxY = annualNet.length > 0 ? Math.max(...annualNet.map(d => d.year)) : 0
    setAnnualNet([...annualNet, { year: maxY + 1, net: 0, asset_amount: 0, liability_amount: 0 }])
  }
  const remove = (idx: number) => setAnnualNet(annualNet.filter((_, i) => i !== idx))

  // 计算累计（前端预览）
  const cumulative = (() => {
    let cum = 0
    return annualNet.map(d => { cum += d.net; return { ...d, cum } })
  })()

  // 从基础数据按时间区间加载：资产收入-负债支出=每年净现金流
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
      // 把资产和负债按年合并 → 净现金流 = 资产收入 - 负债支出
      const assetMap = new Map<number, number>()
      const liabMap = new Map<number, number>()
      for (const a of (data.asset_cashflows || [])) {
        assetMap.set(a.period_year, (assetMap.get(a.period_year) || 0) + a.amount)
      }
      for (const l of (data.liability_cashflows || [])) {
        liabMap.set(l.period_year, (liabMap.get(l.period_year) || 0) + l.amount)
      }
      const years = new Set<number>([...assetMap.keys(), ...liabMap.keys()])
      const merged: NetCashflow[] = [...years].sort((a, b) => a - b).map(y => {
        const asset = assetMap.get(y) || 0
        const liab = liabMap.get(y) || 0
        return {
          year: y,
          net: asset - liab,               // 净现金流 = 资产收入 - 负债支出（万元）
          asset_amount: asset,
          liability_amount: liab,
        }
      })
      setAnnualNet(merged)
      setAggregateSummary(data.summary)
      message.success(`已加载 ${merged.length} 年净现金流`)
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载失败')
    }
    setAggregating(false)
  }

  const onAnalyze = async () => {
    setLoading(true)
    try {
      const v = await form.validateFields()
      // 把净现金流拆成资产/负债两条调用 fullAnalysis（净 = 资产收入 - 负债支出）
      const r = await algorithmsApi.fullAnalysis({
        company_id: companyId,
        company_type: 'LIFE',
        asset_cashflows: annualNet.map(d => ({ period_year: d.year, amount: Math.max(d.net, 0) })),
        liability_cashflows: annualNet.map(d => ({ period_year: d.year, amount: Math.max(-d.net, 0) })),
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
      <Text type="secondary">5号规则第三铁律：累计净现金流首次 ≥ 0 的年份 ≤ 阈值 ｜ 从基础数据按时间区间聚合</Text>

      {/* 数据加载条件 */}
      <Card style={{ marginTop: 16 }} title="🗂️ 数据加载条件">
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
        <Form form={form} layout="inline" initialValues={{ yieldRate: 4.5, costRate: 3.5 }}>
          <Form.Item label="投资收益率" name="yieldRate">
            <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="负债成本" name="costRate">
            <InputNumber min={0} max={20} step={0.1} addonAfter="%" style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="阈值">
            <Select value={threshold} onChange={setThreshold} style={{ width: 100 }}
              options={[{ value: 5, label: '5 年' }, { value: 7, label: '7 年' }, { value: 10, label: '10 年' }]} />
          </Form.Item>
        </Form>
      </Card>

      {/* 净现金流表 */}
      <Card style={{ marginTop: 16 }} title="📈 每年净现金流（净现金流 = 资产收入 − 负债支出，由基础数据聚合得出）" size="small"
        extra={<Button size="small" onClick={add}>+ 添加年份</Button>}>
        <Spin spinning={aggregating} tip="正在聚合基础数据...">
          <Table
            size="small"
            dataSource={annualNet.map((d, i) => ({ ...d, idx: i, cum: cumulative[i]?.cum ?? 0 }))}
            rowKey="idx"
            pagination={false}
            scroll={{ y: 320 }}
            columns={[
              { title: '年', dataIndex: 'year', width: 100,
                render: (v: number, _: any, idx: number) => (
                  <InputNumber value={v} min={2000} max={2100} onChange={(e) => update(idx, 'year', e as number)} style={{ width: 90 }} />
                ) },
              { title: '资产收入(万)', dataIndex: 'asset_amount', width: 150,
                render: (v: number, _: any, idx: number) => (
                  <InputNumber
                    value={v ?? 0}
                    step={100}
                    onChange={(e) => update(idx, 'asset_amount', e as number)}
                    style={{ width: 130 }}
                    formatter={(val) => val?.toLocaleString()}
                  />
                ) },
              { title: '负债支出(万)', dataIndex: 'liability_amount', width: 150,
                render: (v: number, _: any, idx: number) => (
                  <InputNumber
                    value={v ?? 0}
                    step={100}
                    onChange={(e) => update(idx, 'liability_amount', e as number)}
                    style={{ width: 130 }}
                    formatter={(val) => val?.toLocaleString()}
                  />
                ) },
              { title: '净现金流(万)', dataIndex: 'net', width: 150,
                render: (v: number) => (
                  <span style={{ color: v >= 0 ? '#52c41a' : '#ff4d4f', fontWeight: 600 }}>
                    {v?.toLocaleString() ?? '-'}
                  </span>
                ) },
              { title: '累计(万)', dataIndex: 'cum', width: 150,
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
        </Spin>
      </Card>

      <Card style={{ marginTop: 16, textAlign: 'center' }}>
        <Button type="primary" size="large" loading={loading} icon={<PlayCircleOutlined />}
          onClick={onAnalyze}
          disabled={annualNet.length === 0}
          style={{ background: 'linear-gradient(135deg, #c2410c 0%, #9a3412 100%)', border: 'none', minWidth: 200 }}>
          计算回正期
        </Button>
        {annualNet.length === 0 && (
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">请先点击「从基础数据加载」按时间区间拉取净现金流</Text>
          </div>
        )}
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
                valueStyle={{ color: result.status === 'PASS' ? '#52c41a' : result.status === 'WARN' ? '#faad14' : '#ff4d4f' }}
              />
              <Text type="secondary">阈值 ≤ {threshold} 年</Text>
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