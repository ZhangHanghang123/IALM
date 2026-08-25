/**
 * IALM 算法引擎列表（14 项）
 */
import { useEffect, useState } from 'react'
import { Card, Tag, Space, Typography, Row, Col, Divider } from 'antd'
import { CalculatorOutlined } from '@ant-design/icons'
import { algorithmsApi } from '../api'

const { Title, Text, Paragraph } = Typography

const algoDesc: Record<string, { desc: string; formula: string }> = {
  'ALG-001': {
    desc: '测算资产端与负债端现金流按时间桶分布的匹配程度，监管要求 ≥ 80%',
    formula: 'DMR = 1 - 0.5 × Σ|A_i/L_A - L_i/L_L|',
  },
  'ALG-002': {
    desc: '测算投资收益率与负债资金成本 + 费用率的比例关系',
    formula: 'CYR = 投资收益率×(1-税率) / (负债成本 + 费用率)',
  },
  'ALG-003': {
    desc: '测算累计净现金流首次 ≥ 0 所需的年数（线性插值）',
    formula: 'Payback = 累计净现金流首次 ≥ 0 的年份',
  },
  'ALG-004': {
    desc: 'Macaulay 久期与久期缺口，衡量利率风险敞口',
    formula: 'D = Σ(t·PV(CF_t))/Σ(PV(CF_t)); Gap = D_A - D_L',
  },
  'ALG-005': { desc: '基于蒙特卡洛模拟预测未来 30 年现金流', formula: 'CF_t = CF_{t-1} + ε, ε~N(μ,σ²)' },
  'ALG-006': { desc: 'Hull-White/Vasicek/CIR 三种利率模型', formula: 'dr = (θ-αr)dt + σdW' },
  'ALG-007': { desc: '6 个监管预置压力情景：利率±200bp/退保+50%/投资-50%/汇率+15%', formula: '∆NAV = ΣPV(CF·shock)' },
  'ALG-008': { desc: 'Markowitz 均值-方差最优投资组合', formula: 'min σ²_p s.t. μ_p ≥ target' },
  'ALG-009': { desc: 'Black-Litterman 贝叶斯资产配置', formula: 'E(R) = [(τΣ)⁻¹ + P^TΩ⁻¹P]⁻¹[(τΣ)⁻¹Π + P^TΩ⁻¹Q]' },
  'ALG-010': { desc: 'Brinson 业绩归因：配置 + 选择 + 交互', formula: '贡献率 = (w_p - w_b)×(R_b - R_total)' },
  'ALG-011': { desc: '在险价值 VaR 与条件在险价值 CVaR', formula: 'VaR_α = inf{x: P(L>x)≤1-α}' },
  'ALG-012': { desc: '动态复制免疫策略', formula: 'min ||D_A - D_L||² s.t. CV_A ≈ CV_L' },
  'ALG-013': { desc: '再保现金流建模', formula: 'CF_reins = ∑(q·premium - c·claim)' },
  'ALG-014': { desc: '久期匹配资产负债管理（ALM-DM）', formula: 'D_A - D_L = 0; CV_A - CV_L = 0' },
}

export default function AlgorithmList() {
  const [items, setItems] = useState<any[]>([])
  useEffect(() => {
    algorithmsApi.list().then((r) => setItems(r.data.algorithms || [])).catch(() => {})
  }, [])

  return (
    <div>
      <Title level={3}>🧮 算法引擎</Title>
      <Text type="secondary">14 项核心算法实现，从监管指标到组合优化的完整工具箱</Text>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        {items.map((a) => (
          <Col span={8} key={a.id}>
            <Card hoverable
              title={
                <Space>
                  <CalculatorOutlined style={{ color: '#667eea' }} />
                  <span>{a.id}</span>
                  <Tag color="blue">{a.category}</Tag>
                </Space>
              }
              extra={<Text strong style={{ color: '#722ed1' }}>{a.name}</Text>}
              style={{ minHeight: 180 }}
            >
              <Paragraph style={{ marginBottom: 8 }}>{algoDesc[a.id]?.desc}</Paragraph>
              <Divider style={{ margin: '8px 0' }} />
              <Text type="secondary" style={{ fontSize: 12 }}>
                公式: <Text code style={{ fontSize: 11 }}>{algoDesc[a.id]?.formula}</Text>
              </Text>
              <div style={{ marginTop: 8 }}>
                <Tag color="orange">阈值: {a.threshold}</Tag>
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  )
}