/**
 * IALM 市场数据
 */
import { useState, useEffect } from 'react'
import { Card, Tabs, Tag, Table, Typography, Select, Space, Spin, Empty } from 'antd'
import ReactECharts from 'echarts-for-react'
import DataListPage from '../components/DataListPage'
import { marketDataApi } from '../api'

const { Title, Text } = Typography

export default function MarketData() {
  const [curves, setCurves] = useState<any[]>([])
  const [selectedCurveId, setSelectedCurveId] = useState<number | null>(null)
  const [points, setPoints] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    marketDataApi.yieldCurves({ page: 1, page_size: 100 }).then((r) => {
      setCurves(r.data.items || [])
      if (r.data.items?.length > 0) {
        setSelectedCurveId(r.data.items[0].id)
      }
    })
  }, [])

  useEffect(() => {
    if (!selectedCurveId) return
    setLoading(true)
    marketDataApi.yieldCurvePoints(selectedCurveId).then((r) => {
      setPoints(r.data.points || [])
    }).finally(() => setLoading(false))
  }, [selectedCurveId])

  const chartOption = {
    title: { text: curves.find(c => c.id === selectedCurveId)?.curve_name || '收益率曲线', left: 'center' },
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 30, top: 50, bottom: 60 },
    xAxis: {
      type: 'category',
      data: points.map(p => `${p.tenor_years}Y`),
      name: '期限',
    },
    yAxis: {
      type: 'value',
      name: '收益率(%)',
      axisLabel: { formatter: (v: number) => `${(v * 100).toFixed(2)}%` },
    },
    series: [{
      type: 'line',
      data: points.map(p => (p.rate * 100).toFixed(4)),
      itemStyle: { color: '#667eea' },
      smooth: true,
      areaStyle: { color: 'rgba(102, 126, 234, 0.1)' },
      markPoint: {
        data: [
          { type: 'max', name: '最大值' },
          { type: 'min', name: '最小值' },
        ],
      },
    }],
  }

  return (
    <Tabs
      defaultActiveKey="yield-curves"
      type="card"
      items={[
        {
          key: 'yield-curves',
          label: '收益率曲线',
          children: (
            <div>
              <Title level={3}>收益率曲线</Title>
              <Text type="secondary">中债/国开/信用/同业存单/外币利率曲线</Text>
              <Space style={{ marginTop: 16, marginBottom: 16 }}>
                <Text>选择曲线：</Text>
                <Select
                  style={{ width: 280 }}
                  value={selectedCurveId}
                  onChange={setSelectedCurveId}
                  options={curves.map(c => ({ value: c.id, label: `${c.curve_name} (${c.curve_type})` }))}
                />
              </Space>
              <Card>
                {loading ? <Spin /> : points.length > 0 ? (
                  <ReactECharts option={chartOption} style={{ height: 360 }} />
                ) : <Empty description="暂无数据" />}
              </Card>
              <Card title="曲线点位数据" style={{ marginTop: 16 }}>
                <Table
                  rowKey="id"
                  dataSource={points}
                  pagination={false}
                  size="small"
                  columns={[
                    { title: '年期', dataIndex: 'tenor_years', width: 100,
                      render: (v: number) => `${v}Y` },
                    { title: '收益率', dataIndex: 'rate', width: 140,
                      render: (v: number) => `${(v * 100).toFixed(3)}%` },
                    { title: '日期', dataIndex: 'curve_date', width: 140 },
                  ]}
                />
              </Card>
            </div>
          ),
        },
        {
          key: 'fx-rates',
          label: '汇率',
          children: (
            <DataListPage
              title="汇率数据"
              subtitle="USD/CNY/EUR/HKD 等主要币种汇率"
              fetcher={(p) => marketDataApi.fxRates(p)}
              columns={[
                { title: '币种对', dataIndex: 'currency_pair', width: 140 },
                { title: '买入价', dataIndex: 'bid_rate', width: 110,
                  render: (v: number) => v?.toFixed(4) },
                { title: '卖出价', dataIndex: 'ask_rate', width: 110,
                  render: (v: number) => v?.toFixed(4) },
                { title: '中间价', dataIndex: 'mid_rate', width: 110,
                  render: (v: number) => v?.toFixed(4) },
                { title: '日期', dataIndex: 'rate_date', width: 130 },
                { title: '来源', dataIndex: 'data_source', width: 100 },
              ]}
            />
          ),
        },
        {
          key: 'equity-indices',
          label: '股票指数',
          children: (
            <DataListPage
              title="股票指数"
              subtitle="沪深 300/中证 500/恒生指数等"
              fetcher={(p) => marketDataApi.equityIndices(p)}
              columns={[
                { title: '代码', dataIndex: 'index_code', width: 110 },
                { title: '名称', dataIndex: 'index_name', width: 200 },
                { title: '日期', dataIndex: 'trade_date', width: 110 },
                { title: '开', dataIndex: 'open_price', width: 100,
                  render: (v: number) => v?.toFixed(2) },
                { title: '高', dataIndex: 'high_price', width: 100,
                  render: (v: number) => v?.toFixed(2) },
                { title: '低', dataIndex: 'low_price', width: 100,
                  render: (v: number) => v?.toFixed(2) },
                { title: '收', dataIndex: 'close_price', width: 100,
                  render: (v: number) => v?.toFixed(2) },
                { title: '涨跌幅', dataIndex: 'change_rate', width: 100,
                  render: (v: number) => (
                    <span style={{ color: v > 0 ? '#ff4d4f' : v < 0 ? '#52c41a' : '#999' }}>
                      {v > 0 ? '+' : ''}{v?.toFixed(2)}%
                    </span>
                  ) },
              ]}
            />
          ),
        },
        {
          key: 'credit-spreads',
          label: '信用利差',
          children: (
            <DataListPage
              title="信用利差"
              subtitle="各评级/期限的信用利差（bps）"
              fetcher={(p) => marketDataApi.creditSpreads(p)}
              columns={[
                { title: '评级', dataIndex: 'rating', width: 100,
                  render: (v: string) => <Tag color="blue">{v}</Tag> },
                { title: '期限(年)', dataIndex: 'tenor_years', width: 100,
                  render: (v: number) => `${v}Y` },
                { title: '利差(bps)', dataIndex: 'spread_bps', width: 130,
                  render: (v: number) => v?.toFixed(1) },
                { title: '日期', dataIndex: 'spread_date', width: 140 },
                { title: '来源', dataIndex: 'data_source', width: 100 },
              ]}
            />
          ),
        },
      ]}
    />
  )
}