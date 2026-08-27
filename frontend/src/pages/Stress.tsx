/**
 * IALM 压力测试（监管情景 + 结果 + 运行模拟）
 * 监管情景 tab：可展开查看具体冲击因子配置，支持编辑修改
 */
import { useState, useEffect } from 'react'
import {
  Card, Tabs, Tag, Typography, Statistic, Row, Col, Table, Button, Space, Input as AntInput,
  Modal, Form, Select, message, Empty, Switch, Alert, Tooltip, Divider,
} from 'antd'
import {
  ThunderboltOutlined, EditOutlined, PlusOutlined, DeleteOutlined,
  ReloadOutlined, CaretRightOutlined, InfoCircleOutlined,
} from '@ant-design/icons'
import StressRunner from '../components/StressRunner'
import { stressApi } from '../api'

const { Title, Text, Paragraph } = Typography

const scenarioColors: Record<string, string> = {
  INTEREST: 'blue',
  LAPSE: 'orange',
  INVESTMENT: 'purple',
  FX: 'cyan',
  COMPREHENSIVE: 'red',
  CUSTOM: 'green',
}

const factorTypeLabels: Record<string, string> = {
  parallel_shift: '利率平行移动',
  multiplier: '乘数',
  pct_change: '百分比变动',
}

const factorNameSuggestions = [
  'interest_rate', 'lapse_rate', 'investment_yield', 'mortality_rate',
  'expense_rate', 'USD_CNY', 'EUR_CNY', 'HKD_CNY', 'equity_price',
  'property_value', 'spread_widening', 'catastrophe_loss',
]

interface Factor {
  name: string
  type: string
  value: number
}

interface Scenario {
  id: number
  scenario_code: string
  scenario_name: string
  scenario_type: string
  source: string
  description: string
  shocks_json: { factors: Factor[] } | any
  is_active: number
}

export default function Stress() {
  return (
    <Tabs
      defaultActiveKey="scenarios"
      type="card"
      items={[
        { key: 'scenarios', label: '监管情景', children: <ScenariosTab /> },
        { key: 'results', label: '测试结果', children: <ResultsTab /> },
        { key: 'run', label: '运行模拟', children: <StressRunner /> },
      ]}
    />
  )
}

