/**
 * 现金流引擎 - 重算 Modal
 * 用于资产端管理 / 负债端管理 顶部触发
 */
import { useState, useEffect } from 'react'
import { Modal, Button, Alert, Form, Select, Statistic, Row, Col, Space, Tag, Spin, message, Typography } from 'antd'
import { ExperimentOutlined, ReloadOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { cashflowEngineApi } from '../api'

const { Text } = Typography

interface Props {
  open: boolean
  companyId: number
  companyShort: string
  onClose: () => void
  onCompleted?: () => void
}

export default function EngineRegenerateModal({ open, companyId, companyShort, onClose, onCompleted }: Props) {
  const [form] = Form.useForm()
  const [status, setStatus] = useState<any>(null)
  const [curves, setCurves] = useState<any[]>([])
  const [statusLoading, setStatusLoading] = useState(false)
  const [regenLoading, setRegenLoading] = useState(false)
  const [lastResult, setLastResult] = useState<any>(null)

  const loadStatus = async () => {
    if (!companyId) return
    setStatusLoading(true)
    try {
      const r = await cashflowEngineApi.status({ company_id: companyId })
      setStatus(r.data)
    } catch (e: any) {
      message.error('加载引擎状态失败')
    }
    setStatusLoading(false)
  }

  const loadCurves = async () => {
    try {
      const r = await cashflowEngineApi.curves()
      setCurves(r.data?.items || [])
    } catch (e) { console.error(e) }
  }

  useEffect(() => {
    if (open) {
      loadStatus()
      loadCurves()
    }
  }, [open, companyId])

  const onRegenerate = async () => {
    const v = await form.validateFields()
    setRegenLoading(true)
    setLastResult(null)
    try {
      const r = await cashflowEngineApi.regenerate({
        company_id: companyId,
        scenario_code: v.scenario_code,
        curve_code: v.curve_code,
      })
      setLastResult(r.data)
      message.success('重算完成')
      await loadStatus()
      if (onCompleted) onCompleted()
    } catch (e: any) {
      message.error(e?.response?.data?.message || '重算失败')
    }
    setRegenLoading(false)
  }

  return (
    <Modal
      title={<Space><ExperimentOutlined style={{ color: '#722ed1' }} /><span>现金流测算引擎 - {companyShort}</span></Space>}
      open={open}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose}>关闭</Button>,
        <Button key="regen" type="primary" icon={<ThunderboltOutlined />} loading={regenLoading} onClick={onRegenerate}>
          触发引擎重算
        </Button>,
      ]}
      width={820}
    >
      <Alert
        style={{ marginBottom: 16 }}
        type="info" showIcon
        message="引擎原理"
        description={
          <ul style={{ margin: '4px 0 0 0', paddingLeft: 20 }}>
            <li><b>资产端</b>：按 holding 的 <code>interest_payment_freq/unit</code> + <code>principal_payment_freq/unit</code> 生成支付日程，按 category_code 决定现金流类型（COUPON / DIVIDEND / DISTRIBUTION / SETTLE / RENTAL）</li>
            <li><b>负债端</b>：按 policy 的 payment_period / insurance_period + 死亡表 (qx) + 退保率 (LAPSE_*) 生成 PREMIUM_IN / CLAIM_OUT / BENEFIT_OUT / SURRENDER_OUT / EXPENSE_OUT</li>
            <li><b>贴现</b>：使用 ialm_yield_curve 的 NSS 利率点 + 线性插值（默认中债国债曲线 CN-GB-2025，21 个 tenor）</li>
          </ul>
        }
      />

      {/* 引擎参数 */}
      <Form form={form} layout="inline" initialValues={{ scenario_code: 'BASE', curve_code: 'CN-GB-2025' }}
        style={{ marginBottom: 16 }}>
        <Form.Item label="情景" name="scenario_code">
          <Select style={{ width: 120 }} options={[
            { value: 'BASE', label: 'BASE' },
            { value: 'UP200', label: 'UP200' },
            { value: 'DOWN200', label: 'DOWN200' },
            { value: 'STRESS', label: 'STRESS' },
          ]} />
        </Form.Item>
        <Form.Item label="贴现曲线" name="curve_code">
          <Select style={{ width: 200 }}
            options={curves.map(c => ({ value: c.curve_code, label: c.curve_name }))} />
        </Form.Item>
        <Form.Item>
          <Button icon={<ReloadOutlined />} onClick={loadStatus} loading={statusLoading}>刷新状态</Button>
        </Form.Item>
      </Form>

      {/* 当前引擎状态 */}
      {status && (
        <Spin spinning={statusLoading}>
          <Row gutter={16}>
            <Col span={12}>
              <div style={{ background: '#f0f5ff', padding: 12, borderRadius: 4, marginBottom: 12 }}>
                <Space>
                  <Tag color="blue">资产端</Tag>
                  <Text strong>持仓 {status.asset.holdings_total} 个</Text>
                </Space>
                <Row gutter={8} style={{ marginTop: 8 }}>
                  <Col span={12}>
                    <Statistic title="已生成现金流" value={status.asset.cashflows_total}
                      suffix="条" valueStyle={{ fontSize: 18 }} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="合计 PV" value={Math.round(status.asset.total_present_value)}
                      suffix="万" precision={0} valueStyle={{ fontSize: 18, color: '#52c41a' }} />
                  </Col>
                </Row>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  区间：{status.asset.first_period || '-'} ~ {status.asset.last_period || '-'}（{status.asset.scenarios} 情景）
                </Text>
              </div>
            </Col>
            <Col span={12}>
              <div style={{ background: '#fff7e6', padding: 12, borderRadius: 4, marginBottom: 12 }}>
                <Space>
                  <Tag color="orange">负债端</Tag>
                  <Text strong>保单 {status.liability.policies_total} 张</Text>
                </Space>
                <Row gutter={8} style={{ marginTop: 8 }}>
                  <Col span={12}>
                    <Statistic title="已生成现金流" value={status.liability.cashflows_total}
                      suffix="条" valueStyle={{ fontSize: 18 }} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="合计 PV" value={Math.round(status.liability.total_present_value)}
                      suffix="万" precision={0} valueStyle={{ fontSize: 18, color: '#fa8c16' }} />
                  </Col>
                </Row>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  区间：{status.liability.first_period || '-'} ~ {status.liability.last_period || '-'}（{status.liability.scenarios} 情景）
                </Text>
              </div>
            </Col>
          </Row>
          <div style={{ textAlign: 'center', fontSize: 12, color: '#666', marginBottom: 12 }}>
            贴现曲线：<Tag color="purple">{status.curve_code}</Tag>（{status.curve_points} 个 tenor）
          </div>
        </Spin>
      )}

      {/* 重算结果 */}
      {lastResult && (
        <Alert
          type="success" showIcon
          message="本次重算完成"
          description={
            <Row gutter={16}>
              <Col span={12}>
                <Statistic title="资产持仓处理" value={lastResult.asset_holdings_processed} suffix="个" />
                <Statistic title="资产现金流生成" value={lastResult.asset_cashflows_generated} suffix="条" />
              </Col>
              <Col span={12}>
                <Statistic title="保单处理" value={lastResult.liability_policies_processed} suffix="张" />
                <Statistic title="负债现金流生成" value={lastResult.liability_cashflows_generated} suffix="条" />
              </Col>
            </Row>
          }
        />
      )}
    </Modal>
  )
}