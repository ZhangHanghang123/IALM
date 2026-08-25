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
                { title: '保险公司', dataIndex: 'company_name', width: 140 },
                { title: '产品', dataIndex: 'product_code', width: 120 },
                { title: '保额(万)', dataIndex: 'insured_amount', width: 140,
                  render: (v: number) => v?.toLocaleString() },
                { title: '保费(万)', dataIndex: 'premium', width: 120,
                  render: (v: number) => v?.toLocaleString() },
                { title: '保期(年)', dataIndex: 'policy_term', width: 100 },
                { title: '生效日', dataIndex: 'inception_date', width: 120 },
                { title: '到期日', dataIndex: 'maturity_date', width: 120 },
                { title: '状态', dataIndex: 'status', width: 100,
                  render: (v: string) => <Tag color={v === 'ACTIVE' ? 'green' : 'default'}>{v}</Tag> },
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
                { title: '编码', dataIndex: 'category_code', width: 140 },
                { title: '名称', dataIndex: 'category_name' },
                { title: '父分类', dataIndex: 'parent_code', width: 120 },
                { title: '负债类型', dataIndex: 'liability_type', width: 120,
                  render: (v: string) => <Tag color={liabilityColors[v]}>{v}</Tag> },
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
                { title: '保险公司', dataIndex: 'company_name', width: 140 },
                { title: '准备金类型', dataIndex: 'reserve_type', width: 160 },
                { title: '报告日', dataIndex: 'report_date', width: 120 },
                { title: '金额(万)', dataIndex: 'amount', width: 140,
                  render: (v: number) => v?.toLocaleString() },
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
                { title: '公司ID', dataIndex: 'company_id', width: 80 },
                { title: '假设类型', dataIndex: 'assumption_type', width: 160 },
                { title: '参数名', dataIndex: 'parameter_name' },
                { title: '参数值', dataIndex: 'value_numeric', width: 140,
                  render: (v: number) => v?.toFixed(4) },
                { title: '单位', dataIndex: 'unit', width: 80 },
                { title: '生效日', dataIndex: 'effective_date', width: 120 },
                { title: '来源', dataIndex: 'source', width: 160 },
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
              subtitle="按年/月预测的负债端现金流（给付/退保）"
              fetcher={(p) => liabilitiesApi.cashflows({ ...p, page_size: 50 })}
              columns={[
                { title: '公司ID', dataIndex: 'company_id', width: 80 },
                { title: '保单ID', dataIndex: 'policy_id', width: 100 },
                { title: '年', dataIndex: 'period_year', width: 80 },
                { title: '月', dataIndex: 'period_month', width: 80 },
                { title: '金额(万)', dataIndex: 'amount', width: 140,
                  render: (v: number) => v?.toLocaleString() },
                { title: '给付类型', dataIndex: 'benefit_type', width: 120 },
                { title: '币种', dataIndex: 'currency', width: 80 },
              ]}
            />
          ),
        },
      ]}
    />
  )
}