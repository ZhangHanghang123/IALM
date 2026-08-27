/**
 * IALM 现金流预测 + 蒙特卡洛模拟
 * 现金流预测：分 资产 / 负债 / 净现金流 三条线预测，初始值从资产负债数据管理统计当前余额
 */
import { useState, useEffect } from 'react'
import { Card, Form, InputNumber, Button, Typography, Empty, Tabs, Table, Statistic, Row, Col, Alert, Select, Space, Spin, Tag } from 'antd'
import { PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { algorithmsApi, companiesApi } from '../api'

const { Title, Text, Paragraph } = Typography

export default function CashflowForecast() {
  return (
    <Tabs
      defaultActiveKey="forecast"
      type="card"
      items={[
        {
          key: 'forecast',
          label: '现金流预测',
          children: <ForecastPage />,
        },
        {
          key: 'monte-carlo',
          label: '蒙特卡洛模拟',
          children: <MonteCarloPage />,
        },
      ]}
    />
  )
}

function ForecastPage() {
  const [form] = Form.useForm()
  const [companyId, setCompanyId] = useState<number>(1)
  const [companies, setCompanies] = useState<any[]>([])
  const [scenarioCode, setScenarioCode] = useState<string>('BASE')
  const [initialAsset, setInitialAsset] = useState<number>(0)
  const [initialLiability, setInitialLiability] = useState<number>(0)
  const [balanceSummary, setBalanceSummary] = useState<any>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [initializing, setInitializing] = useState(false)

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

  // 从基础数据加载当前余额，作为预测初始值
  const onLoadBalance = async () => {
    setInitializing(true)
    try {
      const r = await algorithmsApi.currentBalance({ company_id: companyId })
      const data = r.data
      setBalanceSummary(data)
      setInitialAsset(data.asset_total_book_value)
      setInitialLiability(data.liability_reserve_total)
      message.success(`已加载当前余额：资产 ${data.asset_total_book_value.toLocaleString()} 万 / 负债 ${data.liability_reserve_total.toLocaleString()} 万`)
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载失败')
    }
    setInitializing(false)
  }

  // 三条线预测：资产 / 负债 / 净现金流
  const onPredict = () => {
    const v = form.getFieldsValue()
    const horizon = v.horizon || 30
    const assetMu = (v.assetGrowth ?? 4.5) / 100   // 资产端收益率
    const liabMu = (v.liabGrowth ?? 3.5) / 100    // 负债端增长率
    const volatility = (v.volatility ?? 10) / 100

    const years: number[] = []
    for (let i = 0; i <= horizon; i++) years.push(2025 + i)

    // 单条预测：GBM 几何布朗运动
    const gbm = (start: number, mu: number, sigma: number) => {
      const path: number[] = [start]
      let value = start
      for (let i = 1; i <= horizon; i++) {
        const u1 = Math.random() || 1e-9
        const u2 = Math.random()
        const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
        value = value * Math.exp((mu - 0.5 * sigma ** 2) + sigma * z)
        path.push(Math.round(value))
      }
      return path
    }

    // 100 次蒙特卡洛模拟，统计中位数 + 5%/95% 分位数
    const assetPaths: number[][] = []
    const liabPaths: number[][] = []
    const netPaths: number[][] = []
    for (let p = 0; p < 100; p++) {
      const aPath = gbm(initialAsset, assetMu, volatility)
      const lPath = gbm(initialLiability, liabMu, volatility * 0.6) // 负债波动率较低
      assetPaths.push(aPath)
      liabPaths.push(lPath)
      netPaths.push(aPath.map((v, i) => v - lPath[i]))
    }
    const percentile = (paths: number[][], yearIdx: number, p: number) => {
      const sorted = paths.map(path => path[yearIdx]).sort((a, b) => a - b)
      return sorted[Math.floor(sorted.length * p)]
    }
    const assetMedian = years.map((_, i) => percentile(assetPaths, i, 0.5))
    const assetP5 = years.map((_, i) => percentile(assetPaths, i, 0.05))
    const assetP95 = years.map((_, i) => percentile(assetPaths, i, 0.95))
    const liabMedian = years.map((_, i) => percentile(liabPaths, i, 0.5))
    const liabP5 = years.map((_, i) => percentile(liabPaths, i, 0.05))
    const liabP95 = years.map((_, i) => percentile(liabPaths, i, 0.95))
    const netMedian = years.map((_, i) => percentile(netPaths, i, 0.5))
    const netP5 = years.map((_, i) => percentile(netPaths, i, 0.05))
    const netP95 = years.map((_, i) => percentile(netPaths, i, 0.95))

    setResult({
      years,
      assetMedian, assetP5, assetP95,
      liabMedian, liabP5, liabP95,
      netMedian, netP5, netP95,
      horizon,
    })
  }

  const chartOption = result && {
    title: { text: '现金流预测 — 资产 / 负债 / 净现金流 三线', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0 },
    grid: { left: 70, right: 30, top: 50, bottom: 60 },
    xAxis: { type: 'category', data: result.years, name: '年' },
    yAxis: { type: 'value', name: '余额(万元)' },
    series: [
      // 资产端
      { name: '资产95%上限', type: 'line', data: result.assetP95, lineStyle: { type: 'dashed', color: 'rgba(82,196,26,0.6)' }, symbol: 'none', stack: 'a' },
      { name: '资产中位数', type: 'line', data: result.assetMedian, lineStyle: { color: '#52c41a', width: 2 }, areaStyle: { color: 'rgba(82,196,26,0.1)' }, stack: 'a' },
      { name: '资产5%下限', type: 'line', data: result.assetP5, lineStyle: { type: 'dashed', color: 'rgba(82,196,26,0.6)' }, symbol: 'none', stack: 'a' },
      // 负债端
      { name: '负债95%上限', type: 'line', data: result.liabP95, lineStyle: { type: 'dashed', color: 'rgba(255,77,79,0.6)' }, symbol: 'none', stack: 'l' },
      { name: '负债中位数', type: 'line', data: result.liabMedian, lineStyle: { color: '#ff4d4f', width: 2 }, areaStyle: { color: 'rgba(255,77,79,0.1)' }, stack: 'l' },
      { name: '负债5%下限', type: 'line', data: result.liabP5, lineStyle: { type: 'dashed', color: 'rgba(255,77,79,0.6)' }, symbol: 'none', stack: 'l' },
      // 净现金流
      { name: '净现金流95%', type: 'line', data: result.netP95, lineStyle: { type: 'dashed', color: 'rgba(102,126,234,0.6)' }, symbol: 'none', stack: 'n' },
      { name: '净现金流', type: 'line', data: result.netMedian, lineStyle: { color: '#667eea', width: 3 }, areaStyle: { color: 'rgba(102,126,234,0.15)' }, stack: 'n' },
      { name: '净现金流5%', type: 'line', data: result.netP5, lineStyle: { type: 'dashed', color: 'rgba(102,126,234,0.6)' }, symbol: 'none', stack: 'n' },
    ],
  }

  return (
    <div>
      <Title level={3}>📈 现金流预测</Title>
      <Text type="secondary">分 资产 / 负债 / 净现金流 三条线预测，初始值从资产负债数据管理自动统计</Text>

      {/* 数据加载条件 */}
      <Card style={{ marginTop: 16 }} title="🗂️ 数据加载条件（初始余额）">
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
            loading={initializing}
            onClick={onLoadBalance}
            style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}
          >
            从资产负债数据加载初始余额
          </Button>
        </Space>

        {balanceSummary && (
          <Alert
            style={{ marginTop: 12 }}
            type="info"
            showIcon
            message={
              <Space wrap>
                <Tag color="green">资产账面价值 {balanceSummary.asset_total_book_value.toLocaleString()} 万元</Tag>
                <Tag color="orange">负债准备金 {balanceSummary.liability_reserve_total.toLocaleString()} 万元</Tag>
                <Tag color={balanceSummary.net_balance >= 0 ? 'blue' : 'red'}>
                  净资产 {balanceSummary.net_balance >= 0 ? '+' : ''}{balanceSummary.net_balance.toLocaleString()} 万元
                </Tag>
              </Space>
            }
          />
        )}
      </Card>

      {/* 预测参数 */}
      <Card style={{ marginTop: 16 }}>
        <Form form={form} layout="inline" initialValues={{ horizon: 30, assetGrowth: 4.5, liabGrowth: 3.5, volatility: 10 }}>
          <Form.Item label="预测期(年)" name="horizon">
            <InputNumber min={1} max={50} style={{ width: 90 }} />
          </Form.Item>
          <Form.Item label="资产增长率" name="assetGrowth">
            <InputNumber min={-10} max={20} step={0.1} addonAfter="%" style={{ width: 110 }} />
          </Form.Item>
          <Form.Item label="负债增长率" name="liabGrowth">
            <InputNumber min={-10} max={20} step={0.1} addonAfter="%" style={{ width: 110 }} />
          </Form.Item>
          <Form.Item label="波动率" name="volatility">
            <InputNumber min={0} max={50} step={1} addonAfter="%" style={{ width: 100 }} />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={onPredict}
              disabled={initialAsset === 0}
              style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}
            >
              运行三线预测
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* 初始值概览 */}
      {(initialAsset > 0 || initialLiability > 0) && (
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={8}>
            <Card size="small">
              <Statistic
                title="资产初始余额"
                value={initialAsset}
                suffix="万元"
                valueStyle={{ color: '#52c41a' }}
              />
              <Text type="secondary">来源：ialm_asset_holding.cost_value 求和</Text>
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small">
              <Statistic
                title="负债初始余额"
                value={initialLiability}
                suffix="万元"
                valueStyle={{ color: '#ff4d4f' }}
              />
              <Text type="secondary">来源：ialm_reserve.amount 求和</Text>
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small">
              <Statistic
                title="净资产"
                value={initialAsset - initialLiability}
                suffix="万元"
                valueStyle={{ color: (initialAsset - initialLiability) >= 0 ? '#667eea' : '#ff4d4f' }}
              />
              <Text type="secondary">净现金流预测起点 = 资产 − 负债</Text>
            </Card>
          </Col>
        </Row>
      )}

      {/* 预测结果图 */}
      {result ? (
        <Card style={{ marginTop: 16 }}>
          <ReactECharts option={chartOption} style={{ height: 450 }} />
          <Alert
            style={{ marginTop: 16 }}
            type="info"
            message="三线预测说明"
            description={
              <div>
                <div>• <b style={{ color: '#52c41a' }}>资产端</b>：以账面价值为初始值，按资产增长率做 GBM 模拟</div>
                <div>• <b style={{ color: '#ff4d4f' }}>负债端</b>：以准备金为初始值，按负债增长率做 GBM 模拟（波动率取资产 60%）</div>
                <div>• <b style={{ color: '#667eea' }}>净现金流</b>：每年资产 − 负债，反映保险公司偿付能力富余</div>
                <div>• 公式：V<sub>t+1</sub> = V<sub>t</sub> · exp((μ - σ²/2) + σ·z)，z ~ N(0,1)</div>
              </div>
            }
          />
        </Card>
      ) : (
        <Empty description="请先加载初始余额，再设置参数运行预测" style={{ marginTop: 60 }} />
      )}
    </div>
  )
}

