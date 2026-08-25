/**
 * IALM 资产端管理
 */
import { Card, Tabs, Tag, Space, Tooltip } from 'antd'
import DataListPage from '../components/DataListPage'
import { assetsApi } from '../api'

const riskColors: Record<string, string> = {
  LOW: 'green',
  MEDIUM: 'orange',
  HIGH: 'red',
  UNRATED: 'default',
}

// 主权/政府债默认评级（无显式评级时填此）
const SOVEREIGN_RATING = '主权AAA'

export default function Assets() {
  return (
    <Tabs
      defaultActiveKey="holdings"
      type="card"
      items={[
        {
          key: 'holdings',
          label: '资产持仓',
          children: (
            <DataListPage
              title="资产持仓管理"
              subtitle="投资持仓清单（关联 ialm_insurance_company / ialm_asset_category）"
              fetcher={(p) => assetsApi.holdings(p)}
              columns={[
                { title: '持仓编号', dataIndex: 'asset_code', width: 110 },
                { title: '资产名称', dataIndex: 'asset_name', width: 200 },
                // === 外键关联展示（JOIN ialm_insurance_company）===
                { title: '机构编码', dataIndex: 'company_code', width: 140,
                  render: (v: string) => <Tag color="purple">{v}</Tag> },
                { title: '保险公司', dataIndex: 'company_name', width: 90,
                  render: (v: string, row: any) => (
                    <Tooltip title={`全称: ${row.company_full_name || ''} | ID=${row.company_id}`}>
                      <span>{v}</span>
                    </Tooltip>
                  ) },
                // === 外键关联展示（JOIN ialm_asset_category）===
                { title: '资产分类', dataIndex: 'category_code', width: 150 },
                { title: '分类名称', dataIndex: 'category_name', width: 130 },
                // === 业务字段 ===
                { title: '账面价值(万)', dataIndex: 'cost_value', width: 120,
                  render: (v: number) => v?.toLocaleString(undefined, {maximumFractionDigits: 0}) },
                { title: '市值(万)', dataIndex: 'market_value', width: 110,
                  render: (v: number) => v?.toLocaleString(undefined, {maximumFractionDigits: 0}) },
                { title: '票面利率', dataIndex: 'coupon_rate', width: 90,
                  render: (v: number) => `${(v * 100).toFixed(2)}%` },
                { title: '久期(年)', dataIndex: 'duration_year', width: 90,
                  render: (v: number) => v?.toFixed(2) },
                { title: '到期日', dataIndex: 'maturity_date', width: 110 },
                { title: '评级', dataIndex: 'credit_rating', width: 90,
                  render: (v: string, row: any) => {
                    // 政府债无显式评级 → 默认主权AAA
                    const code = row.category_code || ''
                    if (v && v.trim()) return <Tag color="blue">{v}</Tag>
                    if (code.includes('GOVT') || code.includes('CDB') || code.includes('POLICY')) {
                      return <Tag color="cyan">{SOVEREIGN_RATING}</Tag>
                    }
                    return <Tag>未评级</Tag>
                  } },
                { title: '币种', dataIndex: 'currency', width: 70 },
              ]}
            />
          ),
        },
        {
          key: 'categories',
          label: '资产分类',
          children: (
            <DataListPage
              title="资产分类"
              subtitle="资产分类树（多层级：现金/债券/权益/基金/另类）"
              fetcher={(p) => assetsApi.categories(p)}
              columns={[
                { title: '分类编码', dataIndex: 'category_code', width: 180 },
                { title: '分类名称', dataIndex: 'category_name', width: 200 },
                { title: '父分类ID', dataIndex: 'parent_id', width: 100,
                  render: (v: number) => v === 0 ? <Tag>根分类</Tag> : v },
                { title: '分类类型', dataIndex: 'category_type', width: 100,
                  render: (v: string) => <Tag color={
                    v === 'CASH' ? 'green' :
                    v === 'BOND' ? 'blue' :
                    v === 'EQUITY' ? 'magenta' :
                    v === 'FUND' ? 'cyan' :
                    v === 'ALTERNATIVE' ? 'orange' : 'default'
                  }>{v}</Tag> },
                { title: '风险权重', dataIndex: 'risk_weight', width: 100,
                  render: (v: number) => `${(v * 100).toFixed(1)}%` },
                { title: '默认久期(年)', dataIndex: 'duration_default', width: 120,
                  render: (v: number) => v?.toFixed(2) },
              ]}
            />
          ),
        },
        {
          key: 'cashflows',
          label: '资产现金流',
          children: (
            <DataListPage
              title="资产现金流"
              subtitle="按期预测的资产端现金流（息票/本金）"
              fetcher={(p) => assetsApi.cashflows({ ...p, page_size: 50 })}
              columns={[
                { title: '期数', dataIndex: 'period_number', width: 70 },
                { title: '年', dataIndex: 'period_year', width: 80,
                  render: (v: number) => v?.toFixed(0) },
                { title: '现金流类型', dataIndex: 'cashflow_type', width: 130,
                  render: (v: string) => <Tag color={
                    v === 'COUPON' ? 'blue' :
                    v === 'PRINCIPAL' ? 'orange' : 'default'
                  }>{v}</Tag> },
                { title: '金额(万)', dataIndex: 'amount', width: 140,
                  render: (v: number) => v?.toLocaleString(undefined, {maximumFractionDigits: 2}) },
                { title: '折现因子', dataIndex: 'discount_factor', width: 100,
                  render: (v: number) => v?.toFixed(4) },
                { title: '现值(万)', dataIndex: 'present_value', width: 140,
                  render: (v: number) => v?.toLocaleString(undefined, {maximumFractionDigits: 2}) },
                { title: '现金流日期', dataIndex: 'period_date', width: 110 },
              ]}
            />
          ),
        },
      ]}
    />
  )
}