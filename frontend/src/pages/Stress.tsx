/**
 * IALM 压力测试
 * - 监管情景 tab：可展开查看具体冲击因子配置，支持编辑修改
 *   每行新增"运行此情景"按钮 → 弹出运行 Modal（参数从基础数据加载，用户可微调）
 * - 测试结果 tab：历史压力测试记录（运行后自动写入 ialm_stress_result）
 */
import { useState, useEffect } from 'react'
import {
  Card, Tabs, Tag, Typography, Row, Col, Table, Button, Space, Input as AntInput,
  Modal, Form, Select, Statistic, InputNumber, Tooltip, Empty, Switch, Alert, Divider, message,
} from 'antd'
import {
  ThunderboltOutlined, EditOutlined, PlusOutlined, DeleteOutlined,
  ReloadOutlined, CaretRightOutlined, InfoCircleOutlined, DatabaseOutlined, PlayCircleOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { stressApi, companiesApi } from '../api'

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

// 跨 tab 通知：ScenariosTab 运行后通知 ResultsTab 刷新
const publishRefresh = () => {
  const subs = (window as any).__stressRefreshSubs || []
  subs.forEach((cb: () => void) => cb())
}

export default function Stress() {
  return (
    <Tabs
      defaultActiveKey="scenarios"
      type="card"
      items={[
        { key: 'scenarios', label: '监管情景', children: <ScenariosTab /> },
        { key: 'results', label: '测试结果', children: <ResultsTab /> },
      ]}
    />
  )
}

// ════════════════════════════════════════════════════════════
// 监管情景 tab
// ════════════════════════════════════════════════════════════
function ScenariosTab() {
  const [items, setItems] = useState<Scenario[]>([])
  const [loading, setLoading] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editingScenario, setEditingScenario] = useState<Scenario | null>(null)
  const [editForm] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const [editFactors, setEditFactors] = useState<Factor[]>([])

  // 运行模拟 Modal 状态
  const [runModalOpen, setRunModalOpen] = useState(false)
  const [runningScenario, setRunningScenario] = useState<Scenario | null>(null)

  const load = async () => {
    setLoading(true)
    try {
      const r = await stressApi.scenarios({ page: 1, page_size: 100 })
      setItems(r.data?.items || [])
    } catch (e: any) {
      message.error('加载情景失败')
    }
    setLoading(false)
  }
  useEffect(() => { load() }, [])

  const openEdit = (s: Scenario) => {
    setEditingScenario(s)
    const factors = (s.shocks_json?.factors) || []
    setEditFactors(factors.map(f => ({ ...f })))
    editForm.setFieldsValue({
      scenario_name: s.scenario_name,
      scenario_type: s.scenario_type,
      description: s.description,
    })
    setEditModalOpen(true)
  }

  const updateFactor = (idx: number, key: keyof Factor, val: any) => {
    const arr = [...editFactors]
    arr[idx] = { ...arr[idx], [key]: val }
    setEditFactors(arr)
  }

  const removeFactor = (idx: number) => {
    setEditFactors(editFactors.filter((_, i) => i !== idx))
  }

  const addFactor = () => {
    setEditFactors([...editFactors, { name: 'interest_rate', type: 'parallel_shift', value: 100 }])
  }

  const onSave = async () => {
    if (!editingScenario) return
    try {
      const values = await editForm.validateFields()
      setSaving(true)
      await stressApi.updateScenario(editingScenario.id, {
        scenario_name: values.scenario_name,
        scenario_type: values.scenario_type,
        description: values.description,
        shocks_json: { factors: editFactors },
      })
      message.success('保存成功')
      setEditModalOpen(false)
      load()
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '保存失败')
    }
    setSaving(false)
  }

  const toggleActive = async (s: Scenario) => {
    try {
      await stressApi.updateScenario(s.id, { is_active: s.is_active ? 0 : 1 })
      message.success(s.is_active ? '已停用' : '已启用')
      load()
    } catch (e: any) {
      message.error('切换失败')
    }
  }

  const openRun = (s: Scenario) => {
    setRunningScenario(s)
    setRunModalOpen(true)
  }

  const onRunCompleted = () => {
    setRunModalOpen(false)
    publishRefresh()
  }

  return (
    <div>
      <Title level={3}>📋 监管预置压力情景</Title>
      <Text type="secondary">可展开查看具体冲击因子配置，支持编辑修改 · 每行可"运行此情景"</Text>

      <Card style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          dataSource={items}
          loading={loading}
          pagination={{ pageSize: 20, showTotal: t => `共 ${t} 条` }}
          expandable={{
            expandedRowRender: (r: Scenario) => <FactorsPanel factors={(r.shocks_json?.factors) || []} scenarioName={r.scenario_name} />,
            expandIcon: ({ expanded, onExpand, record }) => (
              <CaretRightOutlined
                onClick={e => onExpand(record, e as any)}
                rotate={expanded ? 90 : 0}
                style={{ transition: 'transform 0.2s' }}
              />
            ),
          }}
          columns={[
            { title: '情景编码', dataIndex: 'scenario_code', width: 140 },
            {
              title: '情景名称', dataIndex: 'scenario_name', width: 220,
              render: (v: string, r: Scenario) => (
                <Space>
                  <Tag color={scenarioColors[r.scenario_type] || 'default'}>{v}</Tag>
                  {r.source === 'REG' && <Tag color="red" style={{ marginLeft: -4 }}>监管</Tag>}
                  {r.source === 'CUSTOM' && <Tag color="green" style={{ marginLeft: -4 }}>自定义</Tag>}
                </Space>
              ),
            },
            {
              title: '类型', dataIndex: 'scenario_type', width: 110,
              render: (v: string) => <Tag color={scenarioColors[v] || 'default'}>{v}</Tag>,
            },
            {
              title: '因子数', width: 80, align: 'center',
              render: (_: any, r: Scenario) => {
                const cnt = r.shocks_json?.factors?.length || 0
                return <Badge count={cnt} showZero color={cnt > 0 ? 'blue' : 'default'} />
              },
            },
            {
              title: '说明', dataIndex: 'description', ellipsis: true,
              render: (v: string) => <Text type="secondary">{v || '-'}</Text>,
            },
            {
              title: '启用', dataIndex: 'is_active', width: 80,
              render: (v: number, r: Scenario) => (
                <Switch checked={!!v} size="small" onChange={() => toggleActive(r)} />
              ),
            },
            {
              title: '操作', width: 200, fixed: 'right' as const,
              render: (_: any, r: Scenario) => (
                <Space size={4}>
                  <Button type="primary" size="small" icon={<ThunderboltOutlined />}
                    onClick={() => openRun(r)} disabled={!r.is_active}>
                    运行此情景
                  </Button>
                  <Button type="link" size="small" icon={<EditOutlined />}
                    onClick={() => openEdit(r)}>
                    修改配置
                  </Button>
                </Space>
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
                    <Select options={Object.entries(scenarioColors).map(([v]) => ({ value: v, label: v }))} />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item label="情景说明" name="description">
                <AntInput.TextArea rows={2} />
              </Form.Item>
            </Form>

            <Divider orientation="left">
              <Space><span>⚡ 冲击因子配置</span><Tag>{editFactors.length} 个</Tag></Space>
            </Divider>

            <Table
              size="small"
              dataSource={editFactors.map((f, i) => ({ ...f, idx: i }))}
              rowKey="idx"
              pagination={false}
              columns={[
                {
                  title: '因子名', dataIndex: 'name', width: 180,
                  render: (v: string, _: any, idx: number) => (
                    <AntInput
                      value={v} list="factor-names"
                      onChange={(e) => updateFactor(idx, 'name', e.target.value)}
                    />
                  ),
                },
                {
                  title: '类型', dataIndex: 'type', width: 130,
                  render: (v: string, _: any, idx: number) => (
                    <Select
                      value={v} style={{ width: '100%' }}
                      options={Object.entries(factorTypeLabels).map(([vv, ll]) => ({ value: vv, label: ll }))}
                      onChange={(val) => updateFactor(idx, 'type', val)}
                    />
                  ),
                },
                {
                  title: '冲击值', dataIndex: 'value', width: 110,
                  render: (v: number, _: any, idx: number) => (
                    <InputNumber value={v} step={0.01} style={{ width: '100%' }}
                      onChange={(val) => updateFactor(idx, 'value', val as number)} />
                  ),
                },
                {
                  title: '含义', width: 200,
                  render: (_: any, r: Factor) => {
                    if (r.type === 'parallel_shift') return <Text type="secondary">利率平行移动 {r.value} bp（正=上行）</Text>
                    if (r.type === 'multiplier') return <Text type="secondary">乘数 {r.value}（1.5=上升50%，0.7=下降30%）</Text>
                    if (r.type === 'pct_change') return <Text type="secondary">百分比变动 {r.value}%</Text>
                    return '-'
                  },
                },
                {
                  title: '操作', width: 80,
                  render: (_: any, __: any, idx: number) => (
                    <Button danger size="small" icon={<DeleteOutlined />} onClick={() => removeFactor(idx)} />
                  ),
                },
              ]}
            />

            <datalist id="factor-names">
              {factorNameSuggestions.map(n => <option key={n} value={n} />)}
            </datalist>

            <Button type="dashed" block icon={<PlusOutlined />} style={{ marginTop: 12 }} onClick={addFactor}>
              添加冲击因子
            </Button>
          </>
        )}
      </Modal>

      {/* 运行模拟 Modal */}
      <RunSimulationModal
        open={runModalOpen}
        scenario={runningScenario}
        onClose={() => setRunModalOpen(false)}
        onCompleted={onRunCompleted}
      />
    </div>
  )
}

// ════════════════════════════════════════════════════════════
// 运行模拟 Modal（参数从基础数据自动加载 + 用户可微调 + 运行）
// ════════════════════════════════════════════════════════════
function RunSimulationModal({
  open, scenario, onClose, onCompleted,
}: {
  open: boolean
  scenario: Scenario | null
  onClose: () => void
  onCompleted: () => void
}) {
  const [form] = Form.useForm()
  const [companies, setCompanies] = useState<any[]>([])
  const [paramSummary, setParamSummary] = useState<any>(null)
  const [paramLoading, setParamLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<any>(null)

  useEffect(() => {
    if (!open) return
    companiesApi.list({ page: 1, page_size: 100 }).then(r => {
      const items = r.data?.items || []
      setCompanies(items)
      if (items.length > 0) {
        form.setFieldValue('company_id', items[0].id)
        loadBaseParams(items[0].id)
      }
    })
    setResult(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const loadBaseParams = async (companyId: number) => {
    if (!companyId) return
    setParamLoading(true)
    try {
      const r = await stressApi.baseParameters({ company_id: companyId })
      const p = r.data
      setParamSummary(p)
      form.setFieldsValue({
        assetValue: p.asset_value,
        liabilityValue: p.liability_value,
        assetDuration: p.asset_duration,
        liabilityDuration: p.liability_duration,
        baseScr: p.base_scr,
      })
    } catch (e: any) {
      message.error('加载基础参数失败')
    }
    setParamLoading(false)
  }

  const onCompanyChange = (cid: number) => loadBaseParams(cid)

  const onRun = async () => {
    if (!scenario) return
    try {
      const v = await form.validateFields()
      setRunning(true)
      const r = await stressApi.run({
        company_id: v.company_id,
        scenario_id: scenario.id,
        asset_value: v.assetValue,
        liability_value: v.liabilityValue,
        asset_duration: v.assetDuration,
        liability_duration: v.liabilityDuration,
        base_scr: v.baseScr,
      })
      setResult(r.data)
      message.success(`模拟完成，已写入测试结果（id=${r.data.id}）`)
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '运行失败')
    }
    setRunning(false)
  }

  const chartOption = result && result.detail && {
    title: { text: `${scenario?.scenario_name} · 因子冲击传导`, left: 'center' },
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 30, top: 50, bottom: 60 },
    xAxis: { type: 'category', data: result.detail.map((d: any) => `${d.factor}(${d.value})`) },
    yAxis: { type: 'value', name: '影响金额(万)' },
    series: [{
      type: 'bar',
      data: result.detail.map((d: any) => d.impact),
      itemStyle: { color: (p: any) => p.value >= 0 ? '#52c41a' : '#ff4d4f' },
    }],
  }

  return (
    <Modal
      title={<Space><ThunderboltOutlined style={{ color: '#722ed1' }} /><span>运行压力情景：{scenario?.scenario_name || ''}</span></Space>}
      open={open}
      onCancel={onClose}
      footer={result ? [
        <Button key="close" onClick={onClose}>关闭</Button>,
        <Button key="ok" type="primary" onClick={() => { onClose(); onCompleted() }}>完成并刷新结果</Button>,
      ] : [
        <Button key="cancel" onClick={onClose}>取消</Button>,
        <Button key="run" type="primary" icon={<PlayCircleOutlined />} loading={running} onClick={onRun}>运行模拟</Button>,
      ]}
      width={900}
    >
      {/* 情景信息 */}
      {scenario && (
        <Alert
          style={{ marginBottom: 12 }}
          type="info" showIcon
          message={
            <Space>
              <span>情景编码：<Tag color="blue">{scenario.scenario_code}</Tag></span>
              <Tag color={scenarioColors[scenario.scenario_type] || 'default'}>{scenario.scenario_type}</Tag>
              <span>因子数：<Tag>{(scenario.shocks_json?.factors || []).length}</Tag></span>
            </Space>
          }
          description={
            <div>
              <div style={{ marginBottom: 6 }}>{scenario.description}</div>
              <Space size={4} wrap>
                {(scenario.shocks_json?.factors || []).map((f: Factor, i: number) => (
                  <Tag key={i} color="purple">{f.name} ({f.type}={f.value})</Tag>
                ))}
              </Space>
            </div>
          }
        />
      )}

      {/* 公司 + 基础参数 */}
      <Card size="small" title={<><DatabaseOutlined /> 基础参数（自动从资产负债数据加载）</>}
        extra={<Button size="small" icon={<ReloadOutlined />} loading={paramLoading} onClick={() => loadBaseParams(form.getFieldValue('company_id'))}>重新加载</Button>}>
        <Form form={form} layout="inline">
          <Form.Item label="公司" name="company_id" rules={[{ required: true }]}>
            <Select style={{ width: 180 }} onChange={onCompanyChange}
              options={companies.map(c => ({ value: c.id, label: c.company_short || c.company_name }))} />
          </Form.Item>
          <Form.Item label="资产规模(万)" name="assetValue">
            <InputNumber min={0} step={10000} style={{ width: 140 }} />
          </Form.Item>
          <Form.Item label="负债规模(万)" name="liabilityValue">
            <InputNumber min={0} step={10000} style={{ width: 140 }} />
          </Form.Item>
          <Form.Item label="资产久期(年)" name="assetDuration">
            <InputNumber min={0} max={30} step={0.1} style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="负债久期(年)" name="liabilityDuration">
            <InputNumber min={0} max={30} step={0.1} style={{ width: 130 }} />
          </Form.Item>
          <Form.Item label="基础 SCR(万)" name="baseScr">
            <InputNumber min={0} step={1000} style={{ width: 140 }} />
          </Form.Item>
        </Form>
        {paramSummary && (
          <Alert
            style={{ marginTop: 8 }}
            type="success" showIcon
            message={
              <Space wrap>
                <Tag color="blue">{paramSummary.company_short}</Tag>
                <Tag>持仓 {paramSummary.summary.asset_holding_count}</Tag>
                <Tag>准备金类型 {paramSummary.summary.reserve_by_type.length}</Tag>
                <Tag>折现率 {(paramSummary.discount_rate * 100).toFixed(2)}%</Tag>
                <Tag>SCR 比率 {(paramSummary.summary.scr_ratio_used * 100)}%</Tag>
              </Space>
            }
          />
        )}
      </Card>

      {/* 结果展示 */}
      {result && !result.error && (
        <Card style={{ marginTop: 12 }} size="small">
          <Row gutter={16}>
            <Col span={6}><Statistic title="基准 NAV(万)" value={result.base_net_value} /></Col>
            <Col span={6}><Statistic title="NAV 变化(万)" value={result.nav_change} valueStyle={{ color: result.nav_change >= 0 ? '#52c41a' : '#ff4d4f' }} /></Col>
            <Col span={6}><Statistic title="压力后 NAV" value={result.new_net_value} /></Col>
            <Col span={6}><Statistic title="SCR 变化" value={result.scr_change_pct} suffix="%" valueStyle={{ color: result.passed ? '#52c41a' : '#ff4d4f' }} /></Col>
          </Row>
          <Alert
            style={{ marginTop: 12 }}
            type={result.passed ? 'success' : 'error'}
            showIcon
            message={result.passed ? '✅ 压力情景通过' : '❌ 压力情景未通过'}
            description={
              <Table
                size="small"
                dataSource={result.detail}
                pagination={false}
                rowKey={(r: any) => `${r.factor}-${r.value}`}
                columns={[
                  { title: '因子', dataIndex: 'factor' },
                  { title: '冲击值', dataIndex: 'value', width: 100 },
                  { title: '单位', dataIndex: 'unit', width: 80 },
                  { title: '影响金额(万)', dataIndex: 'impact', width: 140,
                    render: (v: number) => (
                      <span style={{ color: v >= 0 ? '#52c41a' : '#ff4d4f' }}>
                        {v > 0 ? '+' : ''}{v?.toFixed(2)}
                      </span>
                    ) },
                ]}
              />
            }
          />
          {chartOption && (
            <div style={{ marginTop: 12 }}>
              <ReactECharts option={chartOption} style={{ height: 220 }} />
            </div>
          )}
        </Card>
      )}
    </Modal>
  )
}

// ════════════════════════════════════════════════════════════
// 因子展开面板（表格行内）
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
          { title: '因子名', dataIndex: 'name', width: 180 },
          {
            title: '类型', dataIndex: 'type', width: 130,
            render: (v: string) => <Tag>{factorTypeLabels[v] || v}</Tag>,
          },
          { title: '冲击值', dataIndex: 'value', width: 110 },
          {
            title: '说明', width: 300,
            render: (_: any, r: Factor) => {
              if (r.type === 'parallel_shift') return <Text type="secondary">利率平行移动 {r.value} bp</Text>
              if (r.type === 'multiplier') return <Text type="secondary">乘数 {r.value}（1.5=上升50%）</Text>
              if (r.type === 'pct_change') return <Text type="secondary">百分比变动 {r.value}%</Text>
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

  useEffect(() => {
    load(1)
    // 订阅跨 tab 刷新事件
    const subs = (window as any).__stressRefreshSubs || ((window as any).__stressRefreshSubs = [])
    const cb = () => load(1)
    subs.push(cb)
    return () => {
      const idx = subs.indexOf(cb)
      if (idx >= 0) subs.splice(idx, 1)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div>
      <Title level={3}>📋 压力测试结果</Title>
      <Text type="secondary">历史压力测试记录（运行模拟后自动写入）</Text>
      <Card style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          dataSource={items}
          loading={loading}
          locale={{ emptyText: items.length === 0 ? '暂无测试结果，请到"监管情景"tab 选择情景并点击"运行此情景"' : undefined }}
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
            { title: '情景', dataIndex: 'scenario_name', width: 200 },
            { title: '情景编码', dataIndex: 'scenario_code', width: 140 },
            {
              title: '测试日', dataIndex: 'report_date', width: 130,
              render: (v: string) => v?.slice(0, 10),
            },
            {
              title: '资产影响(万)', dataIndex: 'asset_impact', width: 130,
              render: (v: number) => (
                <span style={{ color: v < 0 ? '#ff4d4f' : '#52c41a' }}>
                  {v > 0 ? '+' : ''}{v?.toLocaleString()}
                </span>
              ),
            },
            {
              title: 'NAV 变化(万)', dataIndex: 'nav_change', width: 140,
              render: (v: number) => (
                <span style={{ color: v < 0 ? '#ff4d4f' : '#52c41a' }}>
                  {v > 0 ? '+' : ''}{v?.toLocaleString()}
                </span>
              ),
            },
            {
              title: 'NAV 变化率', dataIndex: 'nav_change_pct', width: 120,
              render: (v: number) => `${v?.toFixed(2)}%`,
            },
            {
              title: '偿付能力变化', width: 160,
              render: (_: any, r: any) => (
                <Tooltip title={`前 ${r.solvency_ratio_before?.toFixed(4)} → 后 ${r.solvency_ratio_after?.toFixed(4)}`}>
                  <span style={{ color: (r.solvency_ratio_after - r.solvency_ratio_before) >= 0 ? '#52c41a' : '#ff4d4f' }}>
                    {(r.solvency_ratio_after - r.solvency_ratio_before)?.toFixed(4)}
                  </span>
                </Tooltip>
              ),
            },
            {
              title: '流动性缺口', dataIndex: 'liquidity_gap_after', width: 140,
              render: (v: number) => v?.toLocaleString(),
            },
            {
              title: '执行', dataIndex: 'exec_status', width: 90,
              render: (v: string) => <Tag color="blue">{v}</Tag>,
            },
            {
              title: '结果', dataIndex: 'passed', width: 100, fixed: 'right' as const,
              render: (v: number, r: any) =>
                v ? <Tag color="green">通过</Tag> : <Tag color="red">未通过 ({r.is_breached ? '已违约' : '未违约'})</Tag>,
            },
          ]}
        />
      </Card>
    </div>
  )
}

// Badge 占位
const Badge = ({ count, showZero, color }: any) => {
  if (count === 0 && !showZero) return null
  return <Tag color={color}>{count}</Tag>
}