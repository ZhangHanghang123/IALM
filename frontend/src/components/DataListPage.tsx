/**
 * 通用数据列表页面（表格 + 搜索 + 分页）
 */
import { useState, useEffect } from 'react'
import { Card, Table, Input, Button, Space, Typography } from 'antd'
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

interface Column {
  title: string
  dataIndex: string
  width?: number
  render?: (v: any, r: any) => any
}

interface DataListPageProps {
  title: string
  subtitle?: string
  fetcher: (params: any) => Promise<any>
  columns: Column[]
  extraActions?: React.ReactNode
}

export default function DataListPage({ title, subtitle, fetcher, columns, extraActions }: DataListPageProps) {
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [loading, setLoading] = useState(false)
  const [keyword, setKeyword] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const r = await fetcher({ page, page_size: pageSize, keyword: keyword || undefined })
      setItems(r.data?.items || [])
      setTotal(r.data?.total || 0)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  return (
    <div>
      <Title level={3}>{title}</Title>
      {subtitle && <Text type="secondary">{subtitle}</Text>}

      <Card style={{ marginTop: 16 }}>
        <Space style={{ marginBottom: 16 }} size={8}>
          <Input
            placeholder="搜索关键字"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={() => { setPage(1); load() }}
            style={{ width: 240 }}
            allowClear
            prefix={<SearchOutlined />}
          />
          <Button type="primary" onClick={() => { setPage(1); load() }}>搜索</Button>
          <Button icon={<ReloadOutlined />} onClick={() => { setKeyword(''); setPage(1); load() }}>重置</Button>
          {extraActions}
        </Space>

        <Table
          rowKey="id"
          dataSource={items}
          columns={columns as any}
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: (p) => setPage(p),
            showSizeChanger: false,
            showTotal: (t) => `共 ${t} 条`,
          }}
        />
      </Card>
    </div>
  )
}