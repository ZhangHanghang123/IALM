/**
 * IALM 分析历史
 */
import { useEffect, useState } from 'react'
import { Card, Table, Tag, Typography } from 'antd'
import { algorithmsApi } from '../api'

const { Title } = Typography

const statusColor: Record<string, string> = {
  PASS: 'green',
  WARN: 'orange',
  FAIL: 'red',
}

export default function History() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    algorithmsApi
      .history({ page: 1, page_size: 50 })
      .then((r) => setItems(r.data.items || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    {
      title: '分析日期',
      dataIndex: 'analysis_date',
      width: 180,
      render: (v: string) => v ? new Date(v).toLocaleString('zh-CN') : '-',
    },
    {
      title: '机构 ID',
      dataIndex: 'company_id',
      width: 100,
    },
    {
      title: '期限匹配率',
      dataIndex: 'duration_match_ratio',
      width: 130,
      render: (v: number, r: any) => v != null ? `${v.toFixed(4)} ${getStatusTag(r.duration_match_status)}` : '-',
    },
    {
      title: '成本收益比',
      dataIndex: 'cost_yield_ratio',
      width: 130,
      render: (v: number, r: any) => v != null ? `${v.toFixed(4)} ${getStatusTag(r.cost_yield_status)}` : '-',
    },
    {
      title: '回正期',
      dataIndex: 'cashflow_payback_years',
      width: 110,
      render: (v: number, r: any) => v != null ? `${v.toFixed(2)} 年 ${getStatusTag(r.cashflow_payback_status)}` : '-',
    },
    {
      title: '久期缺口',
      dataIndex: 'duration_gap_years',
      width: 130,
      render: (v: number, r: any) => v != null ? `${v.toFixed(2)} 年 ${getStatusTag(r.duration_gap_status)}` : '-',
    },
    {
      title: '总评',
      dataIndex: 'overall_status',
      width: 100,
      render: (v: string) => <Tag color={statusColor[v]}>{v}</Tag>,
    },
    { title: '算法版本', dataIndex: 'algorithm_version', width: 100 },
  ]

  function getStatusTag(status: string) {
    return <Tag color={statusColor[status]} style={{ marginLeft: 4 }}>{status}</Tag>
  }

  return (
    <div>
      <Title level={3}>📜 分析历史</Title>
      <Card style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          dataSource={items}
          columns={columns}
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>
    </div>
  )
}