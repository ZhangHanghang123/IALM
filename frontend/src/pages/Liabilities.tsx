/**
 * IALM 负债端管理
 */
import { Card, Tabs, Tag, Space } from 'antd'
import DataListPage from '../components/DataListPage'
import { liabilitiesApi } from '../api'

const liabilityColors: Record<string, string> = {
  LIFE: 'blue',
  PROPERTY: 'orange',
  HEALTH: 'cyan',
  REINSURANCE: 'purple',
}

export default function Liabilities() {
  return (
    <Tabs
      defaultActiveKey="policies"
      type="card"
      items={[
        {
          key: 'policies',
          label: '保单主档',
          children: (
            <DataListPage
              title="保单主档管理"
              subtitle="保险合同主档（保额/保费/期限）"
              fetcher={(p) => liabilitiesApi.policies(p)}
              columns={[
                { title: '保单号', dataIndex: 'policy_no', width: 180 },
                { title: '保险公司', dataIndex: 'company_name', width: 120 },
                { title: '产品', dataIndex: 'product_name', width: 160 },
                { title: '保额(万)', dataIndex: 'sum_insured', width: 120,
                  render: (v: number) => v?.toLocaleString() },
                { title: '年保费(万)', dataIndex: 'annual_premium', width: 120,
                  render: (v: number) => v?.toLocaleString() },
                { title: '缴费期(年)', dataIndex: 'payment_period', width: 100 },
                { title: '保险期(年)', dataIndex: 'insurance_period', width: 100 },
                { title: '生效日', dataIndex: 'effective_date', width: 110 },
                { title: '到期日', dataIndex: 'maturity_date', width: 110 },
              ]}
            />
          ),
        },
        {
          key: 'product-categories',
          label: '产品分类',
          children: (
            <DataListPage
              title="产品分类"
              subtitle="保险产品分类树（按负债类型）"
              fetcher={(p) => liabilitiesApi.productCategories(p)}
              columns={[
                { title: '编码', dataIndex: 'product_type_code', width: 180 },
                { title: '名称', dataIndex: 'product_type_name' },
                { title: '险种', dataIndex: 'insurance_type', width: 100,
                  render: (v: string) => <Tag color={liabilityColors[v] || 'default'}>{v}</Tag> },
                { title: '期限类型', dataIndex: 'duration_type', width: 100 },
                { title: '缴费方式', dataIndex: 'payment_type', width: 100 },
                { title: '风险账户', dataIndex: 'is_risk_account', width: 90,
                  render: (v: number) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
              ]}
            />
          ),
        },
        {
          key: 'reserves',
          label: '准备金',
          children: (
            <DataListPage
              title="责任准备金"
              subtitle="未到期/未决赔款/长寿准备金等"
              fetcher={(p) => liabilitiesApi.reserves(p)}
              columns={[
                { title: '保险公司', dataIndex: 'company_name', width: 120 },
                { title: '准备金类型', dataIndex: 'reserve_type', width: 200 },
                { title: '报告日', dataIndex: 'report_date', width: 120 },
                { title: '金额(万)', dataIndex: 'amount', width: 140,
                  render: (v: number) => v?.toLocaleString() },
                { title: '会计准则', dataIndex: 'accounting_basis', width: 110 },
                { title: '币种', dataIndex: 'currency', width: 80 },
              ]}
            />
          ),
        },
        {
          key: 'assumptions',
          label: '精算假设',
          children: (
            <DataListPage
              title="精算假设"
              subtitle="死亡率/退保率/折现率等精算参数"
              fetcher={(p) => liabilitiesApi.assumptions(p)}
              columns={[
                { title: '假设集', dataIndex: 'assumption_set_code', width: 160 },
                { title: '折现率', dataIndex: 'discount_rate', width: 100,
                  render: (v: number) => `${((v || 0) * 100).toFixed(2)}%` },
                { title: '死亡率表', dataIndex: 'mortality_table_code', width: 160 },
                { title: '退保率编码', dataIndex: 'lapse_rate_code', width: 160 },
                { title: '费用率编码', dataIndex: 'expense_rate_code', width: 160 },
                { title: '生效日', dataIndex: 'effective_date', width: 120 },
              ]}
            />
          ),
        },
        {
          key: 'cashflows',
          label: '负债现金流',
          children: (
            <DataListPage
              title="负债现金流"
              subtitle="按期预测的负债端现金流（保费/给付/退保）"
              fetcher={(p) => liabilitiesApi.cashflows({ ...p, page_size: 50 })}
              columns={[
                { title: '年', dataIndex: 'period_year', width: 80,
                  render: (v: number) => v?.toFixed(0) },
                { title: '现金流类型', dataIndex: 'cashflow_type', width: 160,
                  render: (v: string) => <Tag color={
                    v === 'PREMIUM_IN' ? 'green' :
                    v === 'BENEFIT_OUT' ? 'red' :
                    v === 'CLAIM_OUT' ? 'orange' : 'default'
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