function MonteCarloPage() {
  const [form] = Form.useForm()
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<any>(null)

  const onRun = () => {
    const v = form.getFieldsValue()
    const horizon = v.horizon || 30
    const initial = v.initial || 1000
    const mu = (v.mu || 4) / 100
    const sigma = (v.sigma || 15) / 100
    const nSim = v.nSim || 500
    const ruinThreshold = (v.ruinThreshold || 500)

    setRunning(true)
    setTimeout(() => {
      const finals: number[] = []
      let ruinCount = 0
      const allPaths: number[][] = []

      for (let p = 0; p < nSim; p++) {
        const path: number[] = [initial]
        let value = initial
        for (let i = 1; i <= horizon; i++) {
          const u1 = Math.random() || 1e-9
          const u2 = Math.random()
          const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
          value = value * Math.exp((mu - 0.5 * sigma ** 2) + sigma * z)
          if (value < ruinThreshold) ruinCount++
          path.push(Math.round(value))
        }
        finals.push(value)
        if (p < 50) allPaths.push(path)
      }

      finals.sort((a, b) => a - b)
      const median = finals[Math.floor(nSim / 2)]
      const p5 = finals[Math.floor(nSim * 0.05)]
      const p95 = finals[Math.floor(nSim * 0.95)]
      const mean = finals.reduce((a, b) => a + b, 0) / nSim
      const std = Math.sqrt(finals.reduce((s, x) => s + (x - mean) ** 2, 0) / nSim)
      const ruinProb = ruinCount / (nSim * horizon)

      setResult({
        horizon,
        initial,
        nSim,
        median: Math.round(median),
        p5: Math.round(p5),
        p95: Math.round(p95),
        mean: Math.round(mean),
        std: Math.round(std),
        ruinProb: (ruinProb * 100).toFixed(2),
        paths: allPaths,
        years: Array.from({ length: horizon + 1 }, (_, i) => 2025 + i),
      })
      setRunning(false)
    }, 100)
  }

  const chartOption = result && {
    title: { text: `蒙特卡洛模拟 ${result.nSim} 次路径`, left: 'center' },
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 30, top: 50, bottom: 60 },
    xAxis: { type: 'category', data: result.years },
    yAxis: { type: 'value', name: '资产价值(万)' },
    series: result.paths.map((_: any, i: number) => ({
      type: 'line',
      data: result.paths[i],
      showSymbol: false,
      lineStyle: { width: 0.5, opacity: 0.3, color: '#667eea' },
      smooth: true,
      name: '路径' + (i + 1),
    })),
  }

  return (
    <div>
      <Title level={3}>🎲 蒙特卡洛模拟</Title>
      <Text type="secondary">资产价值随机路径模拟 + 破产概率评估</Text>

      <Card style={{ marginTop: 16 }}>
        <Form form={form} layout="inline" initialValues={{ horizon: 30, initial: 1000, mu: 4, sigma: 15, nSim: 500, ruinThreshold: 500 }}>
          <Form.Item label="模拟期(年)" name="horizon"><InputNumber min={1} max={50} style={{ width: 90 }} /></Form.Item>
          <Form.Item label="初始资产" name="initial"><InputNumber min={0} step={100} style={{ width: 110 }} /></Form.Item>
          <Form.Item label="预期收益" name="mu"><InputNumber min={-10} max={20} step={0.5} addonAfter="%" style={{ width: 100 }} /></Form.Item>
          <Form.Item label="波动率" name="sigma"><InputNumber min={0} max={50} step={1} addonAfter="%" style={{ width: 90 }} /></Form.Item>
          <Form.Item label="模拟次数" name="nSim"><InputNumber min={100} max={5000} step={100} style={{ width: 100 }} /></Form.Item>
          <Form.Item label="破产阈值" name="ruinThreshold"><InputNumber min={0} step={100} style={{ width: 100 }} /></Form.Item>
          <Form.Item>
            <Button type="primary" icon={<PlayCircleOutlined />} loading={running} onClick={onRun}>运行</Button>
          </Form.Item>
        </Form>
      </Card>

      {result && (
        <>
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={6}><Card><Statistic title="中位终值" value={result.median} suffix="万" /></Card></Col>
            <Col span={6}><Card><Statistic title="均值" value={result.mean} suffix="万" /></Card></Col>
            <Col span={6}><Card><Statistic title="标准差" value={result.std} suffix="万" /></Card></Col>
            <Col span={6}><Card>
              <Statistic title="破产概率" value={result.ruinProb} suffix="%" valueStyle={{ color: parseFloat(result.ruinProb) > 5 ? '#ff4d4f' : '#52c41a' }} />
            </Card></Col>
          </Row>
          <Card style={{ marginTop: 16 }}>
            <ReactECharts option={chartOption} style={{ height: 400 }} />
          </Card>
          <Card title="置信区间" style={{ marginTop: 16 }}>
            <Paragraph>
              • <b>5% 分位数</b>（悲观）：{result.p5} 万
              <br />• <b>中位数</b>（基准）：{result.median} 万
              <br />• <b>95% 分位数</b>（乐观）：{result.p95} 万
            </Paragraph>
          </Card>
        </>
      )}
    </div>
  )
}