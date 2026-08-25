/**
 * IALM 保险公司管理
 */
import { useEffect, useState } from 'react'
import { Table, Tag, Card, Space, Typography } from 'antd'
import { companiesApi } from '../api'

const { Title } = Typography

const typeMap: Record<string, { text: string; color: string }> = {
  LIFE: { text: '寿险', color: 'blue' },
  PROPERTY: { text: '财险', color: 'orange' },
  HEALTH: { text: '健康险', color: 'cyan' },
  REINSURANCE: { text: '再保险', color: 'purple' },
}

export default function Companies() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const r = await companiesApi.list({ page: 1, page_size: 50 })
      setItems(r.data.items || [])
    } catch {}
    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  const columns = [
    { title: '机构编码', dataIndex: 'company_code', width: 120 },
    { title: '公司名称', dataIndex: 'company_name' },
    { title: '简称', dataIndex: 'company_short', width: 100 },
    {
      title: '类型',
      dataIndex: 'company_type',
      width: 100,
      render: (v: string) => <Tag color={typeMap[v]?.color}>{typeMap[v]?.text || v}</Tag>,
    },
    {
      title: '监管评级',
      dataIndex: 'regulatory_rating',
      width: 100,
      render: (v: string) => v ? <Tag color={v === 'A' ? 'green' : v === 'B' ? 'blue' : 'orange'}>{v}</Tag> : '-',
    },
    {
      title: '注册资本',
      dataIndex: 'registered_capital',
      width: 160,
      render: (v: number) => v ? `${(v / 10000).toLocaleString()} 万元` : '-',
    },
  ]

  return (
    <div>
      <Title level={3}>🏢 保险公司管理</Title>
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