// ════════════════════════════════════════════════════════════
// 监管情景 tab - 可展开因子配置 + 编辑修改
// ════════════════════════════════════════════════════════════
function ScenariosTab() {
  const [items, setItems] = useState<Scenario[]>([])
  const [loading, setLoading] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editingScenario, setEditingScenario] = useState<Scenario | null>(null)
  const [editFactors, setEditFactors] = useState<Factor[]>([])
  const [editForm] = Form.useForm()
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const r = await stressApi.scenarios({ page: 1, page_size: 100 })
      setItems(r.data?.items || [])
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载失败')
    }
    setLoading(false)
  }
  useEffect(() => { load() }, [])

  const openEdit = (s: Scenario) => {
    setEditingScenario(s)
    setEditFactors(s.shocks_json?.factors ? [...s.shocks_json.factors] : [])
    editForm.setFieldsValue({
      scenario_name: s.scenario_name,
      scenario_type: s.scenario_type,
      description: s.description,
    })
    setEditModalOpen(true)
  }

  const addFactor = () => {
    setEditFactors([...editFactors, { name: 'interest_rate', type: 'parallel_shift', value: 0 }])
  }

  const updateFactor = (idx: number, key: keyof Factor, val: any) => {
    const arr = [...editFactors]
    arr[idx] = { ...arr[idx], [key]: val }
    setEditFactors(arr)
  }

  const removeFactor = (idx: number) => {
    setEditFactors(editFactors.filter((_, i) => i !== idx))
  }

  const onSave = async () => {
    if (!editingScenario) return
    if (editFactors.length === 0) {
      message.error('至少保留一个冲击因子')
      return
    }
    setSaving(true)
    try {
      const v = await editForm.validateFields()
      await stressApi.updateScenario(editingScenario.id, {
        scenario_name: v.scenario_name,
        scenario_type: v.scenario_type,
        description: v.description,
        shocks_json: { factors: editFactors },
      })
      message.success(`已保存情景 [${editingScenario.scenario_code}] 的配置`)
      setEditModalOpen(false)
      load()
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '保存失败')
    }
    setSaving(false)
  }

  const toggleActive = async (s: Scenario, checked: boolean) => {
    try {
      await stressApi.updateScenario(s.id, { is_active: checked ? 1 : 0 })
      message.success(checked ? `已启用 [${s.scenario_code}]` : `已停用 [${s.scenario_code}]`)
      load()
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '操作失败')
    }
  }

  return (
    <div>
      <Title level={3}>⚡ 监管压力情景</Title>
      <Text type="secondary">银保监会 6 个必选情景 + 用户自定义，可展开查看冲击因子并修改</Text>

      <Card style={{ marginTop: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Button icon={<ReloadOutlined />} onClick={load}>刷新</Button>
          <Text type="secondary">共 {items.length} 个情景</Text>
        </Space>

        <Table
          rowKey="id"
          dataSource={items}
          loading={loading}
          pagination={false}
          expandable={{
            expandedRowRender: (record: Scenario) => (
              <FactorsPanel
                factors={record.shocks_json?.factors || []}
                scenarioName={record.scenario_name}
              />
            ),
            expandIcon: ({ expanded, onExpand, record }) =>
              expanded ? (
                <CaretRightOutlined rotate={90} onClick={e => onExpand(record, e)} style={{ cursor: 'pointer' }} />
              ) : (
                <CaretRightOutlined onClick={e => onExpand(record, e)} style={{ cursor: 'pointer' }} />
              ),
          }}
          columns={[
            {
              title: '情景编码', dataIndex: 'scenario_code', width: 200,
              render: (v: string) => <Tag color="blue">{v}</Tag>,
            },
            { title: '情景名称', dataIndex: 'scenario_name' },
            {
              title: '类型', dataIndex: 'scenario_type', width: 130,
              render: (v: string) => <Tag color={scenarioColors[v] || 'default'}>{v}</Tag>,
            },
            {
              title: '来源', dataIndex: 'source', width: 100,
              render: (v: string) => v === 'REG' ? <Tag color="red">监管</Tag> : <Tag color="green">自定义</Tag>,
            },
            {
              title: '因子数', width: 100,
              render: (_: any, r: Scenario) => {
                const n = r.shocks_json?.factors?.length || 0
                return <Tag color={n > 0 ? 'blue' : 'default'}>{n} 个</Tag>
              },
            },
            { title: '说明', dataIndex: 'description', ellipsis: true },
            {
              title: '状态', dataIndex: 'is_active', width: 100,
              render: (v: number, r: Scenario) => (
                <Switch
                  size="small"
                  checked={!!v}
                  onChange={(c) => toggleActive(r, c)}
                  checkedChildren="启用"
                  unCheckedChildren="停用"
                />
              ),
            },
            {
              title: '操作', width: 120, fixed: 'right' as const,
              render: (_: any, r: Scenario) => (
                <Button
                  type="link" size="small" icon={<EditOutlined />}
                  onClick={() => openEdit(r)}
                >
                  修改配置
                </Button>
              ),
            },
          ]}
        />
      </Card>

      {/* 编辑 Modal */}
      <Modal
        title={`修改情景配置：${editingScenario?.scenario_name || ''}`}
        open={editModalOpen}
        onCancel={() => setEditModalOpen(false)}
        onOk={onSave}
        confirmLoading={saving}
        width={800}
        okText="保存配置"
        cancelText="取消"
      >
        {editingScenario && (
          <>
            <Alert
              type="info" showIcon
              message={
                <Space>
                  <span>情景编码：<Tag color="blue">{editingScenario.scenario_code}</Tag></span>
                  <span>来源：{editingScenario.source === 'REG' ? <Tag color="red">监管</Tag> : <Tag color="green">自定义</Tag>}</span>
                </Space>
              }
              style={{ marginBottom: 16 }}
            />

            <Form form={editForm} layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="情景名称" name="scenario_name" rules={[{ required: true }]}>
                    <AntInput />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="情景类型" name="scenario_type" rules={[{ required: true }]}>
                    <Select
                      options={[
                        { value: 'INTEREST', label: '利率风险' },
                        { value: 'LAPSE', label: '退保风险' },
                        { value: 'INVESTMENT', label: '投资风险' },
                        { value: 'FX', label: '汇率风险' },
                        { value: 'COMPREHENSIVE', label: '综合压力' },
                        { value: 'CUSTOM', label: '自定义' },
                      ]}
                    />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item label="说明" name="description">
                <AntInput.TextArea rows={2} />
              </Form.Item>
            </Form>

            <Divider />
            <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text strong>冲击因子配置 ({editFactors.length})</Text>
              <Button size="small" icon={<PlusOutlined />} onClick={addFactor}>添加因子</Button>
            </div>

            <Table
              size="small"
              dataSource={editFactors.map((f, i) => ({ ...f, idx: i }))}
              rowKey="idx"
              pagination={false}
              columns={[
                {
                  title: '因子名称', width: 180,
                  render: (_: any, r: any) => (
                    <AntInput
                      value={r.name}
                      onChange={(e) => updateFactor(r.idx, 'name', e.target.value)}
                      list="factor-name-suggestions"
                    />
                  ),
                },
                {
                  title: '冲击类型', width: 150,
                  render: (_: any, r: any) => (
                    <Select
                      value={r.type}
                      onChange={(v) => updateFactor(r.idx, 'type', v)}
                      style={{ width: '100%' }}
                      options={Object.entries(factorTypeLabels).map(([v, l]) => ({ value: v, label: l }))}
                    />
                  ),
                },
                {
                  title: '冲击值', width: 130,
                  render: (_: any, r: any) => (
                    <AntInput
                      type="number"
                      value={r.value}
                      onChange={(e) => updateFactor(r.idx, 'value', parseFloat(e.target.value) || 0)}
                      addonAfter={r.type === 'pct_change' ? '%' : r.type === 'parallel_shift' ? 'bp' : 'x'}
                    />
                  ),
                },
                {
                  title: '说明', width: 200,
                  render: (_: any, r: any) => {
                    const f = r as Factor
                    if (f.type === 'parallel_shift') {
                      return <Text type="secondary">{f.value > 0 ? '上行' : '下行'} {Math.abs(f.value)} bp</Text>
                    }
                    if (f.type === 'multiplier') {
                      return <Text type="secondary">{f.value < 1 ? '下降至' : '上升至'} {(f.value * 100).toFixed(0)}%</Text>
                    }
                    if (f.type === 'pct_change') {
                      return <Text type="secondary">{f.value > 0 ? '上涨' : '下跌'} {Math.abs(f.value)}%</Text>
                    }
                    return null
                  },
                },
                {
                  title: '操作', width: 80,
                  render: (_: any, r: any) => (
                    <Button danger size="small" icon={<DeleteOutlined />} onClick={() => removeFactor(r.idx)} />
                  ),
                },
              ]}
            />

            <datalist id="factor-name-suggestions">
              {factorNameSuggestions.map(n => <option key={n} value={n} />)}
            </datalist>

            <Alert
              type="warning" showIcon style={{ marginTop: 16 }}
              message={
                <div>
                  <strong>冲击值说明：</strong>
                  <ul style={{ margin: '4px 0 0 0', paddingLeft: 20 }}>
                    <li><b>利率平行移动</b>：正值 = 上行 bp（如 200 = +200bp），负值 = 下行 bp</li>
                    <li><b>乘数</b>：1.5 = 上升 50%（如退保率 1.5x），0.5 = 下降 50%（如投资收益率 0.5x）</li>
                    <li><b>百分比变动</b>：正负值表示涨跌幅（如 USD/CNY +15 = 涨 15%）</li>
                  </ul>
                </div>
              }
            />
          </>
        )}
      </Modal>
    </div>
  )
}

// ════════════════════════════════════════════════════════════
// 因子展开面板
// ════════════════════════════════════════════════════════════
function FactorsPanel({ factors, scenarioName }: { factors: Factor[]; scenarioName: string }) {
  if (!factors || factors.length === 0) {
    return <Empty description="无冲击因子配置" />
  }
  return (
    <div style={{ padding: '8px 16px', background: '#fafafa', borderRadius: 4 }}>
      <Space style={{ marginBottom: 8 }}>
        <Text strong>{scenarioName} · 冲击因子</Text>
        <Tag>{factors.length} 个因子</Tag>
      </Space>
      <Table
        size="small"
        dataSource={factors.map((f, i) => ({ ...f, idx: i }))}
        rowKey="idx"
        pagination={false}
        columns={[
          {
            title: '因子', dataIndex: 'name', width: 180,
            render: (v: string) => <Tag color="geekblue">{v}</Tag>,
          },
          {
            title: '类型', dataIndex: 'type', width: 130,
            render: (v: string) => factorTypeLabels[v] || v,
          },
          {
            title: '冲击值', dataIndex: 'value', width: 120,
            render: (v: number, r: Factor) => {
              const unit = r.type === 'pct_change' ? '%' : r.type === 'parallel_shift' ? 'bp' : 'x'
              return <Tag color="orange">{v} {unit}</Tag>
            },
          },
          {
            title: '说明', render: (_: any, r: Factor) => {
              if (r.type === 'parallel_shift') {
                return <span>{r.value > 0 ? '↗ 上行' : '↘ 下行'} {Math.abs(r.value)} bp</span>
              }
              if (r.type === 'multiplier') {
                const pct = ((r.value - 1) * 100).toFixed(0)
                return <span>{r.value < 1 ? '↘ 下降' : '↗ 上升'} {Math.abs(parseFloat(pct))}%</span>
              }
              if (r.type === 'pct_change') {
                return <span>{r.value > 0 ? '↗ 上涨' : '↘ 下跌'} {Math.abs(r.value)}%</span>
              }
              return '-'
            },
          },
        ]}
      />
    </div>
  )
}

// ════════════════════════════════════════════════════════════
// 测试结果 tab
// ════════════════════════════════════════════════════════════
function ResultsTab() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [pageState, setPageState] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)

  const load = async (p: number = 1) => {
    setLoading(true)
    try {
      const r = await stressApi.results({ page: p, page_size: pageSize })
      setItems(r.data?.items || [])
      setTotal(r.data?.total || 0)
      setPageState(p)
    } catch (e) { console.error(e) }
    setLoading(false)
  }
  useEffect(() => { load(1) }, [])

  return (
    <div>
      <Title level={3}>📋 压力测试结果</Title>
      <Text type="secondary">历史压力测试的 NAV/SCR/LCR 影响记录</Text>
      <Card style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          dataSource={items}
          loading={loading}
          pagination={{
            current: pageState,
            pageSize,
            total,
            onChange: (p) => load(p),
            showSizeChanger: false,
            showTotal: (t) => `共 ${t} 条`,
          }}
          columns={[
            { title: '保险公司', dataIndex: 'company_name', width: 140 },
            { title: '情景', dataIndex: 'scenario_name' },
            {
              title: '测试日', dataIndex: 'test_date', width: 140,
              render: (v: string) => v?.slice(0, 10),
            },
            {
              title: 'NAV 影响(万)', dataIndex: 'nav_impact', width: 140,
              render: (v: number) => (
                <span style={{ color: v < 0 ? '#ff4d4f' : '#52c41a' }}>
                  {v > 0 ? '+' : ''}{v?.toLocaleString()}
                </span>
              ),
            },
            {
              title: 'SCR 变化', dataIndex: 'scr_change', width: 120,
              render: (v: number) => `${v?.toFixed(2)}%`,
            },
            {
              title: 'LCR 变化', dataIndex: 'lcr_change', width: 120,
              render: (v: number) => `${v?.toFixed(2)}%`,
            },
            {
              title: '结果', dataIndex: 'passed', width: 100,
              render: (v: number) => v ? <Tag color="green">通过</Tag> : <Tag color="red">未通过</Tag>,
            },
          ]}
        />
      </Card>
    </div>
  )
}