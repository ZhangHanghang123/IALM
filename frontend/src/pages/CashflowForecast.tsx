/**
 * IALM 现金流预测 + 蒙特卡洛模拟
 */
import { useState } from 'react'
import { Card, Form, InputNumber, Button, Typography, Empty, Tabs, Table, Statistic, Row, Col, Alert } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'

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
  const [result, setResult] = useState<any>(null)

  const onPredict = () => {
    const v = form.getFieldsValue()
    const horizon = v.horizon || 30
    const initial = v.initialCashflow || 1000
    const growth = v.growthRate || 0.03
    const volatility = v.volatility || 0.1

    // 简化现金流预测：GBM（几何布朗运动）
    const years = []
    let value = initial
    for (let i = 0; i <= horizon; i++) {
      years.push({ year: 2025 + i, value: Math.round(value) })
      // Box-Muller 变换生成正态随机数
      const u1 = Math.random()
      const u2 = Math.random()
      const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
      value = value * Math.exp((growth - 0.5 * volatility ** 2) + volatility * z)
    }

    // 同时生成 5%/50%/95% 置信区间（10次蒙特卡洛抽样）
    const paths: number[][] = []
    for (let p = 0; p < 100; p++) {
      const path: number[] = [initial]
      let v = initial
      for (let i = 1; i <= horizon; i++) {
        const u1 = Math.random()
        const u2 = Math.random()
        const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
        v = v * Math.exp((growth - 0.5 * volatility ** 2) + volatility * z)
        path.push(Math.round(v))
      }
      paths.push(path)
    }

    const medianPath = years.map((_, i) => {
      const sorted = paths.map(p => p[i]).sort((a, b) => a - b)
      return sorted[50]
    })
    const p5Path = years.map((_, i) => {
      const sorted = paths.map(p => p[i]).sort((a, b) => a - b)
      return sorted[5]
    })
    const p95Path = years.map((_, i) => {
      const sorted = paths.map(p => p[i]).sort((a, b) => a - b)
      return sorted[95]
    })

    setResult({
      years: years.map(y => y.year),
      median: medianPath,
      p5: p5Path,
      p95: p95Path,
      horizon,
    })
  }

  const chartOption = result && {
    title: { text: '现金流预测（GBM 模型）', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0 },
    grid: { left: 60, right: 30, top: 50, bottom: 60 },
    xAxis: { type: 'category', data: result.years },
    yAxis: { type: 'value', name: '现金流(万)' },
    series: [
      { name: '95% 上限', type: 'line', data: result.p95, lineStyle: { type: 'dashed', color: '#52c41a' }, symbol: 'none' },
      { name: '中位数', type: 'line', data: result.median, lineStyle: { color: '#667eea', width: 2 }, areaStyle: { color: 'rgba(102, 126, 234, 0.1)' } },
      { name: '5% 下限', type: 'line', data: result.p5, lineStyle: { type: 'dashed', color: '#ff4d4f' }, symbol: 'none' },
    ],
  }

  return (
    <div>
      <Title level={3}>📈 现金流预测</Title>
      <Text type="secondary">基于精算假设预测未来资产/负债现金流（GBM 几何布朗运动）</Text>

      <Card style={{ marginTop: 16 }}>
        <Form form={form} layout="inline" initialValues={{ horizon: 30, initialCashflow: 1000, growthRate: 3, volatility: 10 }}>
          <Form.Item label="预测期(年)" name="horizon">
            <InputNumber min={1} max={50} style={{ width: 100 }} />
          </Form.Item>
          <Form.Item label="初始现金流(万)" name="initialCashflow">
            <InputNumber min={0} step={100} style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="预期增长率" name="growthRate">
            <InputNumber min={-10} max={20} step={0.1} addonAfter="%" style={{ width: 110 }} />
          </Form.Item>
          <Form.Item label="波动率" name="volatility">
            <InputNumber min={0} max={50} step={1} addonAfter="%" style={{ width: 100 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={onPredict}>运行预测</Button>
          </Form.Item>
        </Form>
      </Card>

      {result ? (
        <Card style={{ marginTop: 16 }}>
          <ReactECharts option={chartOption} style={{ height: 400 }} />
          <Alert
            style={{ marginTop: 16 }}
            type="info"
            message="模型说明"
            description="采用 GBM（几何布朗运动）模型，模拟 100 条路径并给出 5%/50%/95% 分位数。公式：V_{t+1} = V_t · exp((μ - σ²/2) + σ·z)，z~N(0,1)"
          />
        </Card>
      ) : (
        <Empty description="请设置参数后点击运行预测" style={{ marginTop: 60 }} />
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
      // 运行 nSim 次模拟
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
        if (p < 50) allPaths.push(path) // 只画前50条
      }

      // 统计
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