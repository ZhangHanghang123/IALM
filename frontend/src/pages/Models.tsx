/**
 * IALM 模型管理（模型定义 + 版本 + 参数）
 */
import { Card, Tabs, Tag, Typography } from 'antd'
import DataListPage from '../components/DataListPage'
import { modelsApi } from '../api'

const { Title, Text } = Typography

const priorityColors: Record<string, string> = {
  P0: 'red',
  P1: 'orange',
  P2: 'blue',
}

const testColors: Record<string, string> = {
  PASS: 'green',
  FAIL: 'red',
  PENDING: 'orange',
}

export default function Models() {
  return (
    <Tabs
      defaultActiveKey="definitions"
      type="card"
      items={[
        {
          key: 'definitions',
          label: '模型定义',
          children: (
            <DataListPage
              title="14 项核心算法模型"
              subtitle="算法模型定义（编码/名称/类别/优先级/公式）"
              fetcher={(p) => modelsApi.definitions(p)}
              columns={[
                { title: '模型编码', dataIndex: 'model_code', width: 120,
                  render: (v: string) => <Tag color="blue">{v}</Tag> },
                { title: '模型名称', dataIndex: 'model_name' },
                { title: '类别', dataIndex: 'model_category', width: 140,
                  render: (v: string) => <Tag>{v}</Tag> },
                { title: '优先级', dataIndex: 'priority', width: 100,
                  render: (v: string) => <Tag color={priorityColors[v]}>{v}</Tag> },
                { title: '监管来源', dataIndex: 'regulatory_source', width: 120 },
                { title: '说明', dataIndex: 'description', width: 280 },
                { title: '公式', dataIndex: 'formula_text', width: 280,
                  render: (v: string) => <code style={{ fontSize: 11 }}>{v}</code> },
              ]}
            />
          ),
        },
        {
          key: 'versions',
          label: '模型版本',
          children: (
            <DataListPage
              title="模型版本管理"
              subtitle="算法版本号 + 发布日期 + 生产/测试状态"
              fetcher={(p) => modelsApi.versions(p)}
              columns={[
                { title: '模型', dataIndex: 'model_name', width: 200 },
                { title: '版本号', dataIndex: 'version_no', width: 140 },
                { title: '发布日期', dataIndex: 'release_date', width: 140 },
                { title: '生产环境', dataIndex: 'is_production', width: 120,
                  render: (v: number) => v ? <Tag color="green">✓ 生产</Tag> : <Tag>测试</Tag> },
                { title: '算法变更', dataIndex: 'algorithm_changes', width: 280 },
                { title: '测试状态', dataIndex: 'test_status', width: 120,
                  render: (v: string) => <Tag color={testColors[v]}>{v}</Tag> },
              ]}
            />
          ),
        },
        {
          key: 'parameters',
          label: '模型参数',
          children: (
            <DataListPage
              title="模型参数配置"
              subtitle="算法默认参数与当前值"
              fetcher={(p) => modelsApi.parameters({ ...p, page_size: 50 })}
              columns={[
                { title: '模型ID', dataIndex: 'model_id', width: 100 },
                { title: '参数名', dataIndex: 'parameter_name', width: 180 },
                { title: '当前值', dataIndex: 'parameter_value', width: 180 },
                { title: '默认值', dataIndex: 'default_value', width: 180 },
                { title: '类型', dataIndex: 'value_type', width: 100 },
                { title: '单位', dataIndex: 'unit', width: 80 },
                { title: '说明', dataIndex: 'description', width: 280 },
              ]}
            />
          ),
        },
      ]}
    />
  )